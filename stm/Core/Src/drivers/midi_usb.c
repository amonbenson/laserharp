#include "drivers/midi_usb.h"
#include "cmsis_os.h"
#include "log.h"
#include "midi_types.h"
#include "usbd_def.h"
#include "usbd_midi.h"

extern USBD_HandleTypeDef hUsbDeviceFS;

static midi_usb_driver_t midi_usb_driver;

void midi_usb_driver_init(osMessageQueueId_t tx_queue, osMessageQueueId_t rx_queue) {
    midi_usb_driver.tx_queue = tx_queue;
    midi_usb_driver.rx_queue = rx_queue;
}

void midi_usb_ll_driver_tx_process() {
    // get the next packet from the transmit queue
    midi_packet_t packet;
    if (osMessageQueueGet(midi_usb_driver.tx_queue, &packet, NULL, osWaitForever) != osOK) {
        LOG_ERROR("MIDI USB: Failed to get packet from txQueue");
        return;
    }

    // prepare a usb usb_rx_buffer
    uint8_t usb_rx_buffer[4];
    usb_rx_buffer[0] = (packet.cable << 4) | (packet.command >> 4);
    usb_rx_buffer[1] = packet.command | packet.channel;
    usb_rx_buffer[2] = packet.data1;
    usb_rx_buffer[3] = packet.data2;

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
    uint8_t code;
    midi_packet_t packet;

    // parse each packet in the usb_rx_buffer
    while (usb_rx_buffer_length && *usb_rx_buffer != 0x00) {
        packet.cable = usb_rx_buffer[0] >> 4;
        code = usb_rx_buffer[0] & 0x0F;

        switch (code) {
            case MIDI_USB_CIN_NOTE_OFF:
            case MIDI_USB_CIN_NOTE_ON:
            case MIDI_USB_CIN_POLY_KEY_PRESSURE:
            case MIDI_USB_CIN_CONTROL_CHANGE:
            case MIDI_USB_CIN_PROGRAM_CHANGE:
            case MIDI_USB_CIN_CHANNEL_PRESSURE:
            case MIDI_USB_CIN_PITCH_BEND:
                // handle channel messages
                packet.command = usb_rx_buffer[1] & 0xF0;
                packet.channel = usb_rx_buffer[1] & 0x0F;
                packet.data1 = usb_rx_buffer[2];
                packet.data2 = usb_rx_buffer[3];

                // send the packet to the receive queue
                if (osMessageQueuePut(midi_usb_driver.rx_queue, &packet, 0, 0) != osOK) {
                    LOG_ERROR("MIDI USB: Failed to put packet in rxQueue");
                }

                break;
            default:
                LOG_WARN("MIDI USB: Unhandled code: %d", code);
                break;
        }

        usb_rx_buffer += 4;
        usb_rx_buffer_length -= 4;
    }
}
