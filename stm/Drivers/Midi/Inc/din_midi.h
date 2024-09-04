#pragma once

#include "cmsis_os2.h"
#include "log.h"
#include "midi.h"
#include "stm32f1xx_hal.h"

#define DIN_MIDI_RX_BUFFER_SIZE 128
#define DIN_MIDI_RX_TIMEOUT 10

#define DIN_MIDI_TX_BUFFER_SIZE 128
#define DIN_MIDI_TX_TIMEOUT 100

typedef struct {
    UART_HandleTypeDef *huart;
} din_midi_config_t;

typedef struct {
    din_midi_config_t config;
    midi_interface_t midi;

    osSemaphoreId_t tx_lock;
    // TODO: tx queue

    osSemaphoreId_t rx_lock;
    osMessageQueueId_t rx_queue;
    uint8_t rx_byte;
} din_midi_t;

int din_midi_init(din_midi_t *din, const din_midi_config_t *config);

int din_midi_transmit(din_midi_t *din, midi_message_t *message);
int din_midi_receive(din_midi_t *din, midi_message_t *message);

int din_midi_HAL_UART_RxCpltCallback(din_midi_t *din);
