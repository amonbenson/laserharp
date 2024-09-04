#pragma once

#include "cmsis_os2.h"
#include "log.h"
#include "midi.h"
#include "stm32f1xx_hal.h"

#define IPC_RX_BUFFER_SIZE 128
#define IPC_RX_TIMEOUT 10

#define IPC_TX_BUFFER_SIZE 128
#define IPC_TX_TIMEOUT 100

typedef struct {
    UART_HandleTypeDef *huart;
} ipc_config_t;

typedef struct {
    ipc_config_t config;
    midi_interface_t midi;

    osSemaphoreId_t tx_lock;
    // TODO: tx queue

    osSemaphoreId_t rx_lock;
    osMessageQueueId_t rx_queue;
    uint8_t rx_byte;
} ipc_t;

int ipc_init(ipc_t *din, const ipc_config_t *config);

int ipc_transmit(ipc_t *din, midi_message_t *message);
int ipc_receive(ipc_t *din, midi_message_t *message);

int ipc_HAL_UART_RxCpltCallback(ipc_t *din);
