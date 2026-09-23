#include "sphe_audio_control.h"

#include <stddef.h>

#define REG8(addr)  (*(volatile uint8_t *)(uintptr_t)(addr))
#define REG16(addr) (*(volatile uint16_t *)(uintptr_t)(addr))
#define REG32(addr) (*(volatile uint32_t *)(uintptr_t)(addr))

/*
 * Recovered AP1 live-state addresses.  These are target-specific to the
 * preserved 02R-D-02 image and intentionally bypass the legacy DVD/UI layer.
 */
#define SPHE_STATE_EXTERNAL_MODE         0x80002C2BU
#define SPHE_STATE_EXTERNAL_MODE_PREV    0x80002C2CU

#define SPHE_STATE_DECODER              0x80003198U
#define SPHE_STATE_MASTER_MUTE          0x800032B5U
#define SPHE_STATE_SOURCE_MEDIA         0x800032A5U
#define SPHE_STATE_EXTERNAL_INPUT       0x800032FAU
#define SPHE_STATE_SPEAKER_SUB          0x800032D6U
#define SPHE_STATE_SPEAKER_CENTER       0x800032DCU
#define SPHE_STATE_SPEAKER_REAR         0x8000330EU
#define SPHE_STATE_MIC2                 0x80003324U
#define SPHE_STATE_SPEAKER_FRONT        0x80003327U
#define SPHE_STATE_MIC1                 0x80003297U
#define SPHE_STATE_MASTER_VOLUME        0x80003332U
#define SPHE_STATE_ECHO                 0x8000333AU
#define SPHE_STATE_DOWNSAMPLE_MASK      0x80003244U
#define SPHE_STATE_SPDIF_HW_MODE        0x800042B3U

#define SPHE_STATE_SURROUND_SELECTION   0x80002B0CU
#define SPHE_STATE_EQ_SELECTION         0x80002B0DU
#define SPHE_STATE_USER_EQ7             0x80002B10U

#define SPHE_STATE_ECHO_SLOT            0x8000681DU
#define SPHE_STATE_MIC1_SLOT            0x8000681EU

typedef void (*stock_void_fn)(void);

/*
 * These two stock actions mirror the current live indices into their
 * associated control-state slots before applying them.
 */
static inline void stock_apply_current_echo(void)
{
    ((stock_void_fn)(uintptr_t)0x8077CA14U)();
}

static inline void stock_apply_current_mic1(void)
{
    ((stock_void_fn)(uintptr_t)0x8077CA44U)();
}

static inline void stock_apply_external_mode(void)
{
    ((stock_void_fn)(uintptr_t)0x806FED88U)();
}

static inline void stock_save_external_mode(void)
{
    ((stock_void_fn)(uintptr_t)0x8071DB1CU)();
}

static inline void stock_prepare_external_transition(void)
{
    ((stock_void_fn)(uintptr_t)0x806FABA0U)();
}


bool sphe_control_set_external_mode(enum sphe_external_mode_code mode)
{
    const uint8_t next = (uint8_t)mode;
    const uint8_t previous = REG8(SPHE_STATE_EXTERNAL_MODE_PREV);

    if (next > 3U) {
        return false;
    }

    REG8(SPHE_STATE_EXTERNAL_MODE) = next;
    stock_apply_external_mode();
    stock_save_external_mode();

    if (previous == next) {
        return true;
    }

    /*
     * Stock behavior performs the mute/delay transition whenever AUX is one
     * side of the change: entering mode 3 or leaving previous mode 3.
     */
    if (next == 3U || previous == 3U) {
        stock_prepare_external_transition();
    }

    if (next == 3U) {
        REG8(SPHE_STATE_EXTERNAL_INPUT) = 1U;
        REG8(SPHE_STATE_SOURCE_MEDIA) = 0x0BU;
    } else {
        REG8(SPHE_STATE_EXTERNAL_INPUT) = 2U;
        REG8(SPHE_STATE_SOURCE_MEDIA) = 0x0DU;
    }

    REG8(SPHE_STATE_EXTERNAL_MODE_PREV) = next;
    return true;
}


bool sphe_control_set_tuner_spdif(bool spdif)
{
    const uint8_t desired_selector = spdif ? 2U : 0U;
    const uint8_t desired_state = spdif ? 0x0DU : 0x02U;

    /*
     * Mode 3 is the confirmed AUX route.  Do not silently choose one of the
     * still-unlabelled external hardware modes 0..2 on behalf of the caller.
     */
    if (REG8(SPHE_STATE_EXTERNAL_MODE) == 3U) {
        return false;
    }

    if (REG8(SPHE_STATE_EXTERNAL_INPUT) == desired_selector) {
        REG8(SPHE_STATE_SOURCE_MEDIA) = desired_state;
        return true;
    }

    stock_prepare_external_transition();
    REG8(SPHE_STATE_EXTERNAL_INPUT) = desired_selector;
    REG8(SPHE_STATE_SOURCE_MEDIA) = desired_state;
    return true;
}

