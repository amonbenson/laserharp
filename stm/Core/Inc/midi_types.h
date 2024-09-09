#pragma once

#include <stdint.h>

#define USB_MIDI_CIN_MISC 0x0
#define USB_MIDI_CIN_CABLE 0x1
#define USB_MIDI_CIN_2BYTE 0x2
#define USB_MIDI_CIN_3BYTE 0x3
#define USB_MIDI_CIN_SYSEX_START 0x4
#define USB_MIDI_CIN_SYSEX_END_1BYTE 0x5
#define USB_MIDI_CIN_SYSEX_END_2BYTE 0x6
#define USB_MIDI_CIN_SYSEX_END_3BYTE 0x7
#define USB_MIDI_CIN_NOTE_OFF 0x8
#define USB_MIDI_CIN_NOTE_ON 0x9
#define USB_MIDI_CIN_POLY_KEY_PRESSURE 0xA
#define USB_MIDI_CIN_CONTROL_CHANGE 0xB
#define USB_MIDI_CIN_PROGRAM_CHANGE 0xC
#define USB_MIDI_CIN_CHANNEL_PRESSURE 0xD
#define USB_MIDI_CIN_PITCH_BEND 0xE
#define USB_MIDI_CIN_SINGLE_BYTE 0xF

typedef struct {
    uint8_t cable;
    uint8_t command;
    uint8_t channel;
    uint8_t data1;
    uint8_t data2;
} midi_packet_t;
