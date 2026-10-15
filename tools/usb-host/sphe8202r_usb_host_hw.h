/* SPHE8202R USB Host: verified native firmware MMIO encodings.
 * Static R machine-code evidence: AP1 ProgramUsbHostTransfer @0x806A9AA8,
 * ROM SetDefaultInterruptEnableMasks @0x8800086C; project Issue #48.
 * Pure C99/C++ value builders. NOT a running USB driver or silicon benchmark.
 * Unknown register bits and USB link speed are intentionally not defined.
 */
#ifndef SPHE8202R_USB_HOST_HW_H
#define SPHE8202R_USB_HOST_HW_H

#include <stdint.h>

/* CPU-accessible addresses from native SPHE8202R code. */
#define SPHE_USB_FIFO_WRITE_ADDR       UINT32_C(0xBC020178)
#define SPHE_USB_FIFO_READ_ADDR        UINT32_C(0xBC02017C)
#define SPHE_USB_MEMORY_START_STATUS   UINT32_C(0xBC020184)
#define SPHE_USB_MEMORY_PACKET_COUNT   UINT32_C(0xBC020188)
#define SPHE_USB_MEMORY_PACKET_FIELD   UINT32_C(0xBC02018C)
#define SPHE_USB_MEMORY_BUFFER_ADDR    UINT32_C(0xBC020190)
#define SPHE_USB_MEMORY_RESULT_STATUS  UINT32_C(0xBC020198)
#define SPHE_USB_HOST_TRANSFER_CTL     UINT32_C(0xBC020284)
#define SPHE_USB_HOST_TRANSACTION      UINT32_C(0xBC020288)
#define SPHE_USB_HOST_PACKET_LENGTH    UINT32_C(0xBC02028C)
#define SPHE_USB_ROOT_RESET_STATUS     UINT32_C(0xBC020290)
#define SPHE_USB_ROOT_PROFILE          UINT32_C(0xBC020294)
#define SPHE_USB_ROOT_EVENT_STATUS     UINT32_C(0xBC0202A0)
#define SPHE_USB_ROOT_MODE_WORD        UINT32_C(0xBC020080)
#define SPHE_IRQ_BANK1_ENABLE          UINT32_C(0xBFFE8118)
#define SPHE_IRQ_BANK1_PENDING         UINT32_C(0xBFFE8120)
#define SPHE_IRQ_BANK1_ACK             UINT32_C(0xBFFE811C)
#define SPHE_IRQ_BANK1_USB_BIT         UINT32_C(0x40)

/* Exact observed root-port presets selected by (ROOT_RESET_STATUS & 0x10).
 * Their absolute USB line speed has NOT been established for the R target. */
#define SPHE_USB_ROOT_MODE_BIT4_CLEAR  UINT32_C(0x00000000)
#define SPHE_USB_ROOT_MODE_BIT4_SET    UINT32_C(0x80000000)
#define SPHE_USB_ROOT_PROFILE_BIT4_CLEAR UINT32_C(0x02001003)
#define SPHE_USB_ROOT_PROFILE_BIT4_SET UINT32_C(0x08001003)

/* Hardware command PID bits [19:16], device [6:0], endpoint [11:8],
 * initial DATA0/DATA1 bit24, recovered from R IN/OUT/SETUP paths. */
#define SPHE_USB_TOKEN_OUT             UINT32_C(0x01)
#define SPHE_USB_TOKEN_IN              UINT32_C(0x09)
#define SPHE_USB_TOKEN_SETUP           UINT32_C(0x0D)

static inline uint32_t sphe_usb_host_encode_command(uint32_t device_address,
                                                    uint32_t endpoint_address,
                                                    uint32_t token_pid,
                                                    uint32_t data1)
{
    return (device_address & UINT32_C(0x7F))
         | ((endpoint_address & UINT32_C(0x0F)) << 8)
         | ((token_pid & UINT32_C(0x0F)) << 16)
         | ((data1 & UINT32_C(1)) << 24);
}

/* Native SETUP sends 8 FIFO bytes to EP0, with SETUP PID and DATA0.
 * The length=8 and PIO start=1 are separate register writes. */
static inline uint32_t sphe_usb_host_setup_command(uint32_t device_address)
{
    return sphe_usb_host_encode_command(device_address, 0,
                                        SPHE_USB_TOKEN_SETUP, 0);
}

/* Native internal token 0xFE produces a zero-length DATA1 status stage:
 * IN if no IN-data phase; OUT if the preceding data phase was IN.
 * The zero packet length and PIO start are programmed separately. */
static inline uint32_t sphe_usb_host_status_command(uint32_t device_address,
                                                     uint32_t endpoint_address,
                                                     uint32_t had_data,
                                                     uint32_t data_phase_in)
{
    const uint32_t pid = (had_data != 0 && data_phase_in != 0)
                       ? SPHE_USB_TOKEN_OUT : SPHE_USB_TOKEN_IN;
    return sphe_usb_host_encode_command(device_address, endpoint_address, pid, 1);
}

/* Exact MMIO value bundle for the native full-packet memory-engine path.
 * These are register writes, NOT a packed DMA descriptor in RAM.
 * Callers must still establish real hardware packet limits and DMA coherence. */
typedef struct sphe_usb_memory_register_words {
    uint32_t packet_count;
    uint32_t packet_field;
    uint32_t max_packet_bytes;
    uint32_t physical_buffer_address;
    uint32_t start_word;
} sphe_usb_memory_register_words;

/* Represents a complete packet-multiple chunk as used by native R firmware.
 * Nonmultiples need separate short-packet handling; refusing them here does
 * NOT assert they are impossible in the actual hardware. */
static inline int sphe_usb_host_memory_words(uint32_t complete_chunk_bytes,
                                             uint16_t max_packet_bytes,
                                             uintptr_t buffer_address,
                                             int direction_in,
                                             sphe_usb_memory_register_words *out)
{
    if (out == 0 || max_packet_bytes == 0 ||
        complete_chunk_bytes == 0 ||
        complete_chunk_bytes % max_packet_bytes != 0)
        return 0;

    out->packet_count = complete_chunk_bytes / max_packet_bytes;
    out->packet_field = ((uint32_t)max_packet_bytes) & UINT32_C(0x03F0);
    out->max_packet_bytes = max_packet_bytes;
    out->physical_buffer_address =
        ((uint32_t)buffer_address) & UINT32_C(0x1FFFFFFF);
    /* OUT launches by writing 1 to BC020184, IN by writing 2.
     * Do NOT also write BC020284=1 in this native memory-engine sequence. */
    out->start_word = direction_in ? UINT32_C(2) : UINT32_C(1);
    return 1;
}
#endif /* SPHE8202R_USB_HOST_HW_H */