void sphe_control_get_status(struct sphe_audio_status *out)
{
    if (out == NULL) {
        return;
    }

    out->decoder_state = REG32(SPHE_STATE_DECODER);
    out->downsample_mask = REG16(SPHE_STATE_DOWNSAMPLE_MASK);

    out->master_volume = REG8(SPHE_STATE_MASTER_VOLUME);
    out->master_muted = REG8(SPHE_STATE_MASTER_MUTE);

    out->eq_selection = REG8(SPHE_STATE_EQ_SELECTION);
    out->surround_selection = REG8(SPHE_STATE_SURROUND_SELECTION);

    out->echo_index = REG8(SPHE_STATE_ECHO);
    out->mic1_index = REG8(SPHE_STATE_MIC1);
    out->mic2_index = REG8(SPHE_STATE_MIC2);

    out->speaker_front = REG8(SPHE_STATE_SPEAKER_FRONT);
    out->speaker_center = REG8(SPHE_STATE_SPEAKER_CENTER);
    out->speaker_rear = REG8(SPHE_STATE_SPEAKER_REAR);
    out->speaker_subwoofer = REG8(SPHE_STATE_SPEAKER_SUB);

    out->external_mode = REG8(SPHE_STATE_EXTERNAL_MODE);
    out->external_input_selector = REG8(SPHE_STATE_EXTERNAL_INPUT);
    out->source_media_state = REG8(SPHE_STATE_SOURCE_MEDIA);
    out->spdif_hardware_mode = REG8(SPHE_STATE_SPDIF_HW_MODE);
}

void sphe_control_set_master_volume(uint8_t level)
{
    REG8(SPHE_STATE_MASTER_VOLUME) = level;

    /*
     * Stock behavior applies effective level zero while muted.  Updating the
     * saved live level here lets the stock unmute route restore the new value.
     */
    if (REG8(SPHE_STATE_MASTER_MUTE) == 0U) {
        sphe_set_master_volume(level);
    }
}

void sphe_control_set_master_mute(bool muted)
{
    const bool current = REG8(SPHE_STATE_MASTER_MUTE) != 0U;
    if (current != muted) {
        sphe_toggle_master_mute();
    }
}

bool sphe_control_set_surround(enum sphe_surround_mode mode)
{
    if ((unsigned)mode > (unsigned)SPHE_SURROUND_LIVE) {
        return false;
    }

    REG8(SPHE_STATE_SURROUND_SELECTION) = (uint8_t)mode + 2U;
    sphe_set_surround_index((uint8_t)mode);
    return true;
}

bool sphe_control_set_eq_preset(enum sphe_eq_selection selection)
{
    if ((unsigned)selection < (unsigned)SPHE_EQ_STANDARD ||
        (unsigned)selection > (unsigned)SPHE_EQ_POP) {
        return false;
    }

    /*
     * Reapply the pair, not only the preset helper: coefficient upload can
     * locally clear surround and the stock paired action restores it.
     */
    REG8(SPHE_STATE_EQ_SELECTION) = (uint8_t)selection;
    sphe_reapply_eq_and_surround();
    return true;
}

void sphe_control_set_user_eq7(const uint8_t coefficients[7])
{
    volatile uint8_t *dst =
        (volatile uint8_t *)(uintptr_t)SPHE_STATE_USER_EQ7;

    if (coefficients == NULL) {
        return;
    }

    for (unsigned i = 0; i < 7U; ++i) {
        dst[i] = coefficients[i];
    }

    REG8(SPHE_STATE_EQ_SELECTION) = SPHE_EQ_USER;
    sphe_reapply_eq_and_surround();
}

bool sphe_control_set_speaker_state(
    enum sphe_speaker_channel channel,
    uint8_t state
)
{
    switch (channel) {
    case SPHE_SPEAKER_FRONT:
        if (state > 1U) {
            return false;
        }
        break;

    case SPHE_SPEAKER_CENTER:
    case SPHE_SPEAKER_REAR:
        if (state > 2U) {
            return false;
        }
        break;

    case SPHE_SPEAKER_SUBWOOFER:
        if (state > 1U) {
            return false;
        }
        sphe_control_set_subwoofer(state != 0U);
        return true;

    default:
        return false;
    }

    sphe_set_speaker_channel_state(channel, state);
    sphe_reapply_speaker_topology();
    return true;
}

void sphe_control_set_subwoofer(bool enabled)
{
    REG8(SPHE_STATE_SPEAKER_SUB) = enabled ? 1U : 0U;
    sphe_apply_subwoofer_state(enabled ? 1U : 0U);
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

    sphe_set_speaker_delay((uint8_t)channel, (uint16_t)delay);
    return true;
}

bool sphe_control_set_echo(uint8_t index)
{
    if (index > 8U) {
        return false;
    }

    REG8(SPHE_STATE_ECHO) = index;
    REG8(SPHE_STATE_ECHO_SLOT) = index + 2U;
    stock_apply_current_echo();
    return true;
}

bool sphe_control_set_mic1(uint8_t index)
{
    if (index > 8U) {
        return false;
    }

    REG8(SPHE_STATE_MIC1) = index;
    REG8(SPHE_STATE_MIC1_SLOT) = index + 2U;
    stock_apply_current_mic1();
    return true;
}

bool sphe_control_set_mic2(uint8_t index)
{
    if (index > 8U) {
        return false;
    }

    /*
     * MIC2 has a confirmed separate live index but no recovered persistence
     * route in the loaded code.  Keep this deliberately live-only.
     */
    REG8(SPHE_STATE_MIC2) = index;
    sphe_set_mic2_selection(index);
    return true;
}

void sphe_control_set_spdif_output(enum sphe_spdif_output_option option)
{
    sphe_apply_spdif_output_option(option);
}

bool sphe_control_set_downsample(enum sphe_downsample_mode mode)
{
    if ((unsigned)mode > (unsigned)SPHE_DOWNSAMPLE_192K) {
        return false;
    }

    sphe_set_downsample_mode((uint8_t)mode);
    return true;
}

void sphe_control_set_downmix(enum sphe_downmix_option option)
{
    sphe_apply_downmix_option(option);
}

void sphe_control_set_gm5(enum sphe_gm5_option option)
{
    sphe_apply_gm5_option(option);
}

void sphe_control_apply_dynamic_range(void)
{
    sphe_apply_dynamic_range();
}
