#ifndef SPHE_AUDIO_CONTROL_H
#define SPHE_AUDIO_CONTROL_H

#include <stdbool.h>
#include <stdint.h>

#include "sphe_audio_api.h"

/*
 * Transport-neutral minimal audio control plane.
 *
 * This is NOT an inter-chip wire protocol.  It is a small stateful API that
 * can later be bound to the recovered SPHE <-> secondary-controller transport.
 * Only behavior contracts already recovered from the target firmware are
 * exposed here.
 */

struct sphe_audio_status {
    uint32_t decoder_state;
    uint16_t downsample_mask;

    uint8_t master_volume;
    uint8_t master_muted;

    uint8_t eq_selection;
    uint8_t surround_selection;

    uint8_t echo_index;
    uint8_t mic1_index;
    uint8_t mic2_index;

    uint8_t speaker_front;
    uint8_t speaker_center;
    uint8_t speaker_rear;
    uint8_t speaker_subwoofer;

    uint8_t external_input_selector;
    uint8_t spdif_hardware_mode;
};

void sphe_control_get_status(struct sphe_audio_status *out);

void sphe_control_set_master_volume(uint8_t level);
void sphe_control_set_master_mute(bool muted);

bool sphe_control_set_surround(enum sphe_surround_mode mode);
bool sphe_control_set_eq_preset(enum sphe_eq_selection selection);
void sphe_control_set_user_eq7(const uint8_t coefficients[7]);

bool sphe_control_set_speaker_state(
    enum sphe_speaker_channel channel,
    uint8_t state
);
void sphe_control_set_subwoofer(bool enabled);
bool sphe_control_set_speaker_delay(
    enum sphe_speaker_channel channel,
    int16_t delay
);

bool sphe_control_set_echo(uint8_t index);
bool sphe_control_set_mic1(uint8_t index);
bool sphe_control_set_mic2(uint8_t index);

void sphe_control_set_spdif_output(enum sphe_spdif_output_option option);
bool sphe_control_set_downsample(enum sphe_downsample_mode mode);
void sphe_control_set_downmix(enum sphe_downmix_option option);
void sphe_control_set_gm5(enum sphe_gm5_option option);
void sphe_control_apply_dynamic_range(void);

#endif
