#include "sphe_audio_control.h"

#include <stddef.h>

#define REG8(addr)  (*(volatile uint8_t *)(uintptr_t)(addr))
#define REG16(addr) (*(volatile uint16_t *)(uintptr_t)(addr))
#define REG32(addr) (*(volatile uint32_t *)(uintptr_t)(addr))

/* Recovered AP1 state addresses and semantic values come from
 * sphe_audio_contract.h.  Keep this file behavior-only. */
bool sphe_control_set_external_mode(enum sphe_external_mode_code mode)
{
    const uint8_t next = (uint8_t)mode;
    const uint8_t previous = REG8(SPHE_STATE_PREVIOUS_EXTERNAL_INPUT_MODE_CODE);

    if (next >= (uint8_t)SPHE_EXTERNAL_MODE_COUNT) {
        return false;
    }

    REG8(SPHE_STATE_EXTERNAL_INPUT_MODE_CODE) = next;
    sphe_apply_external_input_hardware_mode();
    sphe_write_external_input_mode_code();

    if (previous == next) {
        return true;
    }

    /*
     * Stock behavior performs the mute/delay transition whenever AUX is one
     * side of the change: entering mode 3 or leaving previous mode 3.
     */
    if (next == (uint8_t)SPHE_EXTERNAL_MODE_AUX ||
        previous == (uint8_t)SPHE_EXTERNAL_MODE_AUX) {
        sphe_prepare_external_input_transition();
    }

    if (next == (uint8_t)SPHE_EXTERNAL_MODE_AUX) {
        REG8(SPHE_STATE_EXTERNAL_INPUT_SELECTOR) = SPHE_EXTERNAL_INPUT_AUX;
        REG8(SPHE_STATE_SOURCE_MEDIA_STATE) = SPHE_SOURCE_MEDIA_STATE_AUX;
    } else {
        REG8(SPHE_STATE_EXTERNAL_INPUT_SELECTOR) = SPHE_EXTERNAL_INPUT_SPDIF;
        REG8(SPHE_STATE_SOURCE_MEDIA_STATE) = SPHE_SOURCE_MEDIA_STATE_SPDIF_IN;
    }

    REG8(SPHE_STATE_PREVIOUS_EXTERNAL_INPUT_MODE_CODE) = next;
    return true;
}


bool sphe_control_set_tuner_spdif(bool spdif)
{
    const uint8_t desired_selector = spdif ? SPHE_EXTERNAL_INPUT_SPDIF : SPHE_EXTERNAL_INPUT_TUNER;
    const uint8_t desired_state = spdif ? SPHE_SOURCE_MEDIA_STATE_SPDIF_IN : SPHE_SOURCE_MEDIA_STATE_TUNER_ROUTE;

    /*
     * Mode 3 is the confirmed AUX route.  Do not silently choose one of the
     * still-unlabelled external hardware modes 0..2 on behalf of the caller.
     */
    if (REG8(SPHE_STATE_EXTERNAL_INPUT_MODE_CODE) == (uint8_t)SPHE_EXTERNAL_MODE_AUX) {
        return false;
    }

    if (REG8(SPHE_STATE_EXTERNAL_INPUT_SELECTOR) == desired_selector) {
        REG8(SPHE_STATE_SOURCE_MEDIA_STATE) = desired_state;
        return true;
    }

    sphe_prepare_external_input_transition();
    REG8(SPHE_STATE_EXTERNAL_INPUT_SELECTOR) = desired_selector;
    REG8(SPHE_STATE_SOURCE_MEDIA_STATE) = desired_state;
    return true;
}

