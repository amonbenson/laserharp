/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : Main program body
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
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "cmsis_os.h"
#include "usb_device.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "animation.h"
#include "drivers/ipc.h"
#include "drivers/laser_array.h"
#include "drivers/midi_usb.h"
#include "log.h"
#include "midi_types.h"
#include "usbd_midi.h"
#include <stdbool.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;

I2C_HandleTypeDef hi2c1;

SPI_HandleTypeDef hspi1;

TIM_HandleTypeDef htim2;
TIM_HandleTypeDef htim3;
DMA_HandleTypeDef hdma_tim3_ch4_up;

UART_HandleTypeDef huart1;
UART_HandleTypeDef huart2;
UART_HandleTypeDef huart3;

/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
    .name = "defaultTask",
    .stack_size = 256 * 4,
    .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for usbReceiveTask */
osThreadId_t usbReceiveTaskHandle;
const osThreadAttr_t usbReceiveTask_attributes = {
    .name = "usbReceiveTask",
    .stack_size = 128 * 4,
    .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for ipcReceiveTask */
osThreadId_t ipcReceiveTaskHandle;
const osThreadAttr_t ipcReceiveTask_attributes = {
    .name = "ipcReceiveTask",
    .stack_size = 128 * 4,
    .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for usbRxData */
osMessageQueueId_t usbRxDataHandle;
const osMessageQueueAttr_t usbRxData_attributes = { .name = "usbRxData" };
/* Definitions for ipcRxData */
osMessageQueueId_t ipcRxDataHandle;
const osMessageQueueAttr_t ipcRxData_attributes = { .name = "ipcRxData" };
/* Definitions for printfSemaphore */
osSemaphoreId_t printfSemaphoreHandle;
const osSemaphoreAttr_t printfSemaphore_attributes = { .name = "printfSemaphore" };
/* Definitions for globalStatus */
osEventFlagsId_t globalStatusHandle;
const osEventFlagsAttr_t globalStatus_attributes = { .name = "globalStatus" };
/* USER CODE BEGIN PV */
laser_array_t laser_array;
animator_t animator;

uint8_t stored_brightness[LA_NUM_DIODES];
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_USART3_UART_Init(void);
static void MX_SPI1_Init(void);
static void MX_TIM2_Init(void);
static void MX_TIM3_Init(void);
static void MX_I2C1_Init(void);
static void MX_ADC1_Init(void);
void StartDefaultTask(void *argument);
void StartUsbReceiveTask(void *argument);
void StartIpcReceiveTask(void *argument);

/* USER CODE BEGIN PFP */
int _write(int file, char *ptr, int len);
void USBD_MIDI_DataInHandler(uint8_t *usb_rx_buffer, uint8_t usb_rx_buffer_length);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
int _write(int file, char *ptr, int len) {
    osSemaphoreAcquire(printfSemaphoreHandle, osWaitForever);
    HAL_UART_Transmit(&huart2, (uint8_t *) ptr, len, 0xFFFF);
    osSemaphoreRelease(printfSemaphoreHandle);

    return len;
}

// void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size) {
//     ipc_driver_HAL_UARTEx_RxEventCallback(huart, Size);
// }

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    ipc_driver_HAL_UART_RxCpltCallback(huart);
}
/* USER CODE END 0 */

/**
 * @brief  The application entry point.
 * @retval int
 */
int main(void) {
    /* USER CODE BEGIN 1 */

    /* USER CODE END 1 */

    /* MCU Configuration--------------------------------------------------------*/

    /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
    HAL_Init();

    /* USER CODE BEGIN Init */

    /* USER CODE END Init */

    /* Configure the system clock */
    SystemClock_Config();

    /* USER CODE BEGIN SysInit */

    /* USER CODE END SysInit */

    /* Initialize all configured peripherals */
    MX_GPIO_Init();
    MX_DMA_Init();
    MX_USART1_UART_Init();
    MX_USART2_UART_Init();
    MX_USART3_UART_Init();
    MX_SPI1_Init();
    MX_TIM2_Init();
    MX_TIM3_Init();
    MX_I2C1_Init();
    MX_ADC1_Init();
    /* USER CODE BEGIN 2 */

    /* USER CODE END 2 */

    /* Init scheduler */
    osKernelInitialize();

    /* USER CODE BEGIN RTOS_MUTEX */
    /* add mutexes, ... */
    /* USER CODE END RTOS_MUTEX */

    /* Create the semaphores(s) */
    /* creation of printfSemaphore */
    printfSemaphoreHandle = osSemaphoreNew(1, 0, &printfSemaphore_attributes);

    /* USER CODE BEGIN RTOS_SEMAPHORES */
    osSemaphoreRelease(printfSemaphoreHandle);
    /* USER CODE END RTOS_SEMAPHORES */

    /* USER CODE BEGIN RTOS_TIMERS */
    /* start timers, add new ones, ... */
    /* USER CODE END RTOS_TIMERS */

    /* Create the queue(s) */
    /* creation of usbRxData */
    usbRxDataHandle = osMessageQueueNew(32, sizeof(midi_packet_t), &usbRxData_attributes);

    /* creation of ipcRxData */
    ipcRxDataHandle = osMessageQueueNew(32, sizeof(ipc_packet_t), &ipcRxData_attributes);

    /* USER CODE BEGIN RTOS_QUEUES */
    /* add queues, ... */
    /* USER CODE END RTOS_QUEUES */

    /* Create the thread(s) */
    /* creation of defaultTask */
    defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

    /* creation of usbReceiveTask */
    usbReceiveTaskHandle = osThreadNew(StartUsbReceiveTask, NULL, &usbReceiveTask_attributes);

    /* creation of ipcReceiveTask */
    ipcReceiveTaskHandle = osThreadNew(StartIpcReceiveTask, NULL, &ipcReceiveTask_attributes);

    /* USER CODE BEGIN RTOS_THREADS */
    /* add threads, ... */
    /* USER CODE END RTOS_THREADS */

    /* Create the event(s) */
    /* creation of globalStatus */
    globalStatusHandle = osEventFlagsNew(&globalStatus_attributes);

    /* USER CODE BEGIN RTOS_EVENTS */

    // initialize drivers
    midi_usb_driver_init(usbRxDataHandle);
    ipc_driver_init(&huart1, ipcRxDataHandle);

    const laser_array_config_t laser_array_config = {
        .hspi = &hspi1,
        .htim_transfer = &htim3,
        .htim_fade = &htim2,
        .rclk_channel = TIM_CHANNEL_4,
    };
    laser_array_init(&laser_array, &laser_array_config);

    // initialize animator
    const animator_config_t animator_config = {
        .laser_array = &laser_array,
    };
    animator_init(&animator, &animator_config);
    /* USER CODE END RTOS_EVENTS */

    /* Start scheduler */
    osKernelStart();

    /* We should never get here as control is now taken by the scheduler */
    /* Infinite loop */
    /* USER CODE BEGIN WHILE */
    while (1) {
        /* USER CODE END WHILE */

        /* USER CODE BEGIN 3 */
    }
    /* USER CODE END 3 */
}

/**
 * @brief System Clock Configuration
 * @retval None
 */
void SystemClock_Config(void) {
    RCC_OscInitTypeDef RCC_OscInitStruct = { 0 };
    RCC_ClkInitTypeDef RCC_ClkInitStruct = { 0 };
    RCC_PeriphCLKInitTypeDef PeriphClkInit = { 0 };

    /** Initializes the RCC Oscillators according to the specified parameters
     * in the RCC_OscInitTypeDef structure.
     */
    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    RCC_OscInitStruct.HSEState = RCC_HSE_ON;
    RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    RCC_OscInitStruct.HSIState = RCC_HSI_ON;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) {
        Error_Handler();
    }

    /** Initializes the CPU, AHB and APB buses clocks
     */
    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

    if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK) {
        Error_Handler();
    }
    PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC | RCC_PERIPHCLK_USB;
    PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV6;
    PeriphClkInit.UsbClockSelection = RCC_USBCLKSOURCE_PLL_DIV1_5;
    if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK) {
        Error_Handler();
    }
}

