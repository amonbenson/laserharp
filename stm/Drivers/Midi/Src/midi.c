#include "midi.h"

#include "log.h"
#include "ret_types.h"

int midi_init(midi_interface_t *midi, const midi_interface_config_t *config) {
    midi->config = *config;

    return RET_OK;
}

static int midi_transmit_raw(midi_interface_t *midi, midi_message_t *message) {
    if (MIDI_IS_CHANNEL_MESSAGE(message->command)) {
        uint8_t data[3];
        data[0] = (message->command & 0xF0) | (message->channel & 0x0F);
        data[1] = message->data1;
        data[2] = message->data2;
        RETURN_ON_ERROR(
            midi->config.cb.ll_transmit(data, sizeof(data), midi->config.cb.context), "Failed to transmit raw message");
    } else if (MIDI_IS_SYSTEM_MESSAGE(message->command)) {
        log_error("Command 0x%02X (system messsage) not implemented", message->command);
        return RET_NOT_IMPLEMENTED;
    } else {
        log_error("Invalid command 0x%02X", message->command);
        return RET_INVALID_PARAM;
    }

    return RET_OK;
}

static int midi_transmit_usb(midi_interface_t *midi, midi_message_t *message) {
    if (MIDI_IS_CHANNEL_MESSAGE(message->command)) {
        uint8_t report[4];
        report[0] = (message->cable_number << 4) | (message->command >> 4);
        report[1] = (message->command & 0xF0) | (message->channel & 0x0F);
        report[2] = message->data1;
        report[3] = message->data2;
        RETURN_ON_ERROR(
            midi->config.cb.ll_transmit(report, sizeof(report), midi->config.cb.context), "Failed to transmit report");
    } else if (MIDI_IS_SYSTEM_MESSAGE(message->command)) {
        log_error("Command 0x%02X (system messsage) not implemented", message->command);
        return RET_NOT_IMPLEMENTED;
    } else {
        log_error("Invalid command 0x%02X", message->command);
        return RET_INVALID_PARAM;
    }

    return RET_OK;
}

int midi_transmit(midi_interface_t *midi, midi_message_t *message) {
    if (midi->config.type == MIDI_INTERFACE_RAW) {
        return midi_transmit_raw(midi, message);
    } else {
        return midi_transmit_usb(midi, message);
    }
}

static int midi_receive_raw(midi_interface_t *midi, midi_message_t *message) {
    uint8_t status;

    // raw messages do not contain cable number information, so we set it to 0
    message->cable_number = 0;

    // get the status byte
    RETURN_ON_ERROR(
        midi->config.cb.ll_receive(&status, 1, true, midi->config.cb.context), "Failed to receive status byte");

    if (MIDI_IS_CHANNEL_MESSAGE(status)) {
        uint8_t data[2];
        RETURN_ON_ERROR(midi->config.cb.ll_receive(data, sizeof(data), false, midi->config.cb.context),
            "Failed to receive message");
        message->command = status & 0xF0;
        message->channel = status & 0x0F;
        message->data1 = data[0];
        message->data2 = data[1];
    } else if (MIDI_IS_SYSTEM_MESSAGE(status)) {
        log_error("Command 0x%02X (system messsage) not implemented", status);
        return RET_NOT_IMPLEMENTED;
    } else {
        log_error("Invalid command 0x%02X", status);
        return RET_INVALID_PARAM;
    }

    return RET_OK;
}

static int midi_receive_usb(midi_interface_t *midi, midi_message_t *message) {
    uint8_t report[4];

    // receive the report
    RETURN_ON_ERROR(
        midi->config.cb.ll_receive(report, sizeof(report), true, midi->config.cb.context), "Failed to receive report");

    uint8_t cn = report[0] >> 4;
    uint8_t cin = report[0] & 0x0F;

    if (MIDI_IS_CHANNEL_MESSAGE(cin << 4)) {
        message->cable_number = cn;
        message->command = report[1] & 0xF0;
        message->channel = report[1] & 0x0F;
        message->data1 = report[2];
        message->data2 = report[3];
    } else {
        log_error("CIN 0x%02X not implemented", report[0] << 4);
        return RET_NOT_IMPLEMENTED;
    }

    return RET_OK;
}

int midi_receive(midi_interface_t *midi, midi_message_t *message) {
    if (midi->config.type == MIDI_INTERFACE_RAW) {
        return midi_receive_raw(midi, message);
    } else {
        return midi_receive_usb(midi, message);
    }
}
