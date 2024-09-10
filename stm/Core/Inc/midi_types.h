#pragma once

#include <stdint.h>

#define MIDI_PACKET_FMT "cable=%d, command=0x%02X, channel=%d, data1=%d, data2=%d"
#define MIDI_PACKET_FMT_ARGS(packet) \
    (packet)->cable, (packet)->command, (packet)->channel, (packet)->data1, (packet)->data2

typedef struct {
    uint8_t cable;
    uint8_t command;
    uint8_t channel;
    uint8_t data1;
    uint8_t data2;
} midi_packet_t;
