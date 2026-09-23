#ifndef SPHE_UART_LOG_H
#define SPHE_UART_LOG_H

#include <stdint.h>

/*
 * Minimal UART logging contract recovered from the rev-8203R RAM loader.
 *
 * Implementation proof:
 *   RomLoaderConsolePutc writes the character to s6+0x900 with
 *   s6=0xBFFE8000, i.e. MMIO 0xBFFE8900, then executes a short delay.
 *   RomLoaderConsolePuts emits CR after LF.
 *
 * This is proven for the ROM-loader RAM execution environment. Use from the
 * normal AP1 runtime only after separate execution/board validation.
 */

#define SPHE_UART_TX_MMIO ((volatile uint32_t *)(uintptr_t)0xBFFE8900U)

static inline void
sphe_uart_tx_delay(void)
{
    volatile uint32_t i;
    for (i = 0; i < 0xFFFFU; ++i) {
        __asm__ volatile("" ::: "memory");
    }
}

static inline void
sphe_uart_putc(uint8_t ch)
{
    *SPHE_UART_TX_MMIO = (uint32_t)ch;
    sphe_uart_tx_delay();
}

static inline void
sphe_uart_puts(const char *text)
{
    while (*text != '\0') {
        uint8_t ch = (uint8_t)*text++;
        sphe_uart_putc(ch);
        if (ch == (uint8_t)'\n') {
            sphe_uart_putc((uint8_t)'\r');
        }
    }
}

static inline void
sphe_uart_put_hex32(uint32_t value)
{
    static const char hex[] = "0123456789ABCDEF";
    int shift;

    sphe_uart_puts("0x");
    for (shift = 28; shift >= 0; shift -= 4) {
        sphe_uart_putc((uint8_t)hex[(value >> shift) & 0xFU]);
    }
}

#endif
