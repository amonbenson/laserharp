#pragma once

#include <stdbool.h>
#include <stdint.h>

#define MIDI_NOTE_OFF 0x80
#define MIDI_NOTE_ON 0x90
#define MIDI_POLY_PRESSURE 0xA0
#define MIDI_CONTROL_CHANGE 0xB0
#define MIDI_PROGRAM_CHANGE 0xC0
#define MIDI_CHANNEL_PRESSURE 0xD0
#define MIDI_PITCH_BEND 0xE0

#define MIDI_IS_CHANNEL_MESSAGE(status) ((status) >= 0x80 && (status) < 0xF0)
#define MIDI_IS_SYSTEM_MESSAGE(status) ((status) >= 0xF0)

typedef struct {
    uint8_t cable_number;
    uint8_t command;
    uint8_t channel;

    union {
        struct {
            uint8_t data1;
            uint8_t data2;
        };
        struct {
            uint8_t note;
            uint8_t velocity;
        } note_on;
        struct {
            uint8_t note;
            uint8_t velocity;
        } note_off;
        struct {
            uint8_t note;
            uint8_t pressure;
        } aftertouch;
        struct {
            uint8_t controller;
            uint8_t value;
        } control_change;
        struct {
            uint8_t program;
            uint8_t _reserved;
        } program_change;
        struct {
            uint8_t pressure;
            uint8_t _reserved;
        } channel_pressure;
        struct {
            uint16_t value;
        } pitch_bend;
    };
} midi_message_t;

typedef int (*midi_ll_transmit_cb_t)(uint8_t *data, uint8_t length, void *context);
typedef int (*midi_ll_receive_cb_t)(uint8_t *data, uint8_t length, bool is_first_byte, void *context);

typedef enum { MIDI_INTERFACE_RAW, MIDI_INTERFACE_USB } midi_interface_type_t;

typedef struct {
    struct {
        midi_ll_transmit_cb_t ll_transmit;
        midi_ll_receive_cb_t ll_receive;
        void *context;
    } cb;

    midi_interface_type_t type;
} midi_interface_config_t;

typedef struct {
    midi_interface_config_t config;
} midi_interface_t;

int midi_init(midi_interface_t *stream, const midi_interface_config_t *config);

int midi_transmit(midi_interface_t *stream, midi_message_t *message);
int midi_receive(midi_interface_t *stream, midi_message_t *message);
