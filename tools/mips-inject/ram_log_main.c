#include <stdint.h>

#include "sphe_audio_api.h"

#define MMIO32(address) (*(volatile uint32_t *)(uintptr_t)(address))

static void
log_u32(const char *label, uint32_t value)
{
    sphe_uart_puts(label);
    sphe_uart_puts("0x");
    sphe_uart_put_hex32(value);
    sphe_uart_puts("\n");
}

void
ram_main(void)
{
    sphe_uart_puts("[sphe] RAM execution OK\n");

    /* Self-load proof: first instruction should be lui s6,0xbffe. */
    log_u32("[sphe] self=", MMIO32(0x80019000U));

    /*
     * Raw UART-adjacent/system register observations.  Only TX at
     * 0xBFFE8900 currently has a recovered behavior contract; semantics of
     * 0xBFFE8904 remain UNKNOWN.
     */
    log_u32("[sphe] uart_8904_raw=", MMIO32(0xBFFE8904U));
    log_u32("[sphe] uart_div=", MMIO32(0xBFFE8914U));
    log_u32("[sphe] uart_aux=", MMIO32(0xBFFE8918U));

    /* System-profile registers written by the recovered target init route. */
    log_u32("[sphe] sys8070=", MMIO32(0xBFFE8070U));
    log_u32("[sphe] sys8010=", MMIO32(0xBFFE8010U));
    log_u32("[sphe] sys8014=", MMIO32(0xBFFE8014U));
    log_u32("[sphe] sys8018=", MMIO32(0xBFFE8018U));

    sphe_uart_log_done();

    for (;;) {
        __asm__ volatile("nop");
    }
}
