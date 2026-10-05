#include "sphe_control_plane.h"
#include "sphe_audio_api.h"
#include "sphe_audio_control.h"

int
sphe_handle_control_command(const struct sphe_control_command *cmd)
{
    if (cmd == (const struct sphe_control_command *)0) {
        return SPHE_CONTROL_NULL_COMMAND;
    }

    switch ((enum sphe_legacy_control_opcode)cmd->opcode) {
    case SPHE_CTRL_SET_MASTER_VOLUME:
        return sphe_control_set_master_volume(cmd->value)
            ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;

    case SPHE_CTRL_TOGGLE_MASTER_MUTE:
        sphe_toggle_master_mute();
        return SPHE_CONTROL_OK;

    case SPHE_CTRL_SET_SURROUND:
        return sphe_control_set_surround((enum sphe_surround_mode)cmd->value)
            ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;

    case SPHE_CTRL_SET_EQ_SELECTION:
        return sphe_control_set_eq_selection((enum sphe_eq_selection)cmd->value)
            ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;

    case SPHE_CTRL_SET_DOWNSAMPLE:
        return sphe_control_set_downsample((enum sphe_downsample_mode)cmd->value)
            ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;

    case SPHE_CTRL_SET_ECHO_LEVEL:
        return sphe_control_set_echo(cmd->value)
            ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;

    case SPHE_CTRL_SET_MIC1_LEVEL:
        return sphe_control_set_mic1(cmd->value)
            ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;

    case SPHE_CTRL_APPLY_SPDIF_OPTION:
        return sphe_control_set_spdif_output(
            (enum sphe_spdif_output_option)cmd->value
        ) ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;

    case SPHE_CTRL_SET_DECODER_OUTPUT_MODE:
        sphe_apply_decoder_output_mode(cmd->value, cmd->aux);
        return SPHE_CONTROL_OK;

    case SPHE_CTRL_SET_EXTERNAL_INPUT_MODE:
        return sphe_control_set_external_mode(
            (enum sphe_external_mode_code)cmd->value
        ) ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;

    case SPHE_CTRL_SET_EXTERNAL_SUBSOURCE:
        if (cmd->value == SPHE_EXTERNAL_INPUT_TUNER) {
            return sphe_control_set_tuner_spdif(false)
                ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;
        }
        if (cmd->value == SPHE_EXTERNAL_INPUT_SPDIF) {
            return sphe_control_set_tuner_spdif(true)
                ? SPHE_CONTROL_OK : SPHE_CONTROL_BAD_ARGUMENT;
        }
        return SPHE_CONTROL_BAD_ARGUMENT;

    default:
        return SPHE_CONTROL_BAD_OPCODE;
    }
}


void
sphe_read_control_status(struct sphe_control_status *status)
{
    if (status == (struct sphe_control_status *)0) {
        return;
    }

    status->master_volume =
        *(volatile uint8_t *)(uintptr_t)SPHE_STATE_MASTER_VOLUME;
    status->master_mute =
        *(volatile uint8_t *)(uintptr_t)SPHE_STATE_MASTER_MUTE;
    status->external_subsource =
        *(volatile uint8_t *)(uintptr_t)SPHE_STATE_EXTERNAL_INPUT_SELECTOR;
    status->source_state =
        *(volatile uint8_t *)(uintptr_t)SPHE_STATE_SOURCE_MEDIA;

    status->surround_selection =
        *(volatile uint8_t *)(uintptr_t)SPHE_STATE_SURROUND_SELECTION;
    status->eq_selection =
        *(volatile uint8_t *)(uintptr_t)SPHE_STATE_EQ_PRESET_INDEX;
    status->echo_level =
        *(volatile uint8_t *)(uintptr_t)SPHE_STATE_ECHO;
    status->mic1_level =
        *(volatile uint8_t *)(uintptr_t)SPHE_STATE_MIC1;

    status->downsample_mask =
        *(volatile uint16_t *)(uintptr_t)SPHE_STATE_DOWNSAMPLE_MASK;
    status->speaker_topology =
        *(volatile uint16_t *)(uintptr_t)SPHE_STATE_SPEAKER_TOPOLOGY;
    status->decoder_state =
        *(volatile uint32_t *)(uintptr_t)SPHE_STATE_DECODER;
}
