#pragma once

#include "cmsis_os2.h"
#include "log.h"
#include "midi.h"
#include "stm32f1xx_hal.h"
#include "usbd_midi.h"
#include <stdbool.h>

#define USB_MIDI_RX_BUFFER_SIZE 128
#define USB_MIDI_RX_TIMEOUT 10

#define USB_MIDI_TX_BUFFER_SIZE 128
#define USB_MIDI_TX_TIMEOUT 100

typedef struct {
    USBD_HandleTypeDef *husb;
} usb_midi_config_t;

typedef struct {
    usb_midi_config_t config;
    midi_interface_t midi;

    osSemaphoreId_t tx_lock;
    // TODO: tx queue

    osSemaphoreId_t rx_lock;
    osMessageQueueId_t rx_queue;
    uint8_t rx_byte;
} usb_midi_t;

int usb_midi_init(usb_midi_t *usb, const usb_midi_config_t *config);

bool usb_midi_connected(usb_midi_t *usb);
int usb_midi_transmit(usb_midi_t *usb, midi_message_t *message);
int usb_midi_receive(usb_midi_t *usb, midi_message_t *message);

int usb_midi_USBD_MIDI_DataInHandler(usb_midi_t *usb, uint8_t *buf, uint8_t len);
