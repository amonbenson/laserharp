#pragma once

#include "cmsis_os.h"
#include "midi_types.h"
#include "usbd_def.h"
#include <stddef.h>

#define MIDI_USB_CIN_MISC 0x0
#define MIDI_USB_CIN_CABLE 0x1
#define MIDI_USB_CIN_2BYTE 0x2
#define MIDI_USB_CIN_3BYTE 0x3
#define MIDI_USB_CIN_SYSEX_START 0x4
#define MIDI_USB_CIN_SYSEX_END_1BYTE 0x5
#define MIDI_USB_CIN_SYSEX_END_2BYTE 0x6
#define MIDI_USB_CIN_SYSEX_END_3BYTE 0x7
#define MIDI_USB_CIN_NOTE_OFF 0x8
#define MIDI_USB_CIN_NOTE_ON 0x9
#define MIDI_USB_CIN_POLY_KEY_PRESSURE 0xA
#define MIDI_USB_CIN_CONTROL_CHANGE 0xB
#define MIDI_USB_CIN_PROGRAM_CHANGE 0xC
#define MIDI_USB_CIN_CHANNEL_PRESSURE 0xD
#define MIDI_USB_CIN_PITCH_BEND 0xE
#define MIDI_USB_CIN_SINGLE_BYTE 0xF

typedef struct {
    osMessageQueueId_t rx_queue;
} midi_usb_driver_t;

void midi_usb_driver_init(osMessageQueueId_t rx_queue);

void midi_usb_driver_transmit(midi_packet_t *packet);
