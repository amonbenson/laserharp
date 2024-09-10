#include "drivers/ipc.h"
#include "log.h"

static ipc_driver_t ipc_driver;

void ipc_driver_init(UART_HandleTypeDef *huart, osMessageQueueId_t rx_queue) {
    ipc_driver.huart = huart;
    ipc_driver.rx_queue = rx_queue;

    // start receiving
    if (HAL_UART_Receive_IT(huart, ipc_driver.rx_buffer, MIDI_PACKET_SIZE) != HAL_OK) {
        LOG_ERROR("IPC: Failed to start receiving");
    }
}

void ipc_driver_transmit(midi_packet_t *packet) {
    // prepare a tx_buffer
    uint8_t tx_buffer[MIDI_PACKET_SIZE];
    tx_buffer[0] = packet->cn_cin;
    tx_buffer[1] = packet->status;
    tx_buffer[2] = packet->data1;
    tx_buffer[3] = packet->data2;

    // start a synchronous transmit
    if (HAL_UART_Transmit(ipc_driver.huart, tx_buffer, MIDI_PACKET_SIZE, HAL_MAX_DELAY) != HAL_OK) {
        LOG_ERROR("IPC: Failed to transmit packet");
    }
}

void ipc_driver_HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size) {
    if (huart != ipc_driver.huart) {
        return;
    }

    if (Size != MIDI_PACKET_SIZE) {
        LOG_ERROR("IPC: Received packet of invalid size: %d", Size);
        return;
    }

    // parse the packet
    midi_packet_t packet;
    packet.cn_cin = ipc_driver.rx_buffer[0];
    packet.status = ipc_driver.rx_buffer[1];
    packet.data1 = ipc_driver.rx_buffer[2];
    packet.data2 = ipc_driver.rx_buffer[3];

    // send the packet to the receive queue
    if (osMessageQueuePut(ipc_driver.rx_queue, &packet, 0, 0) != osOK) {
        LOG_ERROR("IPC: Failed to put packet in rxQueue");
    }
}
