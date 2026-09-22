#ifndef SPHE_AUDIO_API_H
#define SPHE_AUDIO_API_H

#include <stdint.h>

/*
 * Minimal recovered AP1 audio ABI for code injected into the running
 * SPHE8202R application.
 *
 * These addresses are target-specific to the preserved 02R-D-02 image.
 * The caller must execute under the original AP1 runtime so the firmware's
 * $gp/$s6 state and backend runtime services are already initialized.
 */

typedef int (*sphe_audio_dispatch_fn)(
    uint32_t action,
    uint32_t value,
    uint32_t aux
);

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

static inline int
sphe_audio_dispatch(uint32_t action, uint32_t value, uint32_t aux)
{
    return ((sphe_audio_dispatch_fn)(uintptr_t)0x806FFD1CU)(
        action, value, aux
    );
}

/*
 * Stateful firmware wrappers.
 *
 * Prefer these over the raw dispatcher when they also update AP1 state.
 */

typedef int (*sphe_u8_fn)(uint32_t);
typedef int (*sphe_u8_u16_fn)(uint32_t, uint32_t);
typedef void (*sphe_void_fn)(void);

static inline int
sphe_set_master_volume(uint8_t level)
{
    return ((sphe_u8_fn)(uintptr_t)0x8070129CU)(level);
}

static inline void
sphe_toggle_master_mute(void)
{
    ((sphe_void_fn)(uintptr_t)0x806F9D18U)();
}

static inline int
sphe_set_spdif_hardware_mode(uint8_t mode)
{
    /*
     * ApplySpdifHardwareOutputMode also stores the selected byte in AP1 state
     * before dispatching action 7.
     */
    return ((sphe_u8_fn)(uintptr_t)0x80702BA0U)(mode);
}

static inline int
sphe_set_decoder_output_mode(uint8_t mode, uint16_t aux)
{
    return ((sphe_u8_u16_fn)(uintptr_t)0x80702BD0U)(mode, aux);
}

static inline int
sphe_set_speaker_delay(uint8_t channel, uint16_t delay)
{
    return ((sphe_u8_u16_fn)(uintptr_t)0x80702C60U)(channel, delay);
}

static inline int
sphe_set_echo_profile(uint8_t index)
{
    return ((sphe_u8_fn)(uintptr_t)0x80702C8CU)(index);
}

static inline int
sphe_set_mic1_level(uint8_t index)
{
    return ((sphe_u8_fn)(uintptr_t)0x80702B48U)(index);
}

static inline int
sphe_set_mic2_selection(uint8_t index)
{
    return ((sphe_u8_fn)(uintptr_t)0x80702B74U)(index);
}

static inline int
sphe_set_downsample_mode(uint16_t mode)
{
    return ((sphe_u8_fn)(uintptr_t)0x80701B80U)(mode);
}

static inline void
sphe_reapply_speaker_topology(void)
{
    ((sphe_void_fn)(uintptr_t)0x8070106CU)();
}

/*
 * Stateless low-level wrappers. These are equivalent to the recovered tiny
 * AP1 action wrappers and are useful when the caller owns the new state.
 */

static inline int
sphe_set_surround_index(uint8_t index)
{
    return sphe_audio_dispatch(
        SPHE_AUDIO_ACTION_SURROUND,
        index,
        0
    );
}

static inline int
sphe_set_eq_processing_mode(uint8_t mode)
{
    return sphe_audio_dispatch(
        SPHE_AUDIO_ACTION_EQ_PROCESSING,
        mode,
        0
    );
}

static inline int
sphe_set_subwoofer_hardware_state(uint8_t state)
{
    return sphe_audio_dispatch(
        SPHE_AUDIO_ACTION_SUBWOOFER,
        state,
        0
    );
}

#endif
