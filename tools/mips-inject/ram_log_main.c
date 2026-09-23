#include <stdint.h>

#include "sphe_uart.h"

void ram_main(void)
{
    sphe_uart_puts("[sphe] RAM execution OK\n");
    sphe_uart_log_u32("[sphe] status=", SPHE_UART_STATUS_REG);

    /*
     * The recovered STK console protocol treats NUL as end-of-operation.
     * The host's run-ram command returns after receiving this marker.
     */
    sphe_uart_putc_raw(0);
}
