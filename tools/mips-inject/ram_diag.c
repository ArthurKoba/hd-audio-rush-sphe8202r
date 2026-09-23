#include <stdint.h>
#include "sphe_rom_uart.h"

static void put_hex_nibble(uint8_t v)
{
    v &= 0x0f;
    sphe_uart_putc((uint8_t)(v < 10 ? ('0' + v) : ('A' + v - 10)));
}

static void put_hex8(uint8_t v)
{
    put_hex_nibble((uint8_t)(v >> 4));
    put_hex_nibble(v);
}

static void banner(void)
{
    sphe_uart_puts("SPHE8202R RAM DIAG\n\r");
    sphe_uart_puts("UART=BFFE8900 STATUS=BFFE8904\n\r");
    sphe_uart_puts("commands: ? help, p ping, e echo-next-byte\n\r");
}

void ram_diag_main(void)
{
    banner();

    for (;;) {
        uint8_t ch = sphe_uart_getc();

        if (ch == '?') {
            banner();
        } else if (ch == 'p') {
            sphe_uart_puts("PONG\n\r");
        } else if (ch == 'e') {
            uint8_t next;
            sphe_uart_puts("ECHO ");
            next = sphe_uart_getc();
            put_hex8(next);
            sphe_uart_putc(' ');
            sphe_uart_putc(next);
            sphe_uart_puts("\n\r");
        } else {
            sphe_uart_puts("RX ");
            put_hex8(ch);
            sphe_uart_puts("\n\r");
        }
    }
}
