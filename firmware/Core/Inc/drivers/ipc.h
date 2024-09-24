#include "cmsis_os.h"
#include "midi_types.h"
#include "stm32f1xx_hal.h"

#define IPC_PACKET_SIZE 4

typedef uint8_t ipc_packet_t[IPC_PACKET_SIZE];

#define IPC_PACKET_FMT "%02X %02X %02X %02X"
#define IPC_PACKET_FMT_ARGS(packet) (*packet)[0], (*packet)[1], (*packet)[2], (*packet)[3]

typedef struct {
    UART_HandleTypeDef *huart;

    ipc_packet_t rx_buffer;
    osMessageQueueId_t rx_queue;
} ipc_driver_t;

void ipc_driver_init(UART_HandleTypeDef *huart, osMessageQueueId_t rx_queue);

void ipc_driver_transmit(ipc_packet_t *packet);

void ipc_driver_HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size);
