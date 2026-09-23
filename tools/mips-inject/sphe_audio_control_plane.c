#include "sphe_audio_control_plane.h"
#include "sphe_audio_api.h"

#define REG8(addr)  (*(volatile uint8_t *)(uintptr_t)(addr))
#define REG16(addr) (*(volatile uint16_t *)(uintptr_t)(addr))
#define REG32(addr) (*(volatile uint32_t *)(uintptr_t)(addr))

/* Confirmed AP1 runtime state locations for the preserved 02R-D-02 image. */
#define MASTER_MUTE_FLAG        REG8(0x800032B5U)
#define MASTER_VOLUME_LEVEL     REG8(0x80003332U)
#define CURRENT_SURROUND_SEL    REG8(0x80002B0CU)
#define CURRENT_EQ_SEL          REG8(0x80002B0DU)
#define USER_EQ7_BASE           ((volatile uint8_t *)(uintptr_t)0x80002B10U)

#define SPEAKER_FRONT_STATE     REG8(0x80003327U)
#define SPEAKER_CENTER_STATE    REG8(0x800032DCU)
#define SPEAKER_REAR_STATE      REG8(0x8000330EU)
#define SUBWOOFER_STATE         REG8(0x800032D6U)

#define DOWNSAMPLE_MODE_MASK    REG16(0x80003244U)
#define EXTERNAL_INPUT_SELECTOR REG8(0x800032FAU)
#define DECODER_STATE           REG32(0x80003198U)

#define CONTROL_DESCRIPTOR_BASE ((volatile uint8_t *)(uintptr_t)0x80707EACU)
#define CONTROL_SELECTION_BASE  ((volatile uint8_t *)(uintptr_t)0x800066B0U)
#define CONTROL_STATE_BASE      ((volatile uint8_t *)(uintptr_t)0x80006810U)

typedef uint32_t (*resolve_control_fn)(uint32_t control_id);
typedef void (*dispatch_control_fn)(
    uint32_t control_id,
    uint32_t option_id,
    uint32_t side_effects
);

#define RESOLVE_CONTROL     ((resolve_control_fn)(uintptr_t)0x80777E20U)
#define DISPATCH_CONTROL     ((dispatch_control_fn)(uintptr_t)0x80776210U)

static int set_descriptor_option(uint8_t control_id, uint8_t option_id)
{
    uint32_t resolved;
    uint32_t group;
    uint32_t slot;
    uint32_t position;
    uint8_t state_slot;
    volatile uint8_t *descriptor;

    resolved = RESOLVE_CONTROL(control_id);
    if ((resolved & 0xFFFFU) == 0xFFFFU) {
        return SPHE_CTL_BAD_ARGUMENT;
    }

    group = (resolved >> 8) & 0xFFU;
    slot = resolved & 0xFFU;
    descriptor =
        CONTROL_DESCRIPTOR_BASE + group * 0x75U + slot * 0x0DU;

    position = 2U;
    while (position < 10U && descriptor[position] != option_id) {
        ++position;
    }
    if (position >= 10U) {
        return SPHE_CTL_BAD_ARGUMENT;
    }

    CONTROL_SELECTION_BASE[group * 9U + slot] = (uint8_t)position;

    state_slot = descriptor[0x0BU];
    if (state_slot < 0x41U) {
        CONTROL_STATE_BASE[state_slot] = (uint8_t)position;
    }

    DISPATCH_CONTROL(control_id, option_id, 1U);
    return SPHE_CTL_OK;
}

static int set_master_volume(uint8_t level)
{
    /*
     * SetMasterVolumeLevel itself only applies the effective hardware level.
     * Keep the stock runtime level coherent so later unmute/reapply routes use
     * the externally selected value.
     */
    MASTER_VOLUME_LEVEL = level;
    sphe_set_master_volume(level);
    return SPHE_CTL_OK;
}

static int set_master_mute(uint8_t requested)
{
    uint8_t wanted = requested ? 1U : 0U;
    if ((MASTER_MUTE_FLAG ? 1U : 0U) != wanted) {
        sphe_toggle_master_mute();
    }
    return SPHE_CTL_OK;
}

