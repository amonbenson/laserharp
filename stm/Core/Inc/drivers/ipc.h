#include "cmsis_os.h"
#include "midi_types.h"
#include "stm32f1xx_hal.h"

typedef struct {
    UART_HandleTypeDef *huart;

    uint8_t rx_buffer[MIDI_PACKET_SIZE];
    osMessageQueueId_t rx_queue;
} ipc_driver_t;

void ipc_driver_init(UART_HandleTypeDef *huart, osMessageQueueId_t rx_queue);

void ipc_driver_transmit(midi_packet_t *packet);

void ipc_driver_HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size);
