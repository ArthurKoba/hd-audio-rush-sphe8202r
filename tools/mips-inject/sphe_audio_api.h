#ifndef SPHE_AUDIO_API_H
#define SPHE_AUDIO_API_H

#include <stdint.h>

#include "sphe_audio_contract.h"

/*
 * Recovered stock audio actions for the preserved SPHE8202R 02R-D-02 image.
 *
 * This header intentionally does not own AP1 live state.  Stateful behavior
 * belongs in sphe_audio_control.c.  These wrappers expose only confirmed stock
 * actions that can be called from freestanding code running inside the
 * already-initialized AP1 runtime.
 */

typedef int (*sphe_audio_dispatch_fn)(
    enum sphe_audio_action action,
    uint32_t value,
    uint32_t aux
);

typedef void (*sphe_u8_fn)(uint32_t);
typedef void (*sphe_u8_u8_fn)(uint32_t, uint32_t);
typedef void (*sphe_u8_u16_fn)(uint32_t, uint32_t);
typedef void (*sphe_ptr_fn)(const void *);
typedef void (*sphe_void_fn)(void);

static inline int
sphe_audio_dispatch(enum sphe_audio_action action, uint32_t value, uint32_t aux)
{
    return ((sphe_audio_dispatch_fn)(uintptr_t)SPHE_ADDR_DISPATCH_AUDIO_HARDWARE_ACTION)(
        action, value, aux
    );
}

/* Primitive stock wrappers. */

static inline void
sphe_apply_master_volume_level(uint8_t level)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_MASTER_VOLUME_LEVEL)(level);
}

static inline void
sphe_toggle_master_mute(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_TOGGLE_MASTER_MUTE)();
}

static inline void
sphe_apply_spdif_hardware_mode(uint8_t mode)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_SPDIF_HARDWARE_MODE)(mode);
}

static inline void
sphe_apply_decoder_output_mode(uint8_t mode, uint16_t aux)
{
    ((sphe_u8_u16_fn)(uintptr_t)SPHE_ADDR_APPLY_DECODER_OUTPUT_MODE)(mode, aux);
}

static inline void
sphe_apply_speaker_delay(enum sphe_speaker_channel channel, uint16_t delay)
{
    ((sphe_u8_u16_fn)(uintptr_t)SPHE_ADDR_APPLY_SPEAKER_DELAY)(channel, delay);
}

static inline void
sphe_apply_echo_profile(uint8_t index)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_ECHO_PROFILE)(index);
}

static inline void
sphe_apply_mic1_level(uint8_t index)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_MIC1_LEVEL)(index);
}

static inline void
sphe_apply_mic2_selection(uint8_t index)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_MIC2_SELECTION)(index);
}

static inline void
sphe_apply_downsample_mode(enum sphe_downsample_mode mode)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_DOWNSAMPLE_MODE)(mode);
}

static inline void
sphe_reapply_speaker_topology(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_REAPPLY_SPEAKER_TOPOLOGY)();
}

static inline void
sphe_apply_external_input_mode_code(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_APPLY_EXTERNAL_INPUT_MODE_CODE)();
}

static inline void
sphe_save_external_input_mode_code(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_SAVE_EXTERNAL_INPUT_MODE_CODE)();
}

static inline void
sphe_prepare_external_input_transition(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_PREPARE_EXTERNAL_INPUT_TRANSITION)();
}

static inline void
sphe_reapply_current_echo(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_REAPPLY_CURRENT_ECHO)();
}

static inline void
sphe_reapply_current_mic1(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_REAPPLY_CURRENT_MIC1)();
}

/* Higher-level stock behavior contracts. */

static inline void
sphe_apply_spdif_output_option(enum sphe_spdif_output_option option)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_SPDIF_OUTPUT_OPTION)((uint8_t)option);
}

static inline void
sphe_apply_downmix_option(enum sphe_downmix_option option)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_DOWNMIX_OPTION)((uint8_t)option);
}

static inline void
sphe_apply_gm5_option(enum sphe_gm5_option option)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_GM5_OPTION)((uint8_t)option);
}

static inline void
sphe_apply_dynamic_range(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_APPLY_DYNAMIC_RANGE)();
}

static inline void
sphe_apply_eq_preset(enum sphe_eq_selection selection)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_EQ_PRESET)((uint8_t)selection);
}

static inline void
sphe_apply_user_eq7(const uint8_t coefficients[7])
{
    ((sphe_ptr_fn)(uintptr_t)SPHE_ADDR_APPLY_USER_EQ7)(coefficients);
}

static inline void
sphe_reapply_eq_and_surround(void)
{
    ((sphe_void_fn)(uintptr_t)SPHE_ADDR_REAPPLY_EQ_AND_SURROUND)();
}

static inline void
sphe_set_speaker_channel_state(
    enum sphe_speaker_channel channel,
    enum sphe_speaker_state state
)
{
    ((sphe_u8_u8_fn)(uintptr_t)SPHE_ADDR_SET_SPEAKER_CHANNEL_STATE)(
        (uint8_t)channel,
        state
    );
}

static inline void
sphe_apply_subwoofer_state(uint8_t enabled)
{
    ((sphe_u8_fn)(uintptr_t)SPHE_ADDR_APPLY_SUBWOOFER_STATE)(
        enabled ? SPHE_SUBWOOFER_STATE_ON : SPHE_SUBWOOFER_STATE_OFF);
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
