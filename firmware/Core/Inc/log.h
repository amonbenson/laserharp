#pragma once

#define LOG_LEVEL_ERROR 0
#define LOG_LEVEL_WARN 1
#define LOG_LEVEL_INFO 2
#define LOG_LEVEL_DEBUG 3
#define LOG_LEVEL_TRACE 4

#ifndef LOG_GLOBAL_LEVEL
#define LOG_GLOBAL_LEVEL LOG_LEVEL_DEBUG
#endif

#ifndef LOG_USE_COLOR
#define LOG_USE_COLOR 1
#endif

#if LOG_USE_COLOR
#define LOG_COLOR_RESET "\033[0m"
#define LOG_COLOR_RED "\033[1;31m"
#define LOG_COLOR_YELLOW "\033[1;33m"
#define LOG_COLOR_BLUE "\033[1;34m"
#define LOG_COLOR_CYAN "\033[1;36m"
#define LOG_COLOR_WHITE "\033[1;37m"
#else
#define LOG_COLOR_RESET ""
#define LOG_COLOR_RED ""
#define LOG_COLOR_YELLOW ""
#define LOG_COLOR_BLUE ""
#define LOG_COLOR_CYAN ""
#define LOG_COLOR_WHITE ""
#endif

#define LOG_LEVEL_STRING_ERROR LOG_COLOR_RED "ERROR" LOG_COLOR_RESET
#define LOG_LEVEL_STRING_WARN LOG_COLOR_YELLOW "WARN " LOG_COLOR_RESET
#define LOG_LEVEL_STRING_INFO LOG_COLOR_BLUE "INFO " LOG_COLOR_RESET
#define LOG_LEVEL_STRING_DEBUG LOG_COLOR_CYAN "DEBUG" LOG_COLOR_RESET
#define LOG_LEVEL_STRING_TRACE LOG_COLOR_WHITE "TRACE" LOG_COLOR_RESET

// clang-format off
#define LOG_LEVEL_STRING(log_level) \
    (log_level == LOG_LEVEL_ERROR ? LOG_LEVEL_STRING_ERROR : \
    (log_level == LOG_LEVEL_WARN ? LOG_LEVEL_STRING_WARN : \
    (log_level == LOG_LEVEL_INFO ? LOG_LEVEL_STRING_INFO : \
    (log_level == LOG_LEVEL_DEBUG ? LOG_LEVEL_STRING_DEBUG : \
    (log_level == LOG_LEVEL_TRACE ? LOG_LEVEL_STRING_TRACE : "UNKNOWN")))))
// clang-format on

#define LOG(log_level, format, ...) \
    do { \
        if (log_level <= LOG_GLOBAL_LEVEL) { \
            printf("%s %s:%d: " format "\n", LOG_LEVEL_STRING(log_level), __FILE__, __LINE__, ##__VA_ARGS__); \
        } \
    } while (0)

#if LOG_GLOBAL_LEVEL >= LOG_LEVEL_TRACE
#define LOG_ERROR(format, ...) LOG(LOG_LEVEL_ERROR, format, ##__VA_ARGS__)
#else
#define LOG_ERROR(format, ...)
#endif

#if LOG_GLOBAL_LEVEL >= LOG_LEVEL_WARN
#define LOG_WARN(format, ...) LOG(LOG_LEVEL_WARN, format, ##__VA_ARGS__)
#else
#define LOG_WARN(format, ...)
#endif

#if LOG_GLOBAL_LEVEL >= LOG_LEVEL_INFO
#define LOG_INFO(format, ...) LOG(LOG_LEVEL_INFO, format, ##__VA_ARGS__)
#else
#define LOG_INFO(format, ...)
#endif

#if LOG_GLOBAL_LEVEL >= LOG_LEVEL_DEBUG
#define LOG_DEBUG(format, ...) LOG(LOG_LEVEL_DEBUG, format, ##__VA_ARGS__)
#else
#define LOG_DEBUG(format, ...)
#endif

#if LOG_GLOBAL_LEVEL >= LOG_LEVEL_TRACE
#define LOG_TRACE(format, ...) LOG(LOG_LEVEL_TRACE, format, ##__VA_ARGS__)
#else
#define LOG_TRACE(format, ...)
#endif