void sphe_control_get_status(struct sphe_audio_status *out)
{
    if (out == NULL) {
        return;
    }

    out->decoder_state = REG32(SPHE_STATE_AUDIO_DECODER_STATE);
    out->downsample_mask = REG16(SPHE_STATE_DOWNSAMPLE_STATE_MASK);

    out->master_volume = REG8(SPHE_STATE_MASTER_VOLUME_LEVEL);
    out->master_muted = REG8(SPHE_STATE_MASTER_MUTE_FLAG);

    out->eq_selection = REG8(SPHE_STATE_EQ_PRESET_INDEX);
    out->surround_selection = REG8(SPHE_STATE_SURROUND_SELECTION);

    out->echo_index = REG8(SPHE_STATE_ECHO_PROFILE_INDEX);
    out->mic1_index = REG8(SPHE_STATE_MIC1_LEVEL_INDEX);
    out->mic2_index = REG8(SPHE_STATE_MIC2_LEVEL_INDEX);

    out->speaker_front = REG8(SPHE_STATE_SPEAKER_FRONT_STATE);
    out->speaker_center = REG8(SPHE_STATE_SPEAKER_CENTER_STATE);
    out->speaker_rear = REG8(SPHE_STATE_SPEAKER_REAR_STATE);
    out->speaker_subwoofer = REG8(SPHE_STATE_SPEAKER_SUBWOOFER_STATE);

    out->external_mode = REG8(SPHE_STATE_EXTERNAL_INPUT_MODE_CODE);
    out->external_input_selector = REG8(SPHE_STATE_EXTERNAL_INPUT_SELECTOR);
    out->source_media_state = REG8(SPHE_STATE_SOURCE_MEDIA_STATE);
    out->spdif_hardware_mode = REG8(SPHE_STATE_SPDIF_HARDWARE_MODE);
}

bool sphe_control_set_master_volume(uint8_t level)
{
    if (level > SPHE_MASTER_VOLUME_MAX) {
        return false;
    }

    REG8(SPHE_STATE_MASTER_VOLUME_LEVEL) = level;

    /*
     * Stock behavior applies effective level zero while muted.  Updating the
     * saved live level here lets the stock unmute route restore the new value.
     */
    if (REG8(SPHE_STATE_MASTER_MUTE_FLAG) == 0U) {
        sphe_set_master_volume_level(level);
    }
    return true;
}

void sphe_control_set_master_mute(bool muted)
{
    const bool current = REG8(SPHE_STATE_MASTER_MUTE_FLAG) != 0U;
    if (current != muted) {
        sphe_toggle_master_mute();
    }
}

bool sphe_control_set_surround(enum sphe_surround_mode mode)
{
    if ((unsigned)mode > (unsigned)SPHE_SURROUND_LIVE) {
        return false;
    }

    REG8(SPHE_STATE_SURROUND_SELECTION) = (uint8_t)mode + SPHE_CONTROL_SELECTION_BIAS;
    sphe_apply_surround_index((uint8_t)mode);
    return true;
}

bool sphe_control_set_eq_selection(enum sphe_eq_selection selection)
{
    if ((unsigned)selection < (unsigned)SPHE_EQ_STANDARD ||
        (unsigned)selection > (unsigned)SPHE_EQ_USER) {
        return false;
    }

    /*
     * Reapply the pair, not only the preset helper: coefficient upload can
     * locally clear surround and the stock paired action restores it.
     * USER selects the already stored seven-band vector without replacing it.
     */
    REG8(SPHE_STATE_EQ_PRESET_INDEX) = (uint8_t)selection;
    sphe_apply_current_seven_band_eq_preset();
    return true;
}

bool sphe_control_set_eq_preset(enum sphe_eq_selection selection)
{
    if (selection == SPHE_EQ_USER) {
        return false;
    }
    return sphe_control_set_eq_selection(selection);
}

bool sphe_control_set_user_eq7(const uint8_t coefficients[SPHE_EQ_BAND_COUNT])
{
    volatile uint8_t *dst =
        (volatile uint8_t *)(uintptr_t)SPHE_STATE_USER_EQ7_CURVE;

    if (coefficients == NULL) {
        return false;
    }

    for (unsigned i = 0; i < SPHE_EQ_BAND_COUNT; ++i) {
        dst[i] = coefficients[i];
    }

    REG8(SPHE_STATE_EQ_PRESET_INDEX) = SPHE_EQ_USER;
    sphe_apply_current_seven_band_eq_preset();
    return true;
}