static int set_surround(uint8_t mode)
{
    if (mode > SPHE_SURROUND_LIVE) {
        return SPHE_CTL_BAD_ARGUMENT;
    }

    /*
     * Stock current-state encoding is selection 2..7 while the backend index
     * is 0..5. Keeping the state byte coherent prevents later EQ reapply from
     * reverting the externally chosen surround mode.
     */
    CURRENT_SURROUND_SEL = (uint8_t)(mode + 2U);
    sphe_set_surround_index(mode);
    return SPHE_CTL_OK;
}

static int set_eq_preset(uint8_t selection)
{
    if (selection < SPHE_EQ_STANDARD || selection > SPHE_EQ_USER) {
        return SPHE_CTL_BAD_ARGUMENT;
    }
    if (selection == SPHE_EQ_USER) {
        /* USER requires the seven-byte vector; use SPHE_CTL_EQ_USER7. */
        return SPHE_CTL_BAD_ARGUMENT;
    }

    CURRENT_EQ_SEL = selection;
    sphe_reapply_eq_and_surround();
    return SPHE_CTL_OK;
}

static int set_eq_user7(const struct sphe_audio_control_command *command)
{
    unsigned i;

    if (command->length != 7U) {
        return SPHE_CTL_BAD_LENGTH;
    }

    for (i = 0; i < 7U; ++i) {
        USER_EQ7_BASE[i] = command->payload[i];
    }
    CURRENT_EQ_SEL = SPHE_EQ_USER;

    /*
     * This route reapplies USER EQ and then restores current surround, which
     * avoids the local surround-clear side effect of the coefficient uploader.
     */
    sphe_reapply_eq_and_surround();
    return SPHE_CTL_OK;
}

static int set_speaker_state(uint8_t channel, uint8_t state)
{
    if (channel > SPHE_SPEAKER_SUBWOOFER) {
        return SPHE_CTL_BAD_ARGUMENT;
    }

    if (channel == SPHE_SPEAKER_SUBWOOFER) {
        if (state > 1U) {
            return SPHE_CTL_BAD_ARGUMENT;
        }
        sphe_set_speaker_channel_state(SPHE_SPEAKER_SUBWOOFER, state);
        sphe_apply_subwoofer_state(state);
        return SPHE_CTL_OK;
    }

    if (channel == SPHE_SPEAKER_FRONT) {
        if (state > SPHE_SPEAKER_SMALL) {
            return SPHE_CTL_BAD_ARGUMENT;
        }
    } else if (state > SPHE_SPEAKER_OFF) {
        return SPHE_CTL_BAD_ARGUMENT;
    }

    sphe_set_speaker_channel_state(
        (enum sphe_speaker_channel)channel,
        state
    );
    sphe_reapply_speaker_topology();
    return SPHE_CTL_OK;
}

