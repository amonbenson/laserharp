#include "din_midi.h"

#include "log.h"
#include "ret_types.h"

static int din_midi_ll_transmit(uint8_t *data, uint8_t length, void *context) {
    din_midi_t *din = (din_midi_t *) context;

    for (size_t i = 0; i < length; i++) {
        log_trace("DIN TX: 0x%02x (%d/%d bytes)", data[i], i + 1, length);
    }

    HAL_StatusTypeDef hal_ret = HAL_UART_Transmit(din->config.huart, data, length, DIN_MIDI_TX_TIMEOUT);
    RETURN_ON_FALSE(hal_ret == HAL_OK, RET_ERR, "Failed to transmit data");

    return RET_OK;
}

static int din_midi_ll_receive(uint8_t *data, uint8_t length, bool is_first_byte, void *context) {
    din_midi_t *din = (din_midi_t *) context;

    for (size_t i = 0; i < length; i++) {
        uint32_t timeout = (i == 0 && is_first_byte) ? osWaitForever : DIN_MIDI_RX_TIMEOUT;

        osStatus_t os_ret = osMessageQueueGet(din->rx_queue, &data[i], NULL, timeout);
        RETURN_ON_FALSE(os_ret == osOK, RET_QUEUE_EMPTY, "Failed to get data byte from rx queue");

        log_trace("DIN RX: 0x%02x (%d/%d bytes)", data[i], i + 1, length);
    }

    return RET_OK;
}

int din_midi_init(din_midi_t *din, const din_midi_config_t *config) {
    din->config = *config;

    // create the midi interface middleware
    log_debug("Initializing midi interface");
    const midi_interface_config_t midi_config = {
        .cb = { .ll_transmit = din_midi_ll_transmit, .ll_receive = din_midi_ll_receive, .context = din, },
        .type = MIDI_INTERFACE_RAW,
    };
    RETURN_ON_ERROR(midi_init(&din->midi, &midi_config), "Failed to initialize midi interface");

    // create queues and locks
    log_debug("Initializing queues and locks");
    const osMessageQueueAttr_t rx_queue_attr = {
        .name = "din_midi_rx_queue",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    din->rx_queue = osMessageQueueNew(DIN_MIDI_RX_BUFFER_SIZE, sizeof(uint8_t), &rx_queue_attr);
    RETURN_ON_FALSE(din->rx_queue, RET_ERR, "Failed to create rx queue");

    const osSemaphoreAttr_t tx_lock_attr = {
        .name = "din_midi_tx_lock",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    din->tx_lock = osSemaphoreNew(1, 1, &tx_lock_attr);
    RETURN_ON_FALSE(din->tx_lock, RET_ERR, "Failed to create tx lock");

    const osSemaphoreAttr_t rx_lock_attr = {
        .name = "din_midi_rx_lock",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    din->rx_lock = osSemaphoreNew(1, 1, &rx_lock_attr);
    RETURN_ON_FALSE(din->rx_lock, RET_ERR, "Failed to create rx lock");

    // start receiving a single byte
    log_debug("Starting UART receive");
    HAL_StatusTypeDef hal_ret = HAL_UART_Receive_IT(din->config.huart, &din->rx_byte, sizeof(uint8_t));
    RETURN_ON_FALSE(hal_ret == HAL_OK, RET_ERR, "Failed to receive data");

    return RET_OK;
}

int din_midi_transmit(din_midi_t *din, midi_message_t *message) {
    log_trace("Acquiring tx lock");
    osSemaphoreAcquire(din->tx_lock, osWaitForever);

    log_trace("Transmitting message");
    int ret = midi_transmit(&din->midi, message);

    log_trace("Releasing tx lock");
    osSemaphoreRelease(din->tx_lock);

    return ret;
}

int din_midi_receive(din_midi_t *din, midi_message_t *message) {
    log_trace("Acquiring rx lock");
    osSemaphoreAcquire(din->rx_lock, osWaitForever);

    int ret = midi_receive(&din->midi, message);
    log_trace("Received message");

    log_trace("Releasing rx lock");
    osSemaphoreRelease(din->rx_lock);

    return ret;
}

int din_midi_HAL_UART_RxCpltCallback(din_midi_t *din) {
    // store the received byte in the rx queue
    // an error will most likely be a full queue, which is not fatal
    osStatus_t os_ret = osMessageQueuePut(din->rx_queue, &din->rx_byte, 0, 0);
    if (os_ret != osOK) {
        log_warn("DIN RX QUEUE FULL");
    }

    // start receiving the next byte
    // an error here is fatal, because it will essentially break the midi interface
    HAL_StatusTypeDef hal_ret = HAL_UART_Receive_IT(din->config.huart, &din->rx_byte, sizeof(uint8_t));
    PANIC_ON_FALSE(hal_ret == HAL_OK, RET_ERR, "DIN UART receive failed");

    return RET_OK;
}
