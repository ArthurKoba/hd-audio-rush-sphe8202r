#include <stdint.h>

#include "sphe_uart.h"

/*
 * Side-effect-free logging probe for compiler/runtime validation.
 *
 * This does not touch flash and does not change audio state.
 */
__attribute__((used, noinline))
void sphe_uart_logging_probe(uint32_t marker)
{
    sphe_uart_puts("[sphe] probe marker=");
    sphe_uart_puthex32(marker);
    sphe_uart_putc('\n');
}