/**
 * @brief ADC1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_ADC1_Init(void) {

    /* USER CODE BEGIN ADC1_Init 0 */

    /* USER CODE END ADC1_Init 0 */

    ADC_ChannelConfTypeDef sConfig = { 0 };

    /* USER CODE BEGIN ADC1_Init 1 */

    /* USER CODE END ADC1_Init 1 */

    /** Common config
     */
    hadc1.Instance = ADC1;
    hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
    hadc1.Init.ContinuousConvMode = DISABLE;
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    hadc1.Init.NbrOfConversion = 1;
    if (HAL_ADC_Init(&hadc1) != HAL_OK) {
        Error_Handler();
    }

    /** Configure Regular Channel
     */
    sConfig.Channel = ADC_CHANNEL_1;
    sConfig.Rank = ADC_REGULAR_RANK_1;
    sConfig.SamplingTime = ADC_SAMPLETIME_1CYCLE_5;
    if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK) {
        Error_Handler();
    }
    /* USER CODE BEGIN ADC1_Init 2 */

    /* USER CODE END ADC1_Init 2 */
}

/**
 * @brief I2C1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_I2C1_Init(void) {

    /* USER CODE BEGIN I2C1_Init 0 */

    /* USER CODE END I2C1_Init 0 */

    /* USER CODE BEGIN I2C1_Init 1 */

    /* USER CODE END I2C1_Init 1 */
    hi2c1.Instance = I2C1;
    hi2c1.Init.ClockSpeed = 100000;
    hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
    hi2c1.Init.OwnAddress1 = 0;
    hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c1.Init.OwnAddress2 = 0;
    hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&hi2c1) != HAL_OK) {
        Error_Handler();
    }
    /* USER CODE BEGIN I2C1_Init 2 */

    /* USER CODE END I2C1_Init 2 */
}

