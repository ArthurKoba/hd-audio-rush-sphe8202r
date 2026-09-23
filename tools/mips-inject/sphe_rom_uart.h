#ifndef SPHE_ROM_UART_H
#define SPHE_ROM_UART_H

#include <stdint.h>

/*
 * SPHE8202R ROM-loader/debug UART contract recovered from the target-specific
 * RAM helper used by STK rev-8203R.
 *
 * Runtime convention:
 *   s6 = 0xBFFE8000
 *
 * Registers:
 *   data/status live at s6+0x900 / s6+0x904.
 *
 * Confirmed bits:
 *   status bit 0 -> TX ready
 *   status bit 1 -> RX byte available
 */

#define SPHE_S6_BASE      0xBFFE8000u
#define SPHE_UART_DATA    (*(volatile uint32_t *)(SPHE_S6_BASE + 0x0900u))
#define SPHE_UART_STATUS  (*(volatile uint32_t *)(SPHE_S6_BASE + 0x0904u))

static inline void sphe_uart_putc(uint8_t ch)
{
    while ((SPHE_UART_STATUS & 0x1u) == 0u) {
    }
    SPHE_UART_DATA = (uint32_t)ch;
}

static inline uint8_t sphe_uart_getc(void)
{
    while ((SPHE_UART_STATUS & 0x2u) == 0u) {
    }
    return (uint8_t)SPHE_UART_DATA;
}

static inline int sphe_uart_try_getc(uint8_t *out)
{
    if ((SPHE_UART_STATUS & 0x2u) == 0u) {
        return 0;
    }
    *out = (uint8_t)SPHE_UART_DATA;
    return 1;
}

static inline void sphe_uart_puts(const char *s)
{
    while (*s != '\0') {
        sphe_uart_putc((uint8_t)*s++);
    }
}

#endif
