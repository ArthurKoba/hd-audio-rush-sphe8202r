#ifndef SPHE_CONTROL_PLANE_H
#define SPHE_CONTROL_PLANE_H

#include <stdint.h>

enum sphe_legacy_control_opcode {
    SPHE_CTRL_SET_MASTER_VOLUME = 0x01,
    SPHE_CTRL_TOGGLE_MASTER_MUTE = 0x02,
    SPHE_CTRL_SET_SURROUND = 0x03,
    SPHE_CTRL_SET_EQ_SELECTION = 0x04,
    SPHE_CTRL_SET_DOWNSAMPLE = 0x05,
    SPHE_CTRL_SET_ECHO_LEVEL = 0x06,
    SPHE_CTRL_SET_MIC1_LEVEL = 0x07,
    SPHE_CTRL_APPLY_SPDIF_OPTION = 0x08,
    SPHE_CTRL_SET_DECODER_OUTPUT_MODE = 0x09,
    SPHE_CTRL_SET_EXTERNAL_INPUT_MODE = 0x0A,
    SPHE_CTRL_SET_EXTERNAL_SUBSOURCE = 0x0B,
};

enum sphe_legacy_control_result {
    SPHE_CONTROL_OK = 0,
    SPHE_CONTROL_NULL_COMMAND = -1,
    SPHE_CONTROL_BAD_ARGUMENT = -2,
    SPHE_CONTROL_BAD_OPCODE = -3,
};

struct sphe_control_command {
    uint8_t opcode;
    uint8_t value;
    uint16_t aux;
};

struct sphe_control_status {
    uint8_t master_volume;
    uint8_t master_mute;
    uint8_t external_subsource;
    uint8_t source_state;

    uint8_t surround_selection;
    uint8_t eq_selection;
    uint8_t echo_level;
    uint8_t mic1_level;

    uint16_t downsample_mask;
    uint16_t speaker_topology;
    uint32_t decoder_state;
};

/*
 * Compatibility wrapper over the canonical sphe_audio_control API.
 * Returns 0 on success.
 * Negative values are local validation/dispatch failures; they are not
 * original firmware error codes.
 */
int sphe_handle_control_command(const struct sphe_control_command *cmd);
void sphe_read_control_status(struct sphe_control_status *status);

#endif
