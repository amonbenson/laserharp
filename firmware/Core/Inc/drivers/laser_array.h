#pragma once

#include "log.h"
#include "main.h"
#include "stdint.h"
#include "stm32f1xx_hal.h"

#define LA_NUM_DIODES 24
#define LA_NUM_BRIGHTNESS_LEVELS 64
#define LA_TX_DATA_LENGTH (LA_NUM_BRIGHTNESS_LEVELS - 1)

#ifndef LA_FADE_TICK_RATE
#warning "LA_FADE_TICK_RATE was not defined! Using default setting"
#define LA_FADE_TICK_RATE 60
#endif

typedef uint32_t la_bitmask_t;
typedef uint64_t la_brightness_pattern_t;

typedef struct {
    // required peripherals
    SPI_HandleTypeDef *hspi;
    TIM_HandleTypeDef *htim_transfer;
    TIM_HandleTypeDef *htim_fade;
    uint32_t rclk_channel;
} laser_array_config_t;

typedef struct {
    uint8_t current_brightness;
    uint8_t source_brightness;
    uint8_t target_brightness;

    uint32_t transition_duration;
    uint32_t transition_tick;
} la_diode_t;

typedef struct {
    laser_array_config_t config;

    la_diode_t diodes[LA_NUM_DIODES];
    la_bitmask_t tx_data[LA_TX_DATA_LENGTH];
} laser_array_t;

int laser_array_init(laser_array_t *la, const laser_array_config_t *config);
uint8_t laser_array_get_brightness(laser_array_t *la, uint8_t diode_index);
int laser_array_set_brightness(laser_array_t *la, uint8_t diode_index, uint8_t brightness);
int laser_array_fade_brightness(laser_array_t *la, uint8_t diode_index, uint8_t brightness, uint32_t duration);

int laser_array_fade_TIM_PeriodElapsedHandler(laser_array_t *la);
