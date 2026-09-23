#ifndef SPHE_AUDIO_CONTROL_PLANE_H
#define SPHE_AUDIO_CONTROL_PLANE_H

#include <stdint.h>

/*
 * Transport-agnostic minimal audio control plane.
 *
 * It is intentionally independent from the stock DVD/UI/menu event model.
 * A future UART/ALINK/secondary-MCU transport can decode its own wire format
 * and feed these commands into sphe_audio_control_apply().
 */

enum sphe_control_opcode {
    SPHE_CTL_MASTER_VOLUME   = 0x01,
    SPHE_CTL_MASTER_MUTE     = 0x02,

    SPHE_CTL_SPDIF_OUTPUT    = 0x10,
    SPHE_CTL_DOWNSAMPLE      = 0x11,
    SPHE_CTL_DOWNMIX         = 0x12,
    SPHE_CTL_GM5             = 0x13,

    SPHE_CTL_SURROUND        = 0x20,
    SPHE_CTL_EQ_PRESET       = 0x21,
    SPHE_CTL_EQ_USER7        = 0x22,

    SPHE_CTL_SPEAKER_STATE   = 0x30,
    SPHE_CTL_SUBWOOFER       = 0x31,
    SPHE_CTL_SPEAKER_DELAY   = 0x32,
};

enum sphe_control_status {
    SPHE_CTL_OK              = 0,
    SPHE_CTL_BAD_OPCODE      = -1,
    SPHE_CTL_BAD_ARGUMENT    = -2,
    SPHE_CTL_BAD_LENGTH      = -3,
};

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
