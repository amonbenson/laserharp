#include "animation.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// static void boot_animation_update(laser_array_t *la, float progress) {
//     float pos = (sinf(progress * 2 * M_PI) * 0.3 + 0.5) * LA_NUM_DIODES + 0.5;
//     uint8_t pos_int = (uint8_t) pos;
//     uint8_t pos_frac = (uint8_t) ((pos - pos_int) * LA_NUM_BRIGHTNESS_LEVELS - 1);

//     for (uint8_t i = 0; i < LA_NUM_DIODES; i++) {
//         uint8_t brightness = 0;
//         if (i == pos_int) {
//             brightness = pos_frac;
//         } else if (i == pos_int - 1) {
//             brightness = LA_NUM_BRIGHTNESS_LEVELS - 1 - pos_frac;
//         }

//         laser_array_set_brightness(la, i, brightness);
//     }
// }

static void boot_animation_update(laser_array_t *la, float progress) {
    for (uint8_t i = 0; i < LA_NUM_DIODES; i++) {
        float perc = fmodf(i * 0.61803398875 + progress, 1.0);
        uint8_t brightness = (uint8_t) ((1.0 - fmin(perc * 3.0, 1.0)) * LA_NUM_BRIGHTNESS_LEVELS - 1);
        laser_array_set_brightness(la, i, brightness);
    }
}

static void flip_animation_update(laser_array_t *la, float progress) {
    for (uint8_t i = 0; i < LA_NUM_DIODES; i++) {
        uint8_t brightness = 0;
        if (i == (uint8_t) (progress * LA_NUM_DIODES)) {
            brightness = LA_NUM_BRIGHTNESS_LEVELS - 1;
        }

        laser_array_set_brightness(la, i, brightness);
    }
}

static void test_animation_update(laser_array_t *la, float progress) {
    for (uint8_t i = 0; i < LA_NUM_DIODES; i++) {
        uint8_t brightness = 0;
        if (i == 4 && progress < 0.5) {
            brightness = LA_NUM_BRIGHTNESS_LEVELS - 1;
        } else if (i == 5 && progress >= 0.5) {
            brightness = LA_NUM_BRIGHTNESS_LEVELS - 1;
        }

        laser_array_set_brightness(la, i, brightness);
    }
}

const animation_update_fn_t animation_update_fns[NUM_ANIMATIONS] = {
    boot_animation_update,
    flip_animation_update,
    test_animation_update,
};

int animator_init(animator_t *animator, const animator_config_t *config) {
    animator->config = *config;
    animator->current_animation = 0;
    animator->duration = 1.0;
    animator->follow_action = ANIMATION_LOOP;
    animator->progress = 0.0;
    animator->playing = false;

    return 0;
}

int animator_play(animator_t *animator, uint8_t id, float duration, animation_follow_action_t follow_action) {
    if (id >= NUM_ANIMATIONS) {
        LOG_ERROR("Invalid animation ID: %u", id);
        return 1;
    }

    if (duration <= ANIMATION_MIN_DURATION) {
        duration = ANIMATION_MIN_DURATION;
    } else if (duration >= ANIMATION_MAX_DURATION) {
        duration = ANIMATION_MAX_DURATION;
    }

    if (follow_action >= ANIMATION_FOLLOW_ACTION_COUNT) {
        LOG_ERROR("Invalid follow action: %u", follow_action);
        return 1;
    }

    // set the animation parameters
    LOG_TRACE("Playing animation %u for %.2fs. Follow action: %u", id, duration, follow_action);
    animator->current_animation = id;
    animator->duration = duration;
    animator->follow_action = follow_action;
    animator->progress = 0.0;
    animator->playing = true;

    return 0;
}

int animator_stop(animator_t *animator) {
    LOG_TRACE("Stopping animation %u. Running follow action: %u", animator->current_animation, animator->follow_action);

    animator->progress = 1.0;
    animator->playing = false;

    switch (animator->follow_action) {
        case ANIMATION_STOP_LAST_FRAME:
            // run the last frame of the animation
            animation_update_fns[animator->current_animation](animator->config.laser_array, 1.0);
            break;
        case ANIMATION_STOP_OFF:
            // turn off all diodes
            for (uint8_t i = 0; i < LA_NUM_DIODES; i++) {
                laser_array_set_brightness(animator->config.laser_array, i, 0);
            }
            break;
        default:
            break;
    }

    return 0;
}

int animator_update(animator_t *animator, float dt) {
    if (!animator->playing) {
        return 0;
    }

    // update progress
    animator->progress += dt / animator->duration;

    // check if the animation has finished
    bool finished = false;
    if (animator->progress >= 1.0) {
        animator->progress = 1.0;
        finished = true;
    }

    // run the update function
    animation_update_fns[animator->current_animation](animator->config.laser_array, animator->progress);

    // if we have finished, either loop or stop the animation
    if (finished) {
        if (animator->follow_action == ANIMATION_LOOP) {
            animator->progress = 0.0;
        } else {
            animator_stop(animator);
        }
    }

    return 0;
}

uint8_t animator_get_current_animation(animator_t *animator) {
    return animator->current_animation;
}

float animator_get_duration(animator_t *animator) {
    return animator->duration;
}

animation_follow_action_t animator_get_follow_action(animator_t *animator) {
    return animator->follow_action;
}

float animator_get_progress(animator_t *animator) {
    return animator->progress;
}

bool animator_is_playing(animator_t *animator) {
    return animator->playing;
}
