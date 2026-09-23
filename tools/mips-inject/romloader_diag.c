#include <stdint.h>
#include "sphe_audio_api.h"

/*
 * Minimal RAM-only execution probe for the SPHE8202R ROM-loader path.
 *
 * Loaded at VA 0x80019000 by tools/sphe_romloader.py run-ram.
 * It does not access SPI flash or persistent storage.
 */
__attribute__((used, noinline, noreturn))
void romloader_diag_main(void)
{
    sphe_uart_puts("SPHE8202R RAM diag: entered\n");
    sphe_uart_puts("UART log path: ok\n");
    sphe_uart_log_done();

    for (;;) {
        __asm__ volatile ("nop");
    }
}
