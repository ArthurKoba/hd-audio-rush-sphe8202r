#include <stdint.h>

#include "sphe_uart.h"

#define MMIO32(address) (*(volatile uint32_t *)(uintptr_t)(address))

void
ram_main(void)
{
    sphe_uart_puts("[sphe] RAM execution OK\n");

    /* Self-load proof: first instruction should be lui s6,0xbffe. */
    sphe_uart_log_u32("[sphe] self=", MMIO32(0x80019000U));

    /* UART state inherited from the Boot ROM session. */
    sphe_uart_log_u32(
        "[sphe] uart_status=",
        MMIO32(0xBFFE8904U)
    );
    sphe_uart_log_u32("[sphe] uart_div=", MMIO32(0xBFFE8914U));
    sphe_uart_log_u32("[sphe] uart_aux=", MMIO32(0xBFFE8918U));

    /* System-profile registers written by the recovered target init route. */
    sphe_uart_log_u32("[sphe] sys8070=", MMIO32(0xBFFE8070U));
    sphe_uart_log_u32("[sphe] sys8010=", MMIO32(0xBFFE8010U));
    sphe_uart_log_u32("[sphe] sys8014=", MMIO32(0xBFFE8014U));
    sphe_uart_log_u32("[sphe] sys8018=", MMIO32(0xBFFE8018U));

    sphe_uart_log_done();

    for (;;) {
        __asm__ volatile("nop");
    }
}
