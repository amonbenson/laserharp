#include "log.h"

/* Return/error codes */
#define RET_OK 0x00
#define RET_ERR 0x01
#define RET_BUSY 0x02
#define RET_TIMEOUT 0x03
#define RET_OUT_OF_MEMORY 0x04
#define RET_INVALID_STATE 0x05
#define RET_INVALID_PARAM 0x06
#define RET_INVALID_LENGTH 0x07
#define RET_NOT_FOUND 0x08
#define RET_NOT_IMPLEMENTED 0x09
#define RET_NOT_SUPPORTED 0x0a
#define RET_QUEUE_EMPTY 0x0b
#define RET_QUEUE_FULL 0x0c

#define __RET_PANIC() \
    do { \
        osDelay(100); \
        __disable_irq(); \
        while (1) \
            ; \
    } while (0)

/* Exception control flow macros */
#define RETURN_ON_ERROR(expr, fmt, ...) \
    do { \
        int __ret = (expr); \
        if (__ret != RET_OK) { \
            log_error(fmt " (err 0x%02x)", ##__VA_ARGS__, __ret); \
            return __ret; \
        } \
    } while (0)

#define RETURN_ON_FALSE(expr, err, fmt, ...) \
    do { \
        if (!(expr)) { \
            log_error(fmt " (err 0x%02x)", ##__VA_ARGS__, err); \
            return err; \
        } \
    } while (0)

#define GOTO_ON_ERROR(expr, label, fmt, ...) \
    do { \
        int __ret = (expr); \
        if (__ret != RET_OK) { \
            log_error(fmt " (err 0x%02x)", ##__VA_ARGS__, __ret); \
            ret = __ret; \
            goto label; \
        } \
    } while (0)

#define GOTO_ON_FALSE(expr, err, label, fmt, ...) \
    do { \
        if (!(expr)) { \
            log_error(fmt " (err 0x%02x)", ##__VA_ARGS__, err); \
            ret = err; \
            goto label; \
        } \
    } while (0)

#define PANIC_ON_ERROR(expr, fmt, ...) \
    do { \
        int __ret = (expr); \
        if (__ret != RET_OK) { \
            log_fatal(fmt " (err 0x%02x)", ##__VA_ARGS__, __ret); \
            __RET_PANIC(); \
        } \
    } while (0)

#define PANIC_ON_FALSE(expr, err, fmt, ...) \
    do { \
        if (!(expr)) { \
            log_fatal(fmt " (err 0x%02x)", ##__VA_ARGS__, err); \
            __RET_PANIC(); \
        } \
    } while (0)
