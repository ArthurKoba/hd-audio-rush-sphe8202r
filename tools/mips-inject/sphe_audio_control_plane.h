#ifndef SPHE_AUDIO_CONTROL_PLANE_H
#define SPHE_AUDIO_CONTROL_PLANE_H

#include <stdint.h>

#include "sphe_control_protocol.h"

/*
 * Transport-agnostic minimal audio control plane.
 *
 * It is intentionally independent from the stock DVD/UI/menu event model.
 * A future UART/ALINK/secondary-MCU transport can decode its own wire format
 * and feed these commands into sphe_audio_control_apply().
 */



struct sphe_audio_control_command {
    uint8_t opcode;
    uint8_t arg0;
    uint8_t arg1;
    uint8_t length;
    uint8_t payload[7];
};

struct sphe_audio_control_snapshot {
    uint8_t master_volume;
    uint8_t master_muted;

    uint8_t surround_mode;
    uint8_t eq_selection;

    uint8_t speaker_front;
    uint8_t speaker_center;
    uint8_t speaker_rear;
    uint8_t subwoofer;

    uint8_t downsample_mode;
    uint8_t external_input_selector;
    uint16_t reserved;

    uint32_t decoder_state;
};

int sphe_audio_control_apply(const struct sphe_audio_control_command *command);
void sphe_audio_control_snapshot(struct sphe_audio_control_snapshot *snapshot);

#endif