bool sphe_control_set_speaker_state(
    enum sphe_speaker_channel channel,
    uint8_t state
)
{
    switch (channel) {
    case SPHE_SPEAKER_FRONT:
        if (state > (uint8_t)SPHE_SPEAKER_SMALL) {
            return false;
        }
        break;

    case SPHE_SPEAKER_CENTER:
    case SPHE_SPEAKER_REAR:
        if (state > (uint8_t)SPHE_SPEAKER_OFF) {
            return false;
        }
        break;

    case SPHE_SPEAKER_SUBWOOFER:
        if (state > (uint8_t)SPHE_SPEAKER_SMALL) {
            return false;
        }
        sphe_control_set_subwoofer(state != 0U);
        return true;

    default:
        return false;
    }

    sphe_set_speaker_channel_state(channel, state);
    sphe_apply_speaker_configuration();
    return true;
}

void sphe_control_set_subwoofer(bool enabled)
{
    REG8(SPHE_STATE_SPEAKER_SUBWOOFER_STATE) = enabled ? SPHE_SUBWOOFER_STATE_ON : SPHE_SUBWOOFER_STATE_OFF;
    sphe_apply_subwoofer_state(enabled ? SPHE_SUBWOOFER_STATE_ON : SPHE_SUBWOOFER_STATE_OFF);
}

bool sphe_control_set_speaker_delay(
    enum sphe_speaker_channel channel,
    int16_t delay
)
{
    if (channel != SPHE_SPEAKER_CENTER &&
        channel != SPHE_SPEAKER_REAR) {
        return false;
    }

    sphe_apply_speaker_delay_parameter(channel, (uint16_t)delay);
    return true;
}

bool sphe_control_set_echo(uint8_t index)
{
    if (index > SPHE_EFFECT_INDEX_MAX) {
        return false;
    }

    REG8(SPHE_STATE_ECHO_PROFILE_INDEX) = index;
    REG8(SPHE_STATE_ECHO_CONTROL_SELECTION_SLOT) = index + SPHE_CONTROL_SELECTION_BIAS;
    sphe_reapply_current_echo_selection();
    return true;
}

bool sphe_control_set_mic1(uint8_t index)
{
    if (index > SPHE_EFFECT_INDEX_MAX) {
        return false;
    }

    REG8(SPHE_STATE_MIC1_LEVEL_INDEX) = index;
    REG8(SPHE_STATE_MIC1_CONTROL_SELECTION_SLOT) = index + SPHE_CONTROL_SELECTION_BIAS;
    sphe_reapply_current_mic1_selection();
    return true;
}

bool sphe_control_set_mic2(uint8_t index)
{
    if (index > SPHE_EFFECT_INDEX_MAX) {
        return false;
    }

    /*
     * MIC2 has a confirmed separate live index but no recovered persistence
     * route in the loaded code.  Keep this deliberately live-only.
     */
    REG8(SPHE_STATE_MIC2_LEVEL_INDEX) = index;
    sphe_apply_mic2_selection(index);
    return true;
}

bool sphe_control_set_spdif_output(enum sphe_spdif_output_option option)
{
    if (option != SPHE_SPDIF_OFF &&
        option != SPHE_SPDIF_RAW &&
        option != SPHE_SPDIF_PCM) {
        return false;
    }

    sphe_apply_spdif_output_option(option);
    return true;
}

bool sphe_control_set_downsample(enum sphe_downsample_mode mode)
{
    if ((unsigned)mode > (unsigned)SPHE_DOWNSAMPLE_192K) {
        return false;
    }

    sphe_apply_downsample_rate_mode(mode);
    return true;
}

bool sphe_control_set_downmix(enum sphe_downmix_option option)
{
    if (option != SPHE_DOWNMIX_STEREO &&
        option != SPHE_DOWNMIX_OFF &&
        option != SPHE_DOWNMIX_LT_RT &&
        option != SPHE_DOWNMIX_VSS) {
        return false;
    }

    sphe_apply_downmix_option(option);
    return true;
}

bool sphe_control_set_gm5(enum sphe_gm5_option option)
{
    if (option != SPHE_GM5_OFF &&
        option != SPHE_GM5_MODE1 &&
        option != SPHE_GM5_MODE2) {
        return false;
    }

    sphe_handle_gm5_control_option(option);
    return true;
}

void sphe_control_apply_dynamic_range(void)
{
    sphe_apply_dynamic_range_control();
}
