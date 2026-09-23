#ifndef SPHE_AUDIO_API_H
#define SPHE_AUDIO_API_H

#include <stdint.h>

/*
 * Recovered stock audio actions for the preserved SPHE8202R 02R-D-02 image.
 *
 * This header intentionally does not own AP1 live state.  Stateful behavior
 * belongs in sphe_audio_control.c.  These wrappers expose only confirmed stock
 * actions that can be called from freestanding code running inside the
 * already-initialized AP1 runtime.
 */

typedef int (*sphe_audio_dispatch_fn)(
    uint32_t action,
    uint32_t value,
    uint32_t aux
);

typedef void (*sphe_u8_fn)(uint32_t);
typedef void (*sphe_u8_u8_fn)(uint32_t, uint32_t);
typedef void (*sphe_u8_u16_fn)(uint32_t, uint32_t);
typedef void (*sphe_ptr_fn)(const void *);
typedef void (*sphe_void_fn)(void);

enum sphe_audio_action {
    SPHE_AUDIO_ACTION_PIPELINE_MODE     = 0x00,
    SPHE_AUDIO_ACTION_OUTPUT_MODE       = 0x01,
    SPHE_AUDIO_ACTION_MASTER_VOLUME     = 0x02,
    SPHE_AUDIO_ACTION_KEY               = 0x03,
    SPHE_AUDIO_ACTION_ECHO              = 0x04,
    SPHE_AUDIO_ACTION_SURROUND          = 0x05,
    SPHE_AUDIO_ACTION_SUBWOOFER         = 0x06,
    SPHE_AUDIO_ACTION_SPDIF_HW          = 0x07,
    SPHE_AUDIO_ACTION_EQ_PROCESSING     = 0x08,
    SPHE_AUDIO_ACTION_DECODER_STATE     = 0x09,
    SPHE_AUDIO_ACTION_MIC1              = 0x0A,
    SPHE_AUDIO_ACTION_SPEAKER_DELAY     = 0x0B,
    SPHE_AUDIO_ACTION_GM5               = 0x0E,
    SPHE_AUDIO_ACTION_MIC2_TRIGGER      = 0x16,
    SPHE_AUDIO_ACTION_SPEAKER_TOPOLOGY  = 0x17,
};

enum sphe_spdif_output_option {
    SPHE_SPDIF_OFF = 0x12,
    SPHE_SPDIF_RAW = 0x75,
    SPHE_SPDIF_PCM = 0x77,
};

enum sphe_downsample_mode {
    SPHE_DOWNSAMPLE_48K  = 0,
    SPHE_DOWNSAMPLE_96K  = 1,
    SPHE_DOWNSAMPLE_192K = 2,
};

enum sphe_downmix_option {
    SPHE_DOWNMIX_STEREO = 0x31,
    SPHE_DOWNMIX_OFF    = 0x7B,
    SPHE_DOWNMIX_LT_RT  = 0xF7,
    SPHE_DOWNMIX_VSS    = 0xF8,
};

enum sphe_gm5_option {
    SPHE_GM5_OFF   = 0x7B,
    SPHE_GM5_MODE1 = 0x9F,
    SPHE_GM5_MODE2 = 0xA0,
};

enum sphe_surround_mode {
    SPHE_SURROUND_OFF     = 0,
    SPHE_SURROUND_CONCERT = 1,
    SPHE_SURROUND_CHURCH  = 2,
    SPHE_SURROUND_PASSIVE = 3,
    SPHE_SURROUND_WIDE    = 4,
    SPHE_SURROUND_LIVE    = 5,
};

enum sphe_eq_selection {
    SPHE_EQ_STANDARD = 2,
    SPHE_EQ_CLASSIC  = 3,
    SPHE_EQ_ROCK     = 4,
    SPHE_EQ_JAZZ     = 5,
    SPHE_EQ_POP      = 6,
    SPHE_EQ_USER     = 7,
};

enum sphe_speaker_channel {
    SPHE_SPEAKER_FRONT = 0,
    SPHE_SPEAKER_CENTER = 1,
    SPHE_SPEAKER_REAR = 2,
    SPHE_SPEAKER_SUBWOOFER = 3,
};

enum sphe_speaker_state {
    SPHE_SPEAKER_LARGE = 0,
    SPHE_SPEAKER_SMALL = 1,
    SPHE_SPEAKER_OFF = 2,
};

static inline int
sphe_audio_dispatch(uint32_t action, uint32_t value, uint32_t aux)
{
    return ((sphe_audio_dispatch_fn)(uintptr_t)0x806FFD1CU)(
        action, value, aux
    );
}

/* Primitive stock wrappers. */

static inline void
sphe_apply_master_volume_level(uint8_t level)
{
    ((sphe_u8_fn)(uintptr_t)0x8070129CU)(level);
}

