#include <stdint.h>

#include "sphe_uart.h"

#define SPHE_RAM_EXEC_BASE 0x80019000U

void
ram_main(void)
{
    sphe_uart_puts("[sphe] RAM execution OK\n");

    /* Self-load proof: first instruction should be lui s6,0xbffe. */
    sphe_uart_log_u32("[sphe] self=", SPHE_MMIO32(SPHE_RAM_EXEC_BASE));

    /* UART state inherited from the Boot ROM session. */
    sphe_uart_log_u32(
        "[sphe] uart_status=",
        SPHE_UART_STATUS_REG
    );
    sphe_uart_log_u32("[sphe] uart_div=", SPHE_UART_DIVISOR_REG);
    sphe_uart_log_u32("[sphe] uart_aux=", SPHE_UART_AUX_REG);

    /* System-profile registers written by the recovered target init route. */
    sphe_uart_log_u32("[sphe] sys8070=", SPHE_SYS_PROFILE_REG_0070);
    sphe_uart_log_u32("[sphe] sys8010=", SPHE_SYS_PROFILE_REG_0010);
    sphe_uart_log_u32("[sphe] sys8014=", SPHE_SYS_PROFILE_REG_0014);
    sphe_uart_log_u32("[sphe] sys8018=", SPHE_SYS_PROFILE_REG_0018);

    sphe_uart_log_done();

    for (;;) {
        __asm__ volatile("nop");
    }
}
