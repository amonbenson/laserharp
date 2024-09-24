/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.h
 * @brief          : Header for main.c file.
 *                   This file contains the common defines of the application.
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
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#define LOG_GLOBAL_LEVEL LOG_LEVEL_TRACE
#define LOG_USE_COLOR 1
#include "log.h"
/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */
#define __STRINGIFY(x) #x
#define STRINGIFY(x) __STRINGIFY(x)

#define FIRMWARE_VERSION_MAJOR 0
#define FIRMWARE_VERSION_MINOR 1
#define FIRMWARE_VERSION_PATCH 0
#define FIRMWARE_VERSION_STR \
    STRINGIFY(FIRMWARE_VERSION_MAJOR) "." STRINGIFY(FIRMWARE_VERSION_MINOR) "." STRINGIFY(FIRMWARE_VERSION_PATCH)

#define MIDI_IN_PORTS_NUM 0x01 // Specify input ports number of your device
#define MIDI_OUT_PORTS_NUM 0x01 // Specify output ports number of your device
/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define HUART_DEBUG huart2
#define HUART_DIN huart3
#define LA_TRANSFER_PRESCALAR 128
#define HUART_IPC huart1
#define LA_FADE_TICK_RATE 30
#define LA_VPROBE_Pin GPIO_PIN_1
#define LA_VPROBE_GPIO_Port GPIOA
#define DEBUG_TX_Pin GPIO_PIN_2
#define DEBUG_TX_GPIO_Port GPIOA
#define DEBUG_RX_Pin GPIO_PIN_3
#define DEBUG_RX_GPIO_Port GPIOA
#define LA_CLK_Pin GPIO_PIN_5
#define LA_CLK_GPIO_Port GPIOA
#define LA_DS_Pin GPIO_PIN_7
#define LA_DS_GPIO_Port GPIOA
#define LA_LATCH_Pin GPIO_PIN_1
#define LA_LATCH_GPIO_Port GPIOB
#define BTN_CAL_Pin GPIO_PIN_2
#define BTN_CAL_GPIO_Port GPIOB
#define DIN_TX_Pin GPIO_PIN_10
#define DIN_TX_GPIO_Port GPIOB
#define DIN_RX_Pin GPIO_PIN_11
#define DIN_RX_GPIO_Port GPIOB
#define IPC_TX_Pin GPIO_PIN_9
#define IPC_TX_GPIO_Port GPIOA
#define IPC_RX_Pin GPIO_PIN_10
#define IPC_RX_GPIO_Port GPIOA
#define IPC_SCL_Pin GPIO_PIN_6
#define IPC_SCL_GPIO_Port GPIOB
#define IPC_SDA_Pin GPIO_PIN_7
#define IPC_SDA_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
