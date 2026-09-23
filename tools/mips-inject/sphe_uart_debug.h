#ifndef SPHE_UART_DEBUG_H
#define SPHE_UART_DEBUG_H

#include <stdint.h>

/*
 * UART contract recovered from the target vendor RAM stub.
 *
 * s6 is initialized to 0xBFFE8000 by the vendor stub, but these helpers use
 * absolute MMIO addresses so they do not depend on the original $s6 state.
 */
#define SPHE_UART_DATA     (*(volatile uint32_t *)0xBFFE8900u)
#define SPHE_UART_STATUS   (*(volatile uint32_t *)0xBFFE8904u)
#define SPHE_UART_DIVISOR  (*(volatile uint32_t *)0xBFFE8914u)
#define SPHE_UART_CONTROL  (*(volatile uint32_t *)0xBFFE8918u)

enum sphe_debug_baud {
    SPHE_DEBUG_BAUD_57600  = 0x74,
    SPHE_DEBUG_BAUD_115200 = 0x3A,
    SPHE_DEBUG_BAUD_230400 = 0x1D,
};

static inline void sphe_debug_uart_init(enum sphe_debug_baud divisor)
{
    SPHE_UART_CONTROL = 0;
    SPHE_UART_DIVISOR = (uint32_t)divisor;
}

static inline int sphe_debug_rx_ready(void)
{
    return (SPHE_UART_STATUS & 2u) != 0u;
}

static inline uint8_t sphe_debug_getc(void)
{
    while (!sphe_debug_rx_ready()) {
    }
    return (uint8_t)(SPHE_UART_DATA & 0xffu);
}

static inline void sphe_debug_putc(uint8_t ch)
{
    while ((SPHE_UART_STATUS & 1u) == 0u) {
    }
    SPHE_UART_DATA = ch;
}

static inline void sphe_debug_puts(const char *s)
{
    while (*s != '\0') {
        uint8_t ch = (uint8_t)*s++;
        sphe_debug_putc(ch);
        if (ch == '\n') {
            /* Match the vendor stub's LF -> CR behavior. */
            sphe_debug_putc('\r');
        }
    }
}

static inline void sphe_debug_hex32(uint32_t value)
{
    static const char hex[] = "0123456789ABCDEF";
    for (int shift = 28; shift >= 0; shift -= 4) {
        sphe_debug_putc((uint8_t)hex[(value >> shift) & 0x0f]);
    }
}

static inline void sphe_debug_done(void)
{
    /* The headless loader treats NUL as the completion marker. */
    sphe_debug_putc(0);
}

#endif
