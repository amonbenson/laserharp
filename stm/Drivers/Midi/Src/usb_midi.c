#include "usb_midi.h"
#include "ret_types.h"
#include "usbd_midi.h"

static int usb_midi_ll_transmit(uint8_t *data, uint8_t length, void *context) {
    usb_midi_t *usb = (usb_midi_t *) context;

    if (!usb_midi_connected(usb)) {
        log_warn("Transmit while not connected");
        return RET_OK;
    }

    if (length % 4 != 0) {
        log_warn("Transmit length should be a multiple of 4 (was %d)", length);
        return RET_INVALID_LENGTH;
    }

    for (size_t i = 0; i < length; i++) {
        log_trace("USB TX: 0x%02x (%d/%d bytes)", data[i], i + 1, length);
    }

    uint8_t usb_ret = USBD_MIDI_SendReport(usb->config.husb, data, length);
    RETURN_ON_FALSE(usb_ret == USBD_OK, RET_ERR, "Failed to send USB report");

    return RET_OK;
}

static int usb_midi_ll_receive(uint8_t *data, uint8_t length, bool is_first_byte, void *context) {
    usb_midi_t *usb = (usb_midi_t *) context;

    uint32_t timeout = is_first_byte ? osWaitForever : USB_MIDI_RX_TIMEOUT;

    for (size_t i = 0; i < length; i++) {
        // printf("B%d = 0x%02X\n", i, data[i]);
        osStatus_t os_ret = osMessageQueueGet(usb->rx_queue, &data[i], NULL, timeout);
        RETURN_ON_FALSE(os_ret == osOK, RET_QUEUE_EMPTY, "Failed to get data byte from rx queue");

        log_trace("USB RX: 0x%02x (%d/%d bytes)", data[i], i + 1, length);
    }

    return RET_OK;
}

int usb_midi_init(usb_midi_t *usb, const usb_midi_config_t *config) {
    usb->config = *config;

    // create the midi interface middleware
    log_debug("Initializing midi interface");
    const midi_interface_config_t midi_config = {
        .cb = {
            .ll_transmit = usb_midi_ll_transmit,
            .ll_receive = usb_midi_ll_receive,
            .context = usb,
        },
        .type = MIDI_INTERFACE_USB
    };
    RETURN_ON_ERROR(midi_init(&usb->midi, &midi_config), "Failed to initialize midi interface");

    // create queues and locks
    log_debug("Initializing queues and locks");
    const osMessageQueueAttr_t rx_queue_attr = {
        .name = "usb_midi_rx_queue",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    usb->rx_queue = osMessageQueueNew(USB_MIDI_RX_BUFFER_SIZE, sizeof(uint8_t), &rx_queue_attr);
    RETURN_ON_FALSE(usb->rx_queue, RET_ERR, "Failed to create rx queue");

    const osSemaphoreAttr_t tx_lock_attr = {
        .name = "usb_midi_tx_lock",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    usb->tx_lock = osSemaphoreNew(1, 1, &tx_lock_attr);
    RETURN_ON_FALSE(usb->tx_lock, RET_ERR, "Failed to create tx lock");

    const osSemaphoreAttr_t rx_lock_attr = {
        .name = "usb_midi_rx_lock",
        .attr_bits = 0,
        .cb_mem = NULL,
        .cb_size = 0,
    };
    usb->rx_lock = osSemaphoreNew(1, 1, &rx_lock_attr);
    RETURN_ON_FALSE(usb->rx_lock, RET_ERR, "Failed to create rx lock");

    return RET_OK;
}

bool usb_midi_connected(usb_midi_t *usb) {
    return USBD_MIDI_GetState(usb->config.husb) == MIDI_IDLE;
}

int usb_midi_transmit(usb_midi_t *usb, midi_message_t *message) {
    log_trace("Acquiring tx lock");
    osSemaphoreAcquire(usb->tx_lock, osWaitForever);

    log_trace("Transmitting message");
    int ret = midi_transmit(&usb->midi, message);

    log_trace("Releasing tx lock");
    osSemaphoreRelease(usb->tx_lock);

    return ret;
}

int usb_midi_receive(usb_midi_t *usb, midi_message_t *message) {
    log_trace("Acquiring rx lock");
    osSemaphoreAcquire(usb->rx_lock, osWaitForever);

    int ret = midi_receive(&usb->midi, message);
    log_trace("Received message");

    log_trace("Releasing rx lock");
    osSemaphoreRelease(usb->rx_lock);

    return ret;
}

int usb_midi_USBD_MIDI_DataInHandler(usb_midi_t *usb, uint8_t *buf, uint8_t len) {
    // receive all reports
    while (len > 0 && *buf != 0) {
        // store each byte in the rx queue
        for (int i = 0; i < 4; i++) {
            osStatus_t os_ret = osMessageQueuePut(usb->rx_queue, &buf[i], 0, 0);
            if (os_ret != osOK) {
                log_warn("USB RX QUEUE FULL");
            }
        }

        buf += 4;
        len -= 4;
    }

    return RET_OK;
}
