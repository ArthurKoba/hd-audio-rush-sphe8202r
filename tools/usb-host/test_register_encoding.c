/* Host-side regression vectors from SPHE8202R native USB producer code.
 * Not an on-board throughput or electrical USB test. */
#include "sphe8202r_usb_host_hw.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    sphe_usb_memory_register_words words;
    assert(sphe_usb_host_encode_command(0x12, 0x83, SPHE_USB_TOKEN_IN, 1)
           == UINT32_C(0x01090312));
    assert(sphe_usb_host_encode_command(0x7F, 0x0F, SPHE_USB_TOKEN_OUT, 0)
           == UINT32_C(0x00010F7F));
    assert(sphe_usb_host_setup_command(0x42) == UINT32_C(0x000D0042));
    assert(sphe_usb_host_status_command(0x42, 0, 1, 1)
           == UINT32_C(0x01010042)); /* IN data => OUT status */
    assert(sphe_usb_host_status_command(0x42, 0, 1, 0)
           == UINT32_C(0x01090042)); /* OUT data => IN status */
    assert(sphe_usb_host_status_command(0x42, 0, 0, 1)
           == UINT32_C(0x01090042)); /* no data => IN status */
    assert((UINT32_C(0x0151) & SPHE_IRQ_BANK1_USB_BIT) == UINT32_C(0x40));

    assert(sphe_usb_host_memory_words(4096, 64,
                                      (uintptr_t)UINT32_C(0x80701234), 0,
                                      &words));
    assert(words.packet_count == 64);
    assert(words.packet_field == 64);
    assert(words.max_packet_bytes == 64);
    assert(words.physical_buffer_address == UINT32_C(0x00701234));
    assert(words.start_word == 1);
    assert(sphe_usb_host_memory_words(4096, 64,
                                      (uintptr_t)UINT32_C(0xA0701234), 1,
                                      &words));
    assert(words.start_word == 2);
    assert(words.physical_buffer_address == UINT32_C(0x00701234));
    assert(!sphe_usb_host_memory_words(0, 64, 0, 1, &words));
    assert(!sphe_usb_host_memory_words(10, 64, 0, 1, &words));
    assert(!sphe_usb_host_memory_words(64, 0, 0, 1, &words));
    assert(!sphe_usb_host_memory_words(64, 64, 0, 1, 0));
    puts("SPHE8202R USB register encoders: host-side vectors PASS");
    return 0;
}
