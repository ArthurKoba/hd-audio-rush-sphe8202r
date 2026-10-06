#ifndef SPHE_SOC_CONTRACT_H
#define SPHE_SOC_CONTRACT_H

#include <stdint.h>

#define SPHE_MMIO32(address) (*(volatile uint32_t *)(uintptr_t)(address))

/* Recovered SPHE8202R system-window base (runtime s6). */
#define SPHE_SYSTEM_BASE                         0xBFFE8000U
#define SPHE_SYSTEM_REG(offset)                  SPHE_MMIO32(SPHE_SYSTEM_BASE + (offset))

/* System-window registers with confirmed target uses. */
#define SPHE_SYS_USB_RESET_CONTROL_REG           SPHE_SYSTEM_REG(0x000CU)
#define SPHE_SYS_PROFILE_REG_0010                SPHE_SYSTEM_REG(0x0010U)
#define SPHE_SYS_PROFILE_REG_0014                SPHE_SYSTEM_REG(0x0014U)
#define SPHE_SYS_PROFILE_REG_0018                SPHE_SYSTEM_REG(0x0018U)
#define SPHE_SYS_PROFILE_REG_0070                SPHE_SYSTEM_REG(0x0070U)

enum sphe_uart_baud_selector {
    SPHE_UART_BAUD_SELECTOR_57600  = 0,
    SPHE_UART_BAUD_SELECTOR_115200 = 1,
    SPHE_UART_BAUD_SELECTOR_230400 = 2,
};

enum sphe_uart_baud_divisor {
    SPHE_UART_BAUD_DIVISOR_57600  = 0x74,
    SPHE_UART_BAUD_DIVISOR_115200 = 0x3A,
    SPHE_UART_BAUD_DIVISOR_230400 = 0x1D,
};

/* UART register contract. */
#define SPHE_UART_DATA_REG                       SPHE_SYSTEM_REG(0x0900U)
#define SPHE_UART_STATUS_REG                     SPHE_SYSTEM_REG(0x0904U)
#define SPHE_UART_DIVISOR_REG                    SPHE_SYSTEM_REG(0x0914U)
#define SPHE_UART_AUX_REG                        SPHE_SYSTEM_REG(0x0918U)
#define SPHE_UART_STATUS_TX_READY                0x00000001U
#define SPHE_UART_STATUS_RX_READY                0x00000002U

/*
 * GPIO/pad register matrix used by external-input mode and front-panel keys.
 *
 * CONFIRMED native structure:
 * - five register families use the same six-bank layout (bank stride = 4);
 * - SOURCE/SPATIAL setup uses the same bit across family A, family B and
 *   family C, then reads that bit from family E;
 * - ApplyExternalInputHardwareMode writes family D banks 0/4/5 only;
 * - exact mode values below are instruction-proven from raw AP1 bytes.
 *
 * LIKELY behavioral roles:
 * - family C behaves as output-enable because key setup clears the selected
 *   bit before sampling it;
 * - family D behaves as output/value state because source-mode selection
 *   writes exact persistent bit patterns there;
 * - family E behaves as input-value/status because the key readers sample it;
 * - family A/B are mux/ownership setup layers, but exact vendor names remain
 *   UNKNOWN.
 *
 * WITHDRAWN:
 * - the earlier interpretation of 0x09C0..0x09D4 as a dedicated serial-audio
 *   RX peripheral block. Raw cross-family key setup proves this address range
 *   belongs to the wider GPIO/pad register matrix. The synchronous-audio
 *   receiver/pad contract therefore remains open below the 0x18xx layer.
 */
#define SPHE_GPIO_BANK_COUNT                    6U
#define SPHE_GPIO_BANK_STRIDE                   4U
#define SPHE_GPIO_BANK_REG(family_base, bank) \
    SPHE_SYSTEM_REG((family_base) + ((bank) * SPHE_GPIO_BANK_STRIDE))

enum sphe_gpio_register_family_base {
    SPHE_GPIO_SETUP_A_BASE              = 0x14C0,
    SPHE_GPIO_SETUP_B_BASE              = 0x0980,
    SPHE_GPIO_OUTPUT_ENABLE_CANDIDATE_BASE = 0x09A0,
    SPHE_GPIO_OUTPUT_VALUE_CANDIDATE_BASE  = 0x09C0,
    SPHE_GPIO_INPUT_VALUE_CANDIDATE_BASE   = 0x09E0,
};

enum sphe_gpio_bank_index {
    SPHE_GPIO_BANK_0 = 0,
    SPHE_GPIO_BANK_1 = 1,
    SPHE_GPIO_BANK_2 = 2,
    SPHE_GPIO_BANK_3 = 3,
    SPHE_GPIO_BANK_4 = 4,
    SPHE_GPIO_BANK_5 = 5,
};

/* Front-panel keys are sampled from bank 4, bits 13/14. */
#define SPHE_FRONT_PANEL_GPIO_SETUP_A_REG \
    SPHE_GPIO_BANK_REG(SPHE_GPIO_SETUP_A_BASE, SPHE_GPIO_BANK_4)
