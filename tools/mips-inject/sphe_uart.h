#ifndef SPHE_UART_H
#define SPHE_UART_H

#include <stdint.h>

/*
 * Minimal SPHE8202R UART console primitives.
 *
 * Recovered from the target ROM-loader RAM stub:
 *   DATA   = 0xBFFE8900
 *   STATUS = 0xBFFE8904
 *   STATUS bit 0 = TX ready
 *   STATUS bit 1 = RX ready
 *
 * These helpers are freestanding and do not depend on the stock AP1 $gp/$s6
 * state. They are suitable for injected diagnostic/control code.
 */

#define SPHE_UART_DATA_REG   (*(volatile uint32_t *)(uintptr_t)0xBFFE8900U)
#define SPHE_UART_STATUS_REG (*(volatile uint32_t *)(uintptr_t)0xBFFE8904U)

#define SPHE_UART_STATUS_TX_READY 0x00000001U
#define SPHE_UART_STATUS_RX_READY 0x00000002U

static inline void
sphe_uart_putc_raw(uint8_t ch)
{
    while ((SPHE_UART_STATUS_REG & SPHE_UART_STATUS_TX_READY) == 0U) {
    }
    SPHE_UART_DATA_REG = ch;
}

static inline void
sphe_uart_putc(char ch)
{
    sphe_uart_putc_raw((uint8_t)ch);

    /*
     * Match the recovered RAM-loader string behavior: LF is followed by CR.
     */
    if (ch == '\n') {
        sphe_uart_putc_raw('\r');
    }
}

static inline int
sphe_uart_try_getc(uint8_t *out)
{
    if ((SPHE_UART_STATUS_REG & SPHE_UART_STATUS_RX_READY) == 0U) {
        return 0;
    }
    *out = (uint8_t)SPHE_UART_DATA_REG;
    return 1;
}

static inline uint8_t
sphe_uart_getc(void)
{
    while ((SPHE_UART_STATUS_REG & SPHE_UART_STATUS_RX_READY) == 0U) {
    }
    return (uint8_t)SPHE_UART_DATA_REG;
}

static inline void
sphe_uart_puts(const char *text)
{
    while (*text != '\0') {
        sphe_uart_putc(*text++);
    }
}

static inline void
sphe_uart_puthex4(uint8_t value)
{
    value &= 0x0FU;
    sphe_uart_putc_raw(
        (uint8_t)(value < 10U ? ('0' + value) : ('A' + value - 10U))
    );
}

static inline void
sphe_uart_puthex8(uint8_t value)
{
    sphe_uart_puthex4((uint8_t)(value >> 4));
    sphe_uart_puthex4(value);
}

static inline void
sphe_uart_puthex32(uint32_t value)
{
    int shift;
    for (shift = 28; shift >= 0; shift -= 4) {
        sphe_uart_puthex4((uint8_t)(value >> shift));
    }
}

static inline void
sphe_uart_log_u32(const char *label, uint32_t value)
{
    sphe_uart_puts(label);
    sphe_uart_puts("0x");
    sphe_uart_puthex32(value);
    sphe_uart_putc('\n');
}

#endif
