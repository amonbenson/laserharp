#include "ipc.h"

#include "ret_types.h"

static int ipc_ll_transmit(uint8_t *data, uint8_t length, void *context) {
    ipc_t *ipc = (ipc_t *) context;

    for (size_t i = 0; i < length; i++) {
        log_trace("IPC TX: 0x%02x (%d/%d bytes)", data[i], i + 1, length);
    }

    HAL_StatusTypeDef hal_ret = HAL_UART_Transmit(ipc->config.huart, data, length, IPC_TX_TIMEOUT);
    RETURN_ON_FALSE(hal_ret == HAL_OK, RET_ERR, "Failed to transmit data");

    return RET_OK;
}

static int ipc_ll_receive(uint8_t *data, uint8_t length, bool is_first_byte, void *context) {
    ipc_t *ipc = (ipc_t *) context;

    for (size_t i = 0; i < length; i++) {
        uint32_t timeout = (i == 0 && is_first_byte) ? osWaitForever : IPC_RX_TIMEOUT;

        osStatus_t os_ret = osMessageQueueGet(ipc->rx_queue, &data[i], NULL, timeout);
        RETURN_ON_FALSE(os_ret == osOK, RET_QUEUE_EMPTY, "Failed to get data byte from rx queue");

        log_trace("IPC RX: 0x%02x (%d/%d bytes)", data[i], i + 1, length);
    }

    return RET_OK;
}

int ipc_init(ipc_t *ipc, const ipc_config_t *config) {
    ipc->config = *config;

    // create the midi interface middleware
    log_debug("Initializing midi interface");
    const midi_interface_config_t midi_config = {
        .cb = {
                .ll_transmit = ipc_ll_transmit,
                .ll_receive = ipc_ll_receive,
                .context = ipc,
            },
        .type = MIDI_INTERFACE_USB
    };
    RETURN_ON_ERROR(midi_init(&ipc->midi, &midi_config), "Failed to initialize midi interface");

    // create queues and locks
    log_debug("Initializing queues and locks");
    const osMessageQueueAttr_t rx_queue_attr = {
        .name = "ipc_rx_queue",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    ipc->rx_queue = osMessageQueueNew(IPC_RX_BUFFER_SIZE, sizeof(uint8_t), &rx_queue_attr);
    RETURN_ON_FALSE(ipc->rx_queue, RET_ERR, "Failed to create rx queue");

    const osSemaphoreAttr_t tx_lock_attr = {
        .name = "ipc_tx_lock",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    ipc->tx_lock = osSemaphoreNew(1, 1, &tx_lock_attr);
    RETURN_ON_FALSE(ipc->tx_lock, RET_ERR, "Failed to create tx lock");

    const osSemaphoreAttr_t rx_lock_attr = {
        .name = "ipc_rx_lock",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    ipc->rx_lock = osSemaphoreNew(1, 1, &rx_lock_attr);
    RETURN_ON_FALSE(ipc->rx_lock, RET_ERR, "Failed to create rx lock");

    // start receiving a single byte
    log_debug("Starting UART receive");
    HAL_StatusTypeDef hal_ret = HAL_UART_Receive_IT(ipc->config.huart, &ipc->rx_byte, sizeof(uint8_t));
    RETURN_ON_FALSE(hal_ret == HAL_OK, RET_ERR, "Failed to receive data");

    return RET_OK;
}

int ipc_transmit(ipc_t *ipc, midi_message_t *message) {
    log_trace("Acquiring tx lock");
    osSemaphoreAcquire(ipc->tx_lock, osWaitForever);

    log_trace("Transmitting message");
    int ret = midi_transmit(&ipc->midi, message);

    log_trace("Releasing tx lock");
    osSemaphoreRelease(ipc->tx_lock);

    return ret;
}

int ipc_receive(ipc_t *ipc, midi_message_t *message) {
    log_trace("Acquiring rx lock");
    osSemaphoreAcquire(ipc->rx_lock, osWaitForever);

    int ret = midi_receive(&ipc->midi, message);
    log_trace("Received message");

    log_trace("Releasing rx lock");
    osSemaphoreRelease(ipc->rx_lock);

    return ret;
}

int ipc_HAL_UART_RxCpltCallback(ipc_t *ipc) {
    // store the received byte in the rx queue
    osStatus_t os_ret = osMessageQueuePut(ipc->rx_queue, &ipc->rx_byte, 0, 0);
    if (os_ret != osOK) {
        log_warn("IPC RX QUEUE FULL");
    }

    // start receiving the next byte
    HAL_StatusTypeDef hal_ret = HAL_UART_Receive_IT(ipc->config.huart, &ipc->rx_byte, sizeof(uint8_t));
    PANIC_ON_FALSE(hal_ret == HAL_OK, RET_ERR, "IPC UART receive failed");

    return RET_OK;
}
