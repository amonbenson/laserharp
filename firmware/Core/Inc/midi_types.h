#pragma once

#include "cmsis_compiler.h"
#include <stdint.h>

#define MIDI_PACKET_FMT "%02X %02X %02X %02X"
#define MIDI_PACKET_FMT_ARGS(packet) (packet)->cn_cin, (packet)->status, (packet)->data1, (packet)->data2

__PACKED_STRUCT _midi_packet {
    uint8_t cn_cin;
    uint8_t status;
    uint8_t data1;
    uint8_t data2;
};
typedef struct _midi_packet midi_packet_t;

#define MIDI_PACKET_SIZE sizeof(midi_packet_t)
