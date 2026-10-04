#include <stdint.h>

#include "sphe_uart.h"

#define REG32(address) (*(volatile uint32_t *)(uintptr_t)(address))

#define SPHE_SYS_CTRL         REG32(0xBFFE800CU)

#define SPHE_USB_BASE         0xBC020000U
#define SPHE_USB_REG_0080     REG32(SPHE_USB_BASE + 0x080U)
#define SPHE_USB_REG_0194     REG32(SPHE_USB_BASE + 0x194U)
#define SPHE_USB_REG_0284     REG32(SPHE_USB_BASE + 0x284U)
#define SPHE_USB_REG_0290     REG32(SPHE_USB_BASE + 0x290U)
#define SPHE_USB_REG_0294     REG32(SPHE_USB_BASE + 0x294U)
#define SPHE_USB_REG_02A0     REG32(SPHE_USB_BASE + 0x2A0U)
#define SPHE_USB_REG_02A4     REG32(SPHE_USB_BASE + 0x2A4U)
#define SPHE_USB_REG_02A8     REG32(SPHE_USB_BASE + 0x2A8U)
#define SPHE_USB_REG_02AC     REG32(SPHE_USB_BASE + 0x2ACU)

static void
spin_delay(volatile uint32_t count)
{
    while (count-- != 0U) {
        __asm__ volatile("nop");
    }
}

static void
log_usb_registers(const char *phase)
{
    sphe_uart_puts(phase);
    sphe_uart_puts("\n");

    sphe_uart_log_u32("  sys800c=", SPHE_SYS_CTRL);
    sphe_uart_log_u32("  usb0080=", SPHE_USB_REG_0080);
    sphe_uart_log_u32("  usb0194=", SPHE_USB_REG_0194);
    sphe_uart_log_u32("  usb0284=", SPHE_USB_REG_0284);
    sphe_uart_log_u32("  usb0290=", SPHE_USB_REG_0290);
    sphe_uart_log_u32("  usb0294=", SPHE_USB_REG_0294);
    sphe_uart_log_u32("  usb02a0=", SPHE_USB_REG_02A0);
    sphe_uart_log_u32("  usb02a4=", SPHE_USB_REG_02A4);
    sphe_uart_log_u32("  usb02a8=", SPHE_USB_REG_02A8);
    sphe_uart_log_u32("  usb02ac=", SPHE_USB_REG_02AC);
}

/*
 * Instruction-backed subset of the stock host-controller initialization.
 *
 * This probe intentionally stops before root-port reset, EP0 enumeration,
 * class creation and all removable-media/filesystem activity.
 *
 * The stock code uses runtime delay helpers around the system reset gate.
 * The RAM-only probe uses bounded spin delays because the normal runtime is
 * not loaded in the Boot-ROM RAM execution environment. Timing is therefore
 * not claimed hardware-equivalent until target execution proves it.
 */
static void
recovered_usb_host_init(void)
{
    uint32_t value;

    value = SPHE_SYS_CTRL;
    SPHE_SYS_CTRL = value | 0x1000U;
    spin_delay(200000U);

    value = SPHE_SYS_CTRL;
    SPHE_SYS_CTRL = value & ~0x1000U;
    spin_delay(200000U);

    SPHE_USB_REG_0284 = 4U;

    value = SPHE_USB_REG_0294;
    SPHE_USB_REG_0294 = value & ~0x1000U;

    SPHE_USB_REG_02A0 = 0x30U;
    SPHE_USB_REG_0080 = 0U;
    SPHE_USB_REG_02A4 = 3U;
    SPHE_USB_REG_0194 = 7U;

    /* Written by the stock higher-level host initializer after base init. */
    SPHE_USB_REG_02AC = 0x46U;
}

void
ram_main(void)
{
    sphe_uart_puts("[sphe] USB host init probe\n");

    log_usb_registers("[sphe] before");

    recovered_usb_host_init();

    log_usb_registers("[sphe] after");

    sphe_uart_puts(
        "[sphe] init-only; no flash/media/filesystem access\n"
    );
    sphe_uart_log_done();

    for (;;) {
        __asm__ volatile("nop");
    }
}
