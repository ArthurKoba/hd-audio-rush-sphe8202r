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
stock_short_delay(uint32_t count)
{
    while (count-- != 0U) {
        volatile uint32_t inner = 50U;

        while (inner-- != 0U) {
            __asm__ volatile("nop");
        }
    }
}

static void
stock_long_delay(uint32_t count)
{
    while (count-- != 0U) {
        volatile uint32_t inner = 26998U;

        while (inner-- != 0U) {
            __asm__ volatile("nop");
        }
    }
}

static void
cpu_irq_disable(void)
{
    uint32_t status;

    __asm__ volatile("mfc0 %0, $12\n\tnop" : "=r"(status));
    status &= ~1U;
    __asm__ volatile("mtc0 %0, $12" :: "r"(status));
}

static void
cpu_irq_enable(void)
{
    uint32_t status;

    __asm__ volatile("mfc0 %0, $12\n\tnop" : "=r"(status));
    status |= 1U;
    __asm__ volatile("mtc0 %0, $12" :: "r"(status));
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
    stock_short_delay(100U);

    value = SPHE_SYS_CTRL;
    SPHE_SYS_CTRL = value & ~0x1000U;
    stock_short_delay(100U);

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

static uint32_t
recovered_usb_root_reset(uint32_t alternate)
{
    uint32_t value;
    uint32_t branch;

    value = SPHE_USB_REG_0294;
    SPHE_USB_REG_0294 = value & ~0x1000U;
    SPHE_USB_REG_0080 = 0U;

    SPHE_USB_REG_0290 = 3U;
    stock_long_delay(200U);
    SPHE_USB_REG_0290 = 0U;
    while ((SPHE_USB_REG_0290 & 1U) != 0U) {
    }
    stock_long_delay(200U);

    value = SPHE_USB_REG_0290;
    value |= alternate != 0U ? 3U : 1U;
    SPHE_USB_REG_0290 = value;
    stock_long_delay(150U);

    cpu_irq_disable();
    SPHE_USB_REG_0290 = 0U;
    while ((SPHE_USB_REG_0290 & 1U) != 0U) {
    }
    stock_short_delay(200U);

    branch = (SPHE_USB_REG_0290 & 0x10U) != 0U ? 1U : 0U;
    if (branch == 0U) {
        SPHE_USB_REG_0080 = 0U;
        SPHE_USB_REG_0294 = 0x02001003U;
    } else {
        SPHE_USB_REG_0080 = 0x80000000U;
        SPHE_USB_REG_0294 = 0x08001003U;
    }

    cpu_irq_enable();
    stock_long_delay(500U);
    return branch;
}

void
ram_main(void)
{
    sphe_uart_puts("[sphe] USB host root probe\n");

    log_usb_registers("[sphe] before");

    recovered_usb_host_init();

    log_usb_registers("[sphe] after-init");

    if ((SPHE_USB_REG_02A8 & 0x100U) != 0U) {
        sphe_uart_puts(
            "[sphe] status 0x2A8 bit0x100 set; stock attach skips root reset\n"
        );
    } else {
        sphe_uart_log_u32(
            "[sphe] root-reset branch=",
            recovered_usb_root_reset(0U)
        );
    }

    log_usb_registers("[sphe] after-root");

    sphe_uart_puts(
        "[sphe] no EP0/media/filesystem access\n"
    );
    sphe_uart_log_done();

    for (;;) {
        __asm__ volatile("nop");
    }
}