/**
 * @brief SPI1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_SPI1_Init(void) {

    /* USER CODE BEGIN SPI1_Init 0 */

    /* USER CODE END SPI1_Init 0 */

    /* USER CODE BEGIN SPI1_Init 1 */

    /* USER CODE END SPI1_Init 1 */
    /* SPI1 parameter configuration*/
    hspi1.Instance = SPI1;
    hspi1.Init.Mode = SPI_MODE_MASTER;
    hspi1.Init.Direction = SPI_DIRECTION_2LINES;
    hspi1.Init.DataSize = SPI_DATASIZE_16BIT;
    hspi1.Init.CLKPolarity = SPI_POLARITY_LOW;
    hspi1.Init.CLKPhase = SPI_PHASE_1EDGE;
    hspi1.Init.NSS = SPI_NSS_SOFT;
    hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_128;
    hspi1.Init.FirstBit = SPI_FIRSTBIT_MSB;
    hspi1.Init.TIMode = SPI_TIMODE_DISABLE;
    hspi1.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    hspi1.Init.CRCPolynomial = 10;
    if (HAL_SPI_Init(&hspi1) != HAL_OK) {
        Error_Handler();
    }
    /* USER CODE BEGIN SPI1_Init 2 */

    /* USER CODE END SPI1_Init 2 */
}

/**
 * @brief TIM2 Initialization Function
 * @param None
 * @retval None
 */
static void MX_TIM2_Init(void) {

    /* USER CODE BEGIN TIM2_Init 0 */

    /* USER CODE END TIM2_Init 0 */

    TIM_ClockConfigTypeDef sClockSourceConfig = { 0 };
    TIM_MasterConfigTypeDef sMasterConfig = { 0 };

    /* USER CODE BEGIN TIM2_Init 1 */

    /* USER CODE END TIM2_Init 1 */
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = 7200 - 1;
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = (10000 / LA_FADE_TICK_RATE) - 1;
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim2) != HAL_OK) {
        Error_Handler();
    }
    sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
    if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK) {
        Error_Handler();
    }
    sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
    sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK) {
        Error_Handler();
    }
    /* USER CODE BEGIN TIM2_Init 2 */

    /* USER CODE END TIM2_Init 2 */
}

/**
 * @brief TIM3 Initialization Function
 * @param None
 * @retval None
 */