static inline void
sphe_toggle_master_mute(void)
{
    ((sphe_void_fn)(uintptr_t)0x806F9D18U)();
}

static inline void
sphe_apply_spdif_hardware_mode(uint8_t mode)
{
    ((sphe_u8_fn)(uintptr_t)0x80702BA0U)(mode);
}

static inline void
sphe_apply_decoder_output_mode(uint8_t mode, uint16_t aux)
{
    ((sphe_u8_u16_fn)(uintptr_t)0x80702BD0U)(mode, aux);
}

static inline void
sphe_apply_speaker_delay(uint8_t channel, uint16_t delay)
{
    ((sphe_u8_u16_fn)(uintptr_t)0x80702C60U)(channel, delay);
}

static inline void
sphe_apply_echo_profile(uint8_t index)
{
    ((sphe_u8_fn)(uintptr_t)0x80702C8CU)(index);
}

static inline void
sphe_apply_mic1_level(uint8_t index)
{
    ((sphe_u8_fn)(uintptr_t)0x80702B48U)(index);
}

static inline void
sphe_apply_mic2_selection(uint8_t index)
{
    ((sphe_u8_fn)(uintptr_t)0x80702B74U)(index);
}

static inline void
sphe_apply_downsample_mode(uint8_t mode)
{
    ((sphe_u8_fn)(uintptr_t)0x80701B80U)(mode);
}

static inline void
sphe_reapply_speaker_topology(void)
{
    ((sphe_void_fn)(uintptr_t)0x8070106CU)();
}

static inline void
sphe_apply_external_input_mode_code(void)
{
    ((sphe_void_fn)(uintptr_t)0x806FED88U)();
}

static inline void
sphe_save_external_input_mode_code(void)
{
    ((sphe_void_fn)(uintptr_t)0x8071DB1CU)();
}

static inline void
sphe_prepare_external_input_transition(void)
{
    ((sphe_void_fn)(uintptr_t)0x806FABA0U)();
}

static inline void
sphe_reapply_current_echo(void)
{
    ((sphe_void_fn)(uintptr_t)0x8077CA14U)();
}

static inline void
sphe_reapply_current_mic1(void)
{
    ((sphe_void_fn)(uintptr_t)0x8077CA44U)();
}

/* Higher-level stock behavior contracts. */

static inline void
sphe_apply_spdif_output_option(enum sphe_spdif_output_option option)
{
    ((sphe_u8_fn)(uintptr_t)0x807759E0U)((uint8_t)option);
}

static inline void
sphe_apply_downmix_option(enum sphe_downmix_option option)
{
    ((sphe_u8_fn)(uintptr_t)0x80775800U)((uint8_t)option);
}

static inline void
sphe_apply_gm5_option(enum sphe_gm5_option option)
{
    ((sphe_u8_fn)(uintptr_t)0x80775F3CU)((uint8_t)option);
}

static inline void
sphe_apply_dynamic_range(void)
{
    ((sphe_void_fn)(uintptr_t)0x807769B8U)();
}

static inline void
sphe_apply_eq_preset(enum sphe_eq_selection selection)
{
    ((sphe_u8_fn)(uintptr_t)0x806E8960U)((uint8_t)selection);
}

static inline void
sphe_apply_user_eq7(const uint8_t coefficients[7])
{
    ((sphe_ptr_fn)(uintptr_t)0x806E8ED0U)(coefficients);
}

static inline void
sphe_reapply_eq_and_surround(void)
{
    ((sphe_void_fn)(uintptr_t)0x806E89E4U)();
}

static inline void
sphe_set_speaker_channel_state(
    enum sphe_speaker_channel channel,
    uint8_t state
)
{
    ((sphe_u8_u8_fn)(uintptr_t)0x80701168U)(
        (uint8_t)channel,
        state
    );
}

static inline void
sphe_apply_subwoofer_state(uint8_t enabled)
{
    ((sphe_u8_fn)(uintptr_t)0x80701268U)(enabled ? 1U : 0U);
}

/* Stateless command-family wrappers. */

static inline int
sphe_apply_surround_index(uint8_t index)
{
    return sphe_audio_dispatch(
        SPHE_AUDIO_ACTION_SURROUND,
        index,
        0
    );
}

static inline int
sphe_apply_eq_processing_mode(uint8_t mode)
{
    return sphe_audio_dispatch(
        SPHE_AUDIO_ACTION_EQ_PROCESSING,
        mode,
        0
    );
}

static inline int
sphe_apply_subwoofer_hardware_state(uint8_t state)
{
    return sphe_audio_dispatch(
        SPHE_AUDIO_ACTION_SUBWOOFER,
        state,
        0
    );
}

#endif
