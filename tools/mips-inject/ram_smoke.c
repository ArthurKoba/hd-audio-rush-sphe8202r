#include <stdint.h>
#include "sphe_uart_debug.h"

__attribute__((noreturn))
void ram_main(void)
{
    sphe_debug_puts("SPHE RAM SMOKE OK\n");
    sphe_debug_puts("UART_STATUS=0x");
    sphe_debug_hex32(SPHE_UART_STATUS);
    sphe_debug_puts("\n");
    sphe_debug_done();

    for (;;) {
    }
}