static void MX_TIM3_Init(void) {

    /* USER CODE BEGIN TIM3_Init 0 */

    /* USER CODE END TIM3_Init 0 */

    TIM_ClockConfigTypeDef sClockSourceConfig = { 0 };
    TIM_MasterConfigTypeDef sMasterConfig = { 0 };
    TIM_OC_InitTypeDef sConfigOC = { 0 };

    /* USER CODE BEGIN TIM3_Init 1 */

    /* USER CODE END TIM3_Init 1 */
    htim3.Instance = TIM3;
    htim3.Init.Prescaler = LA_TRANSFER_PRESCALAR - 1;
    htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim3.Init.Period = 18 - 1;
    htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim3) != HAL_OK) {
        Error_Handler();
    }
    sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
    if (HAL_TIM_ConfigClockSource(&htim3, &sClockSourceConfig) != HAL_OK) {
        Error_Handler();
    }
    if (HAL_TIM_OC_Init(&htim3) != HAL_OK) {
        Error_Handler();
    }
    sMasterConfig.MasterOutputTrigger = TIM_TRGO_UPDATE;
    sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    if (HAL_TIMEx_MasterConfigSynchronization(&htim3, &sMasterConfig) != HAL_OK) {
        Error_Handler();
    }
    sConfigOC.OCMode = TIM_OCMODE_TOGGLE;
    sConfigOC.Pulse = 0;
    sConfigOC.OCPolarity = TIM_OCPOLARITY_LOW;
    sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
    if (HAL_TIM_OC_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_4) != HAL_OK) {
        Error_Handler();
    }
    /* USER CODE BEGIN TIM3_Init 2 */

    /* USER CODE END TIM3_Init 2 */
    HAL_TIM_MspPostInit(&htim3);
}

/**
 * @brief USART1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_USART1_UART_Init(void) {

    /* USER CODE BEGIN USART1_Init 0 */

    /* USER CODE END USART1_Init 0 */

    /* USER CODE BEGIN USART1_Init 1 */

    /* USER CODE END USART1_Init 1 */
    huart1.Instance = USART1;
    huart1.Init.BaudRate = 115200;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart1) != HAL_OK) {
        Error_Handler();
    }
    /* USER CODE BEGIN USART1_Init 2 */

    /* USER CODE END USART1_Init 2 */
}

/**
 * @brief USART2 Initialization Function
 * @param None
 * @retval None
 */
static void MX_USART2_UART_Init(void) {

    /* USER CODE BEGIN USART2_Init 0 */

    /* USER CODE END USART2_Init 0 */

    /* USER CODE BEGIN USART2_Init 1 */

    /* USER CODE END USART2_Init 1 */
    huart2.Instance = USART2;
    huart2.Init.BaudRate = 115200;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart2) != HAL_OK) {
        Error_Handler();
    }
    /* USER CODE BEGIN USART2_Init 2 */

    /* USER CODE END USART2_Init 2 */
}

/**
 * @brief USART3 Initialization Function
 * @param None
 * @retval None
 */
static void MX_USART3_UART_Init(void) {

    /* USER CODE BEGIN USART3_Init 0 */

    /* USER CODE END USART3_Init 0 */

    /* USER CODE BEGIN USART3_Init 1 */

    /* USER CODE END USART3_Init 1 */
    huart3.Instance = USART3;
    huart3.Init.BaudRate = 31250;
    huart3.Init.WordLength = UART_WORDLENGTH_8B;
    huart3.Init.StopBits = UART_STOPBITS_1;
    huart3.Init.Parity = UART_PARITY_NONE;
    huart3.Init.Mode = UART_MODE_TX_RX;
    huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart3.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart3) != HAL_OK) {
        Error_Handler();
    }
    /* USER CODE BEGIN USART3_Init 2 */

    /* USER CODE END USART3_Init 2 */
}

/**
 * Enable DMA controller clock
 */
static void MX_DMA_Init(void) {

    /* DMA controller clock enable */
    __HAL_RCC_DMA1_CLK_ENABLE();

    /* DMA interrupt init */
    /* DMA1_Channel3_IRQn interrupt configuration */
    HAL_NVIC_SetPriority(DMA1_Channel3_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel3_IRQn);
}

/**
 * @brief GPIO Initialization Function
 * @param None
 * @retval None
 */