#define SPHE_FRONT_PANEL_GPIO_SETUP_B_REG \
    SPHE_GPIO_BANK_REG(SPHE_GPIO_SETUP_B_BASE, SPHE_GPIO_BANK_4)
#define SPHE_FRONT_PANEL_GPIO_OUTPUT_ENABLE_CANDIDATE_REG \
    SPHE_GPIO_BANK_REG( \
        SPHE_GPIO_OUTPUT_ENABLE_CANDIDATE_BASE, SPHE_GPIO_BANK_4)
#define SPHE_FRONT_PANEL_KEY_STATUS_REG \
    SPHE_GPIO_BANK_REG(SPHE_GPIO_INPUT_VALUE_CANDIDATE_BASE, SPHE_GPIO_BANK_4)

#define SPHE_FRONT_PANEL_SOURCE_KEY_LEVEL_BIT    0x00002000U
#define SPHE_FRONT_PANEL_SPATIAL_KEY_LEVEL_BIT   0x00004000U

/*
 * CONFIRMED external-input mode output patterns.
 * Family-D's exact vendor name is still LIKELY output-value, not confirmed.
 */
#define SPHE_EXTERNAL_INPUT_MODE_GPIO_REG \
    SPHE_GPIO_BANK_REG(SPHE_GPIO_OUTPUT_VALUE_CANDIDATE_BASE, SPHE_GPIO_BANK_0)
#define SPHE_EXTERNAL_INPUT_MODE_FLAG_A_GPIO_REG \
    SPHE_GPIO_BANK_REG(SPHE_GPIO_OUTPUT_VALUE_CANDIDATE_BASE, SPHE_GPIO_BANK_4)
#define SPHE_EXTERNAL_INPUT_MODE_FLAG_B_GPIO_REG \
    SPHE_GPIO_BANK_REG(SPHE_GPIO_OUTPUT_VALUE_CANDIDATE_BASE, SPHE_GPIO_BANK_5)

#define SPHE_EXTERNAL_INPUT_MODE_GPIO_MASK       0x00000007U
#define SPHE_EXTERNAL_INPUT_MODE_FLAG_A_BIT      0x00008000U
#define SPHE_EXTERNAL_INPUT_MODE_FLAG_B_BIT      0x00000001U

enum sphe_external_input_mode_gpio_bits {
    SPHE_EXTERNAL_INPUT_GPIO_MODE_0 = 0x3,
    SPHE_EXTERNAL_INPUT_GPIO_MODE_1 = 0x5,
    SPHE_EXTERNAL_INPUT_GPIO_MODE_2 = 0x6,
    SPHE_EXTERNAL_INPUT_GPIO_MODE_3 = 0x7,
};

/*
 * LIKELY synchronous-audio pad/mux companion registers.
 * 0x184C/0x186C/0x1870/0x187C are configured in the ROM-called external-sync
 * hardware initializer, are absent from drv_other/WMA/CDROM, and have no AP1
 * use outside that initializer. Exact vendor field names and GPIO19/20/21
 * ownership remain UNKNOWN.
 */
#define SPHE_EXTERNAL_SYNC_PADMUX_CANDIDATE_A_REG SPHE_SYSTEM_REG(0x184CU)
#define SPHE_EXTERNAL_SYNC_PADMUX_CANDIDATE_B_REG SPHE_SYSTEM_REG(0x186CU)
#define SPHE_EXTERNAL_SYNC_PADMUX_CANDIDATE_C_REG SPHE_SYSTEM_REG(0x1870U)
#define SPHE_EXTERNAL_SYNC_PADMUX_CANDIDATE_D_REG SPHE_SYSTEM_REG(0x187CU)

/* CONFIRMED boot programming of the candidate companion fields. */
#define SPHE_EXTERNAL_SYNC_PADMUX_A_FIELD_MASK       0x000000F8U
#define SPHE_EXTERNAL_SYNC_PADMUX_A_BOOT_VALUE       0x00000040U
#define SPHE_EXTERNAL_SYNC_PADMUX_B_FIELD_MASK       0x00000007U
#define SPHE_EXTERNAL_SYNC_PADMUX_B_BOOT_VALUE       0x00000003U
#define SPHE_EXTERNAL_SYNC_PADMUX_C_BOOT_CLEAR_BITS  0x0000DEF8U
#define SPHE_EXTERNAL_SYNC_PADMUX_D_BOOT_CLEAR_BITS  0x0000038FU

/* LIKELY shared companion mux register; AP1 also touches it outside boot init. */
#define SPHE_EXTERNAL_SYNC_SHARED_MUX_CANDIDATE_REG SPHE_SYSTEM_REG(0x1848U)
#define SPHE_EXTERNAL_SYNC_SHARED_MUX_FIELD_MASK     0x00001800U
#define SPHE_EXTERNAL_SYNC_SHARED_MUX_BOOT_VALUE     0x00001000U
#define SPHE_EXTERNAL_SYNC_SHARED_MUX_LATE_CLEAR_BIT 0x00000080U