int sphe_audio_control_apply(const struct sphe_audio_control_command *command)
{
    if (command == 0) {
        return SPHE_CTL_BAD_ARGUMENT;
    }

    switch (command->opcode) {
    case SPHE_CTL_MASTER_VOLUME:
        return set_master_volume(command->arg0);

    case SPHE_CTL_MASTER_MUTE:
        return set_master_mute(command->arg0);

    case SPHE_CTL_SPDIF_OUTPUT:
        return set_descriptor_option(0x71U, command->arg0);

    case SPHE_CTL_DOWNSAMPLE:
        if (command->arg0 == SPHE_DOWNSAMPLE_48K) {
            return set_descriptor_option(0x5BU, 0x4FU);
        }
        if (command->arg0 == SPHE_DOWNSAMPLE_96K) {
            return set_descriptor_option(0x5BU, 0x50U);
        }
        if (command->arg0 == SPHE_DOWNSAMPLE_192K) {
            return set_descriptor_option(0x5BU, 0x51U);
        }
        return SPHE_CTL_BAD_ARGUMENT;

    case SPHE_CTL_DOWNMIX:
        return set_descriptor_option(0xF5U, command->arg0);

    case SPHE_CTL_GM5:
        return set_descriptor_option(0x9EU, command->arg0);

    case SPHE_CTL_SURROUND:
        return set_surround(command->arg0);

    case SPHE_CTL_EQ_PRESET:
        return set_eq_preset(command->arg0);

    case SPHE_CTL_EQ_USER7:
        return set_eq_user7(command);

    case SPHE_CTL_SPEAKER_STATE:
        if (command->arg0 == SPHE_SPEAKER_FRONT) {
            if (command->arg1 == SPHE_SPEAKER_LARGE) {
                return set_descriptor_option(0xD3U, 0x24U);
            }
            if (command->arg1 == SPHE_SPEAKER_SMALL) {
                return set_descriptor_option(0xD3U, 0x2AU);
            }
            return SPHE_CTL_BAD_ARGUMENT;
        }
        if (command->arg0 == SPHE_SPEAKER_CENTER ||
            command->arg0 == SPHE_SPEAKER_REAR) {
            uint8_t control_id =
                command->arg0 == SPHE_SPEAKER_CENTER ? 0xCDU : 0xCEU;
            if (command->arg1 == SPHE_SPEAKER_LARGE) {
                return set_descriptor_option(control_id, 0x24U);
            }
            if (command->arg1 == SPHE_SPEAKER_SMALL) {
                return set_descriptor_option(control_id, 0x2AU);
            }
            if (command->arg1 == SPHE_SPEAKER_OFF) {
                return set_descriptor_option(control_id, 0x7BU);
            }
            return SPHE_CTL_BAD_ARGUMENT;
        }
        if (command->arg0 == SPHE_SPEAKER_SUBWOOFER) {
            return set_descriptor_option(
                0x8BU,
                command->arg1 ? 0x8DU : 0x7BU
            );
        }
        return SPHE_CTL_BAD_ARGUMENT;

    case SPHE_CTL_SUBWOOFER:
        return set_descriptor_option(
            0x8BU,
            command->arg0 ? 0x8DU : 0x7BU
        );

    case SPHE_CTL_SPEAKER_DELAY:
        if (command->arg0 != 1U && command->arg0 != 2U) {
            return SPHE_CTL_BAD_ARGUMENT;
        }
        sphe_set_speaker_delay(
            command->arg0,
            (uint16_t)(command->payload[0] |
                       ((uint16_t)command->payload[1] << 8))
        );
        return SPHE_CTL_OK;

    default:
        return SPHE_CTL_BAD_OPCODE;
    }
}


static uint8_t current_downsample_mode(void)
{
    switch (DOWNSAMPLE_MODE_MASK) {
    case 0x0007:
        return SPHE_DOWNSAMPLE_48K;
    case 0x0067:
        return SPHE_DOWNSAMPLE_96K;
    case 0x0667:
        return SPHE_DOWNSAMPLE_192K;
    default:
        return 0xFFU;
    }
}

void sphe_audio_control_snapshot(struct sphe_audio_control_snapshot *snapshot)
{
    uint8_t surround_selection;

    if (snapshot == 0) {
        return;
    }

    snapshot->master_volume = MASTER_VOLUME_LEVEL;
    snapshot->master_muted = MASTER_MUTE_FLAG ? 1U : 0U;

    surround_selection = CURRENT_SURROUND_SEL;
    snapshot->surround_mode =
        (surround_selection >= 2U && surround_selection <= 7U)
            ? (uint8_t)(surround_selection - 2U)
            : 0xFFU;
    snapshot->eq_selection = CURRENT_EQ_SEL;

    snapshot->speaker_front = SPEAKER_FRONT_STATE;
    snapshot->speaker_center = SPEAKER_CENTER_STATE;
    snapshot->speaker_rear = SPEAKER_REAR_STATE;
    snapshot->subwoofer = SUBWOOFER_STATE;

    snapshot->downsample_mode = current_downsample_mode();
    snapshot->external_input_selector = EXTERNAL_INPUT_SELECTOR;
    snapshot->reserved = 0;

    snapshot->decoder_state = DECODER_STATE;
}