static void MX_GPIO_Init(void) {
    GPIO_InitTypeDef GPIO_InitStruct = { 0 };
    /* USER CODE BEGIN MX_GPIO_Init_1 */
    /* USER CODE END MX_GPIO_Init_1 */

    /* GPIO Ports Clock Enable */
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    /*Configure GPIO pin : BTN_CAL_Pin */
    GPIO_InitStruct.Pin = BTN_CAL_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(BTN_CAL_GPIO_Port, &GPIO_InitStruct);

    /* USER CODE BEGIN MX_GPIO_Init_2 */
    /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/* USER CODE BEGIN Header_StartDefaultTask */
/**
 * @brief  Function implementing the defaultTask thread.
 * @param  argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void *argument) {
    /* init code for USB_DEVICE */
    MX_USB_DEVICE_Init();
    /* USER CODE BEGIN 5 */

    printf("\n\n\n");
    LOG_INFO("Laserharp Firmware version %s", FIRMWARE_VERSION_STR);
    LOG_INFO("Created by Amon Benson");
    LOG_INFO("Compiled on %s at %s", __DATE__, __TIME__);

    // enable all lasers on startup
    for (uint8_t i = 0; i < LA_NUM_DIODES; i++) {
        laser_array_set_brightness(&laser_array, i, LA_NUM_BRIGHTNESS_LEVELS - 1);
    }

    // play the boot animation
    animator_play(&animator, ANIMATION_BOOT, 5.0, ANIMATION_LOOP);

    for (;;) {
        // update the animator. Assume a fixed time step of 20ms
        animator_update(&animator, 0.02);

        // check if we need to restore the stored brightness values. This will happen at the end of an animation if the
        // follow_action was set to ANIMATION_STOP_RESTORE
        if (animator_is_restore_required(&animator)) {
            for (uint8_t i = 0; i < LA_NUM_DIODES; i++) {
                laser_array_set_brightness(&laser_array, i, stored_brightness[i]);
            }
        }

        osDelay(20);
    }
    /* USER CODE END 5 */
}

/* USER CODE BEGIN Header_StartUsbReceiveTask */
/**
 * @brief Function implementing the usbReceiveTask thread.
 * @param argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartUsbReceiveTask */
void StartUsbReceiveTask(void *argument) {
    /* USER CODE BEGIN StartUsbReceiveTask */
    midi_packet_t packet;

    for (;;) {
        // wait for a packet to be received
        if (osMessageQueueGet(usbRxDataHandle, &packet, NULL, osWaitForever) != osOK) {
            LOG_ERROR("USB MIDI: Failed to get packet from usbRxData");
            continue;
        }

        // print the received packet
        LOG_TRACE("USB MIDI: Received packet: " MIDI_PACKET_FMT, MIDI_PACKET_FMT_ARGS(&packet));

        // forward the midi packet to the Raspberry Pi
        ipc_packet_t ipc_packet = { 0 };
        ipc_packet[0] = packet.cn_cin & 0xf0; // force cable number to 0
        ipc_packet[1] = packet.status;
        ipc_packet[2] = packet.data1;
        ipc_packet[3] = packet.data2;
        ipc_driver_transmit(&ipc_packet);
    }
    /* USER CODE END StartUsbReceiveTask */
}

/* USER CODE BEGIN Header_StartIpcReceiveTask */
static uint8_t ipc_velocity_to_brightness(uint8_t velocity) {
    return (uint8_t) ((uint32_t) velocity * (LA_NUM_BRIGHTNESS_LEVELS - 1) / 127);
}

static uint8_t ipc_brightness_to_velocity(uint8_t brightness) {
    return (uint8_t) ((uint32_t) brightness * 127 / (LA_NUM_BRIGHTNESS_LEVELS - 1));
}

/**
 * @brief Function implementing the ipcReceiveTask thread.
 * @param argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartIpcReceiveTask */
