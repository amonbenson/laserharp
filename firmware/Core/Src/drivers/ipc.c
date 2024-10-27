#include "drivers/ipc.h"
#include "log.h"

static ipc_driver_t ipc_driver;

void ipc_driver_init(UART_HandleTypeDef *huart, osMessageQueueId_t rx_queue) {
    ipc_driver.huart = huart;
    ipc_driver.rx_queue = rx_queue;

    // start receiving
    // if (HAL_UARTEx_ReceiveToIdle_IT(huart, ipc_driver.rx_buffer, sizeof(ipc_packet_t)) != HAL_OK) {
    //     LOG_ERROR("IPC: Failed to start receiving");
    // }

    // start receiving
    if (HAL_UART_Receive_IT(huart, ipc_driver.rx_buffer, sizeof(ipc_packet_t)) != HAL_OK) {
        LOG_ERROR("IPC: Failed to start receiving");
    }
}

void ipc_driver_transmit(ipc_packet_t *packet) {
    // start a synchronous transmit
    if (HAL_UART_Transmit(ipc_driver.huart, *packet, sizeof(ipc_packet_t), 1000) != HAL_OK) {
        LOG_ERROR("IPC: Failed to transmit packet");
    }
}

// void ipc_driver_HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size) {
//     if (huart != ipc_driver.huart) {
//         return;
//     }

//     if (Size != IPC_PACKET_SIZE) {
//         LOG_ERROR("IPC: Received packet of invalid size: %d", Size);
//         return;
//     }

//     // queue a copy of the received packet
//     if (osMessageQueuePut(ipc_driver.rx_queue, ipc_driver.rx_buffer, 0, 0) != osOK) {
//         LOG_ERROR("IPC: Failed to put packet in rxQueue");
//     }

//     // start receiving again
//     if (HAL_UARTEx_ReceiveToIdle_IT(huart, ipc_driver.rx_buffer, sizeof(ipc_packet_t)) != HAL_OK) {
//         LOG_ERROR("IPC: Failed to start receiving");
//     }
// }

void ipc_driver_HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart != ipc_driver.huart) {
        return;
    }

    // queue a copy of the received packet
    if (osMessageQueuePut(ipc_driver.rx_queue, ipc_driver.rx_buffer, 0, 0) != osOK) {
        LOG_ERROR("IPC: Failed to put packet in rxQueue");
    }

    // start receiving again
    if (HAL_UART_Receive_IT(huart, ipc_driver.rx_buffer, sizeof(ipc_packet_t)) != HAL_OK) {
        LOG_ERROR("IPC: Failed to start receiving");
    }
}
