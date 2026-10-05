#ifndef SPHE_CONTROL_PLANE_H
#define SPHE_CONTROL_PLANE_H

#include <stdint.h>

#include "sphe_control_protocol.h"



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
