#include "drivers/midi_usb.h"
#include "cmsis_os.h"
#include "log.h"
#include "midi_types.h"
#include "usbd_def.h"
#include "usbd_midi.h"

extern USBD_HandleTypeDef hUsbDeviceFS;

static midi_usb_driver_t midi_usb_driver;

void midi_usb_driver_init(osMessageQueueId_t rx_queue) {
    midi_usb_driver.rx_queue = rx_queue;
}

void midi_usb_driver_transmit(midi_packet_t *packet) {
    // prepare a usb usb_rx_buffer
    uint8_t usb_rx_buffer[4];
    usb_rx_buffer[0] = packet->cn_cin;
    usb_rx_buffer[1] = packet->status;
    usb_rx_buffer[2] = packet->data1;
    usb_rx_buffer[3] = packet->data2;

    // wait for the USB device to be ready
    while (USBD_MIDI_GetState(&hUsbDeviceFS) != MIDI_IDLE) {
        osDelay(1);
    }

    // send the usb_rx_buffer
    uint8_t status = USBD_MIDI_SendReport(&hUsbDeviceFS, usb_rx_buffer, 4);
    if (status != USBD_OK) {
        LOG_ERROR("MIDI USB: Failed to send usb_rx_buffer: %d", status);
    }
}

void USBD_MIDI_DataInHandler(uint8_t *usb_rx_buffer, uint8_t usb_rx_buffer_length) {
    while (usb_rx_buffer_length && *usb_rx_buffer != 0x00) {
        midi_packet_t packet;
        packet.cn_cin = usb_rx_buffer[0];
        packet.status = usb_rx_buffer[1];
        packet.data1 = usb_rx_buffer[2];
        packet.data2 = usb_rx_buffer[3];

        // send the packet to the receive queue
        if (osMessageQueuePut(midi_usb_driver.rx_queue, &packet, 0, 0) != osOK) {
            LOG_ERROR("MIDI USB: Failed to put packet in rxQueue");
        }

        usb_rx_buffer += 4;
        usb_rx_buffer_length -= 4;
    }
}
