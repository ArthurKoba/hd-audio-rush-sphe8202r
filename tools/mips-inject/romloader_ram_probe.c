#include <stdint.h>
#include "sphe_uart_log.h"

void
ram_main(void)
{
    sphe_uart_puts("SPHE8202R RAM probe: entered C code\n");
    sphe_uart_puts("UART TX MMIO=");
    sphe_uart_put_hex32(0xBFFE8900U);
    sphe_uart_puts("\nRAM probe complete\n");

    /*
     * sphe_romloader.py run-ram --wait-nul waits for this terminator.
     */
    sphe_uart_putc(0);

    for (;;) {
        __asm__ volatile("nop");
    }
}
