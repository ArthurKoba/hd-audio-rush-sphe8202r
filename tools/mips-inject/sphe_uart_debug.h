#ifndef SPHE_UART_DEBUG_H
#define SPHE_UART_DEBUG_H

#include <stdint.h>

/*
 * UART contract recovered from the target vendor RAM stub.
 *
 * s6 is initialized to 0xBFFE8000 by the vendor stub, but these helpers use
 * absolute MMIO addresses so they do not depend on the original $s6 state.
 */
#define SPHE_UART_DATA   (*(volatile uint32_t *)0xBFFE8900u)
#define SPHE_UART_STATUS (*(volatile uint32_t *)0xBFFE8904u)

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
