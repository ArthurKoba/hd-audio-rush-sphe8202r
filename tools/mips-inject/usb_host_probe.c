#include <stdint.h>

#include "sphe_uart.h"

#define MIPS_STATUS_INTERRUPT_ENABLE_BIT 0x00000001U

#define STOCK_SHORT_DELAY_INNER_COUNT 50U
#define STOCK_LONG_DELAY_INNER_COUNT 26998U
#define USB_RESET_GATE_SETTLE_COUNT 100U
#define USB_ROOT_RESET_SETTLE_COUNT 200U
#define USB_ROOT_ENABLE_SETTLE_COUNT 150U
#define USB_ROOT_FINAL_SETTLE_COUNT 500U

static void
stock_short_delay(uint32_t count)
{
    while (count-- != 0U) {
        volatile uint32_t inner = STOCK_SHORT_DELAY_INNER_COUNT;

        while (inner-- != 0U) {
            __asm__ volatile("nop");
        }
    }
}

static void
stock_long_delay(uint32_t count)
{
    while (count-- != 0U) {
        volatile uint32_t inner = STOCK_LONG_DELAY_INNER_COUNT;

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
    status &= ~MIPS_STATUS_INTERRUPT_ENABLE_BIT;
    __asm__ volatile("mtc0 %0, $12" :: "r"(status));
}

static void
cpu_irq_enable(void)
{
    uint32_t status;

    __asm__ volatile("mfc0 %0, $12\n\tnop" : "=r"(status));
    status |= MIPS_STATUS_INTERRUPT_ENABLE_BIT;
    __asm__ volatile("mtc0 %0, $12" :: "r"(status));
}

static void
log_usb_registers(const char *phase)
{
    sphe_uart_puts(phase);
    sphe_uart_puts("\n");

    sphe_uart_log_u32("  sys800c=", SPHE_SYS_USB_RESET_CONTROL_REG);
    sphe_uart_log_u32("  usb0080=", SPHE_USB_TRANSFER_STATE_REG);
    sphe_uart_log_u32("  usb0194=", SPHE_USB_CONTROLLER_STATE_B_REG);
    sphe_uart_log_u32("  usb0284=", SPHE_USB_HOST_INIT_CONTROL_REG);
    sphe_uart_log_u32("  usb0290=", SPHE_USB_ROOT_RESET_CONTROL_REG);
    sphe_uart_log_u32("  usb0294=", SPHE_USB_ROOT_FOLLOWUP_CONFIG_REG);
    sphe_uart_log_u32("  usb02a0=", SPHE_USB_CONTROLLER_PRESENCE_STATUS_REG);
    sphe_uart_log_u32("  usb02a4=", SPHE_USB_CONTROLLER_STATE_A_REG);
    sphe_uart_log_u32("  usb02a8=", SPHE_USB_CONTROLLER_SUBTYPE_STATE_REG);
    sphe_uart_log_u32("  usb02ac=", SPHE_USB_HIGHER_INIT_CONFIG_REG);
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

    value = SPHE_SYS_USB_RESET_CONTROL_REG;
    SPHE_SYS_USB_RESET_CONTROL_REG = value | SPHE_SYS_USB_RESET_GATE_BIT;
    stock_short_delay(USB_RESET_GATE_SETTLE_COUNT);

    value = SPHE_SYS_USB_RESET_CONTROL_REG;
    SPHE_SYS_USB_RESET_CONTROL_REG = value & ~SPHE_SYS_USB_RESET_GATE_BIT;
    stock_short_delay(USB_RESET_GATE_SETTLE_COUNT);

    SPHE_USB_HOST_INIT_CONTROL_REG = SPHE_USB_HOST_INIT_CONTROL_VALUE;

    value = SPHE_USB_ROOT_FOLLOWUP_CONFIG_REG;
    SPHE_USB_ROOT_FOLLOWUP_CONFIG_REG = value & ~SPHE_SYS_USB_RESET_GATE_BIT;

    SPHE_USB_CONTROLLER_PRESENCE_STATUS_REG = SPHE_USB_CONTROLLER_PRESENCE_INIT_VALUE;
    SPHE_USB_TRANSFER_STATE_REG = 0U;
    SPHE_USB_CONTROLLER_STATE_A_REG = SPHE_USB_CONTROLLER_STATE_A_INIT_VALUE;
    SPHE_USB_CONTROLLER_STATE_B_REG = SPHE_USB_CONTROLLER_STATE_B_INIT_VALUE;

    /* Written by the stock higher-level host initializer after base init. */
    SPHE_USB_HIGHER_INIT_CONFIG_REG = SPHE_USB_HIGHER_INIT_CONFIG_VALUE;
}

static uint32_t
recovered_usb_root_reset(uint32_t alternate)
{
    uint32_t value;
    uint32_t branch;

    value = SPHE_USB_ROOT_FOLLOWUP_CONFIG_REG;
    SPHE_USB_ROOT_FOLLOWUP_CONFIG_REG = value & ~SPHE_SYS_USB_RESET_GATE_BIT;
    SPHE_USB_TRANSFER_STATE_REG = 0U;

    SPHE_USB_ROOT_RESET_CONTROL_REG = SPHE_USB_ROOT_RESET_ASSERT_VALUE;
    stock_long_delay(USB_ROOT_RESET_SETTLE_COUNT);
    SPHE_USB_ROOT_RESET_CONTROL_REG = 0U;
    while ((SPHE_USB_ROOT_RESET_CONTROL_REG & SPHE_USB_ROOT_CONTROL_ACTIVE_BIT) != 0U) {
    }
    stock_long_delay(USB_ROOT_RESET_SETTLE_COUNT);

    value = SPHE_USB_ROOT_RESET_CONTROL_REG;
    value |= alternate != 0U ? SPHE_USB_ROOT_CONTROL_ALTERNATE_VALUE : SPHE_USB_ROOT_CONTROL_ENABLE_VALUE;
    SPHE_USB_ROOT_RESET_CONTROL_REG = value;
    stock_long_delay(USB_ROOT_ENABLE_SETTLE_COUNT);

    cpu_irq_disable();
    SPHE_USB_ROOT_RESET_CONTROL_REG = 0U;
    while ((SPHE_USB_ROOT_RESET_CONTROL_REG & SPHE_USB_ROOT_CONTROL_ACTIVE_BIT) != 0U) {
    }
    stock_short_delay(USB_ROOT_RESET_SETTLE_COUNT);

    branch = (SPHE_USB_ROOT_RESET_CONTROL_REG & SPHE_USB_ROOT_BRANCH_STATUS_BIT) != 0U ? 1U : 0U;
    if (branch == 0U) {
        SPHE_USB_TRANSFER_STATE_REG = 0U;
        SPHE_USB_ROOT_FOLLOWUP_CONFIG_REG = SPHE_USB_ROOT_FOLLOWUP_BRANCH0_VALUE;
    } else {
        SPHE_USB_TRANSFER_STATE_REG = SPHE_USB_TRANSFER_BRANCH1_FLAG;
        SPHE_USB_ROOT_FOLLOWUP_CONFIG_REG = SPHE_USB_ROOT_FOLLOWUP_BRANCH1_VALUE;
    }

    cpu_irq_enable();
    stock_long_delay(USB_ROOT_FINAL_SETTLE_COUNT);
    return branch;
}

void
ram_main(void)
{
    sphe_uart_puts("[sphe] USB host root probe\n");

    log_usb_registers("[sphe] before");

    recovered_usb_host_init();

    log_usb_registers("[sphe] after-init");

    if ((SPHE_USB_CONTROLLER_SUBTYPE_STATE_REG & SPHE_USB_SUBTYPE_SKIP_ROOT_RESET_BIT) != 0U) {
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
