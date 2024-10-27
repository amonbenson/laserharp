#pragma once

#include "drivers/laser_array.h"
#include <stdbool.h>

#define NUM_ANIMATIONS 3
#define ANIMATION_BOOT 0
#define ANIMATION_FLIP 1
#define ANIMATION_TEST 2

#define ANIMATION_MIN_DURATION 0.01
#define ANIMATION_MAX_DURATION 100.0

typedef void (*animation_update_fn_t)(laser_array_t *la, float progress);

typedef enum {
    ANIMATION_LOOP = 0,
    ANIMATION_STOP_LAST_FRAME,
    ANIMATION_STOP_OFF,
    ANIMATION_STOP_PREVIOUS_STATE,
    ANIMATION_FOLLOW_ACTION_COUNT
} animation_follow_action_t;

typedef struct {
    laser_array_t *laser_array;
} animator_config_t;

typedef struct {
    animator_config_t config;

    uint8_t current_animation;
    float duration;
    animation_follow_action_t follow_action;

    float progress;
    bool playing;

    uint8_t previous_diode_brightness[LA_NUM_DIODES];
} animator_t;

int animator_init(animator_t *animator, const animator_config_t *config);

int animator_play(animator_t *animator, uint8_t id, float duration, animation_follow_action_t follow_action);
int animator_stop(animator_t *animator);
int animator_update(animator_t *animator, float dt);

uint8_t animator_get_current_animation(animator_t *animator);
float animator_get_duration(animator_t *animator);
animation_follow_action_t animator_get_follow_action(animator_t *animator);
float animator_get_progress(animator_t *animator);
bool animator_is_playing(animator_t *animator);
