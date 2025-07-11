/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : usb_device.c
 * @version        : v2.0_Cube
 * @brief          : This file implements the USB Device
 ******************************************************************************
 * @attention
 *
 * Copyright (c) 2024 STMicroelectronics.
 * All rights reserved.
 *
 * This software is licensed under terms that can be found in the LICENSE file
 * in the root directory of this software component.
 * If no LICENSE file comes with this software, it is provided AS-IS.
 *
 ******************************************************************************
 */

// Overwrite includes
#ifdef __IGNORE_CODE_GENERATOR__
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/

#include "usb_device.h"
#include "usbd_core.h"
#include "usbd_desc.h"
#include "usbd_hid.h"

/* USER CODE BEGIN Includes */
#endif

#include "usb_device.h"
#include "usbd_core.h"
#include "usbd_desc.h"
#include "usbd_midi.h"
/* USER CODE END Includes */

/* USER CODE BEGIN PV */
/* Private variables ---------------------------------------------------------*/

/* USER CODE END PV */

/* USER CODE BEGIN PFP */
/* Private function prototypes -----------------------------------------------*/

/* USER CODE END PFP */

/* USB Device Core handle declaration. */
USBD_HandleTypeDef hUsbDeviceFS;

/*
 * -- Insert your variables declaration here --
 */
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/*
 * -- Insert your external function declaration here --
 */
/* USER CODE BEGIN 1 */

/* USER CODE END 1 */

/**
  * Init USB device Library, add supported class and start the library
  * @retval None
  */
void MX_USB_DEVICE_Init(void)
{
  /* USER CODE BEGIN USB_DEVICE_Init_PreTreatment */
    /*
     * Force host to re-enumerate device (see https://stm32world.com/wiki/STM32_USB_Device_Renumeration)
     * Assuming D+ is on PA12
     */
    GPIO_InitTypeDef GPIO_InitStruct = { 0 }; // All zeroed out
    GPIO_InitStruct.Pin = GPIO_PIN_12; // Hardcoding this - PA12 is D+
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP; // Push-pull mode
    GPIO_InitStruct.Pull = GPIO_PULLDOWN; // Resetting so pull low
    GPIO_InitStruct.Speed = GPIO_SPEED_HIGH; // Really shouldn't matter in this case
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct); // Initialize with above settings
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_12, GPIO_PIN_RESET); // Yank low
    HAL_Delay(50); // Enough time for host to disconnect device
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_12, GPIO_PIN_SET); // Back high - so host will enumerate
    HAL_GPIO_DeInit(GPIOA, GPIO_PIN_12); // Deinitialize the pin

    // Overwrite usb device initialization
#ifdef __IGNORE_CODE_GENERATOR__
  /* USER CODE END USB_DEVICE_Init_PreTreatment */

  /* Init Device Library, add supported class and start the library. */
  if (USBD_Init(&hUsbDeviceFS, &FS_Desc, DEVICE_FS) != USBD_OK)
  {
    Error_Handler();
  }
  if (USBD_RegisterClass(&hUsbDeviceFS, &USBD_HID) != USBD_OK)
  {
    Error_Handler();
  }
  if (USBD_Start(&hUsbDeviceFS) != USBD_OK)
  {
    Error_Handler();
  }

  /* USER CODE BEGIN USB_DEVICE_Init_PostTreatment */
#endif

    /* Init Device Library, add supported class and start the library. */
    if (USBD_Init(&hUsbDeviceFS, &FS_Desc, DEVICE_FS) != USBD_OK) {
        Error_Handler();
    }
    if (USBD_RegisterClass(&hUsbDeviceFS, &USBD_MIDI) != USBD_OK) {
        Error_Handler();
    }
    if (USBD_Start(&hUsbDeviceFS) != USBD_OK) {
        Error_Handler();
    }
  /* USER CODE END USB_DEVICE_Init_PostTreatment */
}

/**
  * @}
  */

/**
  * @}
  */

