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

enum sphe_external_mode_code {
    SPHE_EXTERNAL_MODE_0 = 0,
    SPHE_EXTERNAL_MODE_1 = 1,
    SPHE_EXTERNAL_MODE_2 = 2,
    SPHE_EXTERNAL_MODE_AUX = 3,
};

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

    uint8_t external_mode;
    uint8_t external_input_selector;
    uint8_t source_media_state;
    uint8_t spdif_hardware_mode;
};

void sphe_control_get_status(struct sphe_audio_status *out);

bool sphe_control_set_external_mode(enum sphe_external_mode_code mode);

/*
 * Explicit TUNER <-> SPDIF IN subsource selection.
 * Returns false while external mode 3/AUX is active; choose mode 0..2 first.
 */
bool sphe_control_set_tuner_spdif(bool spdif);

bool sphe_control_set_master_volume(uint8_t level);
void sphe_control_set_master_mute(bool muted);

bool sphe_control_set_surround(enum sphe_surround_mode mode);
bool sphe_control_set_eq_preset(enum sphe_eq_selection selection);
bool sphe_control_set_user_eq7(const uint8_t coefficients[7]);

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

bool sphe_control_set_spdif_output(enum sphe_spdif_output_option option);
bool sphe_control_set_downsample(enum sphe_downsample_mode mode);
bool sphe_control_set_downmix(enum sphe_downmix_option option);
bool sphe_control_set_gm5(enum sphe_gm5_option option);
void sphe_control_apply_dynamic_range(void);

#endif
