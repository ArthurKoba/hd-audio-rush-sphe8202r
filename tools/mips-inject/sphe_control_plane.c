#include "sphe_control_plane.h"
#include "sphe_audio_api.h"

int
sphe_handle_control_command(const struct sphe_control_command *cmd)
{
    if (cmd == (const struct sphe_control_command *)0) {
        return -1;
    }

    switch ((enum sphe_control_opcode)cmd->opcode) {
    case SPHE_CTRL_SET_MASTER_VOLUME:
        return sphe_set_master_volume(cmd->value);

    case SPHE_CTRL_TOGGLE_MASTER_MUTE:
        sphe_toggle_master_mute();
        return 0;

    case SPHE_CTRL_SET_SURROUND:
        return sphe_set_surround_mode(
            (enum sphe_surround_mode)cmd->value
        );

    case SPHE_CTRL_SET_EQ_SELECTION:
        return sphe_set_eq_selection_stateful(
            (enum sphe_eq_selection)cmd->value
        );

    case SPHE_CTRL_SET_DOWNSAMPLE:
        if (cmd->value > (uint8_t)SPHE_DOWNSAMPLE_192K) {
            return -2;
        }
        sphe_set_downsample_mode(cmd->value);
        return 0;

    case SPHE_CTRL_SET_ECHO_LEVEL:
        return sphe_set_echo_level_stateful(cmd->value);

    case SPHE_CTRL_SET_MIC1_LEVEL:
        return sphe_set_mic1_level_stateful(cmd->value);

    case SPHE_CTRL_APPLY_SPDIF_OPTION:
        if (cmd->value != (uint8_t)SPHE_SPDIF_OFF &&
            cmd->value != (uint8_t)SPHE_SPDIF_RAW &&
            cmd->value != (uint8_t)SPHE_SPDIF_PCM) {
            return -2;
        }
        sphe_apply_spdif_output_option(
            (enum sphe_spdif_output_option)cmd->value
        );
        return 0;

    case SPHE_CTRL_SET_DECODER_OUTPUT_MODE:
        sphe_set_decoder_output_mode(cmd->value, cmd->aux);
        return 0;

    default:
        return -3;
    }
}