enum sphe_usb_standard_request {
    SPHE_USB_REQUEST_GET_STATUS        = 2,
    SPHE_USB_REQUEST_SET_ADDRESS       = 5,
    SPHE_USB_REQUEST_GET_DESCRIPTOR    = 6,
    SPHE_USB_REQUEST_SET_CONFIGURATION = 9,
};

enum sphe_usb_request_type {
    SPHE_USB_REQUEST_TYPE_HOST_TO_DEVICE_STANDARD = 0x00,
    SPHE_USB_REQUEST_TYPE_DEVICE_TO_HOST_STANDARD = 0x80,
};

enum sphe_usb_child_class {
    SPHE_USB_CHILD_CLASS_MASS_STORAGE = 0x08,
    SPHE_USB_CHILD_CLASS_HUB          = 0x09,
};

enum sphe_usb_root_state_layout {
    SPHE_USB_ROOT_STATE_SIZE_BYTES    = 32,
    SPHE_USB_ROOT_STATE_WORD_A_OFFSET = 24,
    SPHE_USB_ROOT_STATE_WORD_B_OFFSET = 28,
    SPHE_USB_ROOT_STATE_WORD_A_INIT   = 3,
    SPHE_USB_ROOT_STATE_WORD_B_INIT   = 7,
};

#define SPHE_STATE_USB_MASS_STORAGE_PRIMARY_CONTEXT 0x80002E24U
#define SPHE_STATE_USB_HUB_CONTEXT                  0x80002E2CU
#define SPHE_STATE_USB_ROOT_CONTROLLER_STATE        0x80009860U

#define SPHE_ADDR_PREPARE_USB_GET_DESCRIPTOR_REQUEST    0x806C9410U
#define SPHE_ADDR_PREPARE_USB_SET_ADDRESS_REQUEST       0x806C9478U
#define SPHE_ADDR_PREPARE_USB_GET_STATUS_REQUEST        0x806C94C4U
#define SPHE_ADDR_PREPARE_USB_SET_CONFIGURATION_REQUEST 0x806C9514U
#define SPHE_ADDR_INITIALIZE_USB_HOST_CONTROLLER        0x806AB7F8U
#define SPHE_ADDR_INITIALIZE_USB_CONTROLLER_RUNTIME_STATE 0x806AB8F4U

/* USB host-controller window and recovered register roles. */
#define SPHE_USB_BASE                            0xBC020000U
#define SPHE_USB_REG(offset)                     SPHE_MMIO32(SPHE_USB_BASE + (offset))
#define SPHE_USB_TRANSFER_STATE_REG              SPHE_USB_REG(0x0080U)
#define SPHE_USB_CONTROLLER_STATE_B_REG          SPHE_USB_REG(0x0194U)
#define SPHE_USB_HOST_INIT_CONTROL_REG           SPHE_USB_REG(0x0284U)
#define SPHE_USB_ROOT_RESET_CONTROL_REG          SPHE_USB_REG(0x0290U)
#define SPHE_USB_ROOT_FOLLOWUP_CONFIG_REG        SPHE_USB_REG(0x0294U)
#define SPHE_USB_CONTROLLER_PRESENCE_STATUS_REG  SPHE_USB_REG(0x02A0U)
#define SPHE_USB_CONTROLLER_STATE_A_REG          SPHE_USB_REG(0x02A4U)
#define SPHE_USB_CONTROLLER_SUBTYPE_STATE_REG    SPHE_USB_REG(0x02A8U)
#define SPHE_USB_HIGHER_INIT_CONFIG_REG          SPHE_USB_REG(0x02ACU)

/* Proven stock USB initialization/control constants. */
#define SPHE_SYS_USB_RESET_GATE_BIT              0x00001000U
#define SPHE_USB_ROOT_CONTROL_ACTIVE_BIT         0x00000001U
#define SPHE_USB_ROOT_CONTROL_ENABLE_VALUE       0x00000001U
#define SPHE_USB_ROOT_CONTROL_ALTERNATE_VALUE    0x00000003U
#define SPHE_USB_ROOT_RESET_ASSERT_VALUE         0x00000003U
#define SPHE_USB_ROOT_BRANCH_STATUS_BIT          0x00000010U
#define SPHE_USB_SUBTYPE_SKIP_ROOT_RESET_BIT     0x00000100U
#define SPHE_USB_TRANSFER_BRANCH1_FLAG           0x80000000U

#define SPHE_USB_HOST_INIT_CONTROL_VALUE         4U
#define SPHE_USB_CONTROLLER_PRESENCE_INIT_VALUE  0x30U
#define SPHE_USB_CONTROLLER_STATE_A_INIT_VALUE   3U
#define SPHE_USB_CONTROLLER_STATE_B_INIT_VALUE   7U
#define SPHE_USB_HIGHER_INIT_CONFIG_VALUE        0x46U
#define SPHE_USB_ROOT_FOLLOWUP_BRANCH0_VALUE     0x02001003U
#define SPHE_USB_ROOT_FOLLOWUP_BRANCH1_VALUE     0x08001003U

#endif
