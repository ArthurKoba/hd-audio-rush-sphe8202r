#ifndef SPHE_UART_H
#define SPHE_UART_H

#include <stdint.h>

/*
 * SPHE8202R UART contract recovered from the canonical rev-8203R RAM helper.
 *
 * Runtime system base:
 *   s6 = 0xBFFE8000
 *
 * Confirmed MMIO:
 *   DATA   = s6 + 0x900 = 0xBFFE8900
 *   STATUS = s6 + 0x904 = 0xBFFE8904
 *
 * Confirmed status bits:
 *   bit 0 = TX ready
 *   bit 1 = RX byte available
 *
 * Two vendor TX behaviors exist:
 *   - console putc: write DATA, then software delay;
 *   - stream putc: wait STATUS.bit0, then write DATA.
 *
 * The helpers below use the ready-polled path because it is the stronger
 * general transport contract.  String output preserves the vendor LF->CR
 * behavior.  NUL is the STK-compatible end-of-status marker.
 */

#define SPHE_UART_DATA_REG     (*(volatile uint32_t *)(uintptr_t)0xBFFE8900U)

#define SPHE_UART_STATUS_REG     (*(volatile uint32_t *)(uintptr_t)0xBFFE8904U)

#define SPHE_UART_STATUS_TX_READY 0x00000001U
#define SPHE_UART_STATUS_RX_READY 0x00000002U

static inline int
sphe_uart_tx_ready(void)
{
    return (SPHE_UART_STATUS_REG & SPHE_UART_STATUS_TX_READY) != 0U;
}

static inline int
sphe_uart_rx_ready(void)
{
    return (SPHE_UART_STATUS_REG & SPHE_UART_STATUS_RX_READY) != 0U;
}

static inline void
sphe_uart_putc_raw(uint8_t ch)
{
    while (!sphe_uart_tx_ready()) {
    }
    SPHE_UART_DATA_REG = (uint32_t)ch;
}

static inline void
sphe_uart_putc(char ch)
{
    sphe_uart_putc_raw((uint8_t)ch);
}

static inline int
sphe_uart_try_getc(uint8_t *out)
{
    if (!sphe_uart_rx_ready()) {
        return 0;
    }
    *out = (uint8_t)SPHE_UART_DATA_REG;
    return 1;
}

static inline uint8_t
sphe_uart_getc(void)
{
    while (!sphe_uart_rx_ready()) {
    }
    return (uint8_t)SPHE_UART_DATA_REG;
}

static inline void
sphe_uart_puts(const char *text)
{
    while (*text != '\0') {
        const char ch = *text++;
        sphe_uart_putc(ch);
        if (ch == '\n') {
            sphe_uart_putc('\r');
        }
    }
}

static inline void
sphe_uart_put_hex_nibble(uint8_t value)
{
    value &= 0x0FU;
    sphe_uart_putc(
        (char)(value < 10U ? ('0' + value) : ('A' + value - 10U))
    );
}

static inline void
sphe_uart_put_hex8(uint8_t value)
{
    sphe_uart_put_hex_nibble((uint8_t)(value >> 4));
    sphe_uart_put_hex_nibble(value);
}

static inline void
sphe_uart_put_hex32(uint32_t value)
{
    int shift;
    for (shift = 28; shift >= 0; shift -= 4) {
        sphe_uart_put_hex_nibble(
            (uint8_t)(value >> (uint32_t)shift)
        );
    }
}

static inline void
sphe_uart_log_u32(const char *label, uint32_t value)
{
    sphe_uart_puts(label);
    sphe_uart_puts("0x");
    sphe_uart_put_hex32(value);
    sphe_uart_puts("\n");
}

static inline void
sphe_uart_log_done(void)
{
    sphe_uart_putc_raw(0);
}

#endif