void StartIpcReceiveTask(void *argument) {
    /* USER CODE BEGIN StartIpcReceiveTask */
    ipc_packet_t packet, response;

    for (;;) {
        // wait for a packet to be received
        if (osMessageQueueGet(ipcRxDataHandle, &packet, NULL, osWaitForever) != osOK) {
            LOG_ERROR("IPC: Failed to get packet from ipcRxData");
            continue;
        }

        // print the received packet
        LOG_TRACE("IPC: Received packet: " IPC_PACKET_FMT, IPC_PACKET_FMT_ARGS(&packet));

        // stop the intro animation when the first IPC packet is received
        if (animator_get_current_animation(&animator) == ANIMATION_BOOT && animator_is_playing(&animator)) {
            animator_stop(&animator);
        }

        uint8_t major_code = packet[0] & 0xF0;
        uint8_t code = packet[0];

        // initialize response
        response[0] = code;
        response[1] = 0;
        response[2] = 0;
        response[3] = 0;

        switch (major_code) {
            case 0x00: // forward USB midi out packet
                LOG_WARN("IPC: USB Midi Out not implemented");
                break;
            case 0x10: // forward DIN midi out packet
                LOG_WARN("IPC: Din Midi Out not implemented");
                break;
            default: // check full code
                switch (code) {
                    case 0x80: // set brightness of a single laser
                        LOG_DEBUG("IPC: Set brightness of laser %d", packet[1]);

                        // validate the parameters
                        if (packet[1] >= LA_NUM_DIODES) {
                            LOG_ERROR("IPC: Invalid laser number %d", packet[1]);
                            break;
                        }
                        if (packet[2] > 127) {
                            LOG_ERROR("IPC: Invalid brightness %d", packet[2]);
                            break;
                        }

                        // update the laser diode only if the animator is not playing
                        if (!animator_is_playing(&animator)) {
                            laser_array_set_brightness(&laser_array, packet[1], ipc_velocity_to_brightness(packet[2]));
                        }

                        // store the brightness value
                        stored_brightness[packet[1]] = packet[2];
                        break;
                    case 0x81: // set brightness of multiple lasers
                        LOG_DEBUG("IPC: Set brightness of all lasers");

                        // validate the parameters
                        if (packet[1] > 127) {
                            LOG_ERROR("IPC: Invalid brightness %d", packet[1]);
                            break;
                        }

                        // update all laser diodes at once. Again, skip if the animator is playing
                        for (uint8_t i = 0; i < LA_NUM_DIODES; i++) {
                            if (!animator_is_playing(&animator)) {
                                laser_array_set_brightness(&laser_array, i, ipc_velocity_to_brightness(packet[1]));
                            }

                            stored_brightness[i] = packet[1];
                        }
                        break;
                    case 0x82: // get brightness of a single laser
                        LOG_DEBUG("IPC: Get brightness of laser %d", packet[1]);
                        response[1] = packet[1];
                        response[2] = ipc_brightness_to_velocity(laser_array_get_brightness(&laser_array, packet[1]));
                        ipc_driver_transmit(&response);
                        break;
                    case 0x83: // play animation
                        LOG_DEBUG("IPC: Play animation %d", packet[1]);
                        animator_play(&animator, packet[1], packet[2] * 0.1f, packet[3]);
                        break;
                    case 0x84: // stop animation
                        LOG_DEBUG("IPC: Stop animation");
                        animator_stop(&animator);
                        break;
                    case 0xf0: // firmware version inquiry
                        LOG_DEBUG("IPC: Firmware version inquiry");
                        response[1] = FIRMWARE_VERSION_MAJOR;
                        response[2] = FIRMWARE_VERSION_MINOR;
                        response[3] = FIRMWARE_VERSION_PATCH;
                        ipc_driver_transmit(&response);
                        break;
                    case 0xf1: // reboot
                        LOG_INFO("IPC: Rebooting");
                        NVIC_SystemReset();
                        break;
                    default:
                        LOG_ERROR("IPC: Unknown command %02X", code);
                        break;
                }
        }
    }
    /* USER CODE END StartIpcReceiveTask */
}

/**
 * @brief  Period elapsed callback in non blocking mode
 * @note   This function is called  when TIM1 interrupt took place, inside
 * HAL_TIM_IRQHandler(). It makes a direct call to HAL_IncTick() to increment
 * a global variable "uwTick" used as application time base.
 * @param  htim : TIM handle
 * @retval None
 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
    /* USER CODE BEGIN Callback 0 */

    /* USER CODE END Callback 0 */
    if (htim->Instance == TIM1) {
        HAL_IncTick();
    }
    /* USER CODE BEGIN Callback 1 */
    if (htim->Instance == laser_array.config.htim_fade->Instance) {
        laser_array_fade_TIM_PeriodElapsedHandler(&laser_array);
    }
    /* USER CODE END Callback 1 */
}

/**
 * @brief  This function is executed in case of error occurrence.
 * @retval None
 */
void Error_Handler(void) {
    /* USER CODE BEGIN Error_Handler_Debug */
    /* User can add his own implementation to report the HAL error return state */
    __disable_irq();
    while (1) { }
    /* USER CODE END Error_Handler_Debug */
}

#ifdef USE_FULL_ASSERT
/**
 * @brief  Reports the name of the source file and the source line number
 *         where the assert_param error has occurred.
 * @param  file: pointer to the source file name
 * @param  line: assert_param error line source number
 * @retval None
 */
void assert_failed(uint8_t *file, uint32_t line) {
    /* USER CODE BEGIN 6 */
    /* User can add his own implementation to report the file name and line number,
       ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
    /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
