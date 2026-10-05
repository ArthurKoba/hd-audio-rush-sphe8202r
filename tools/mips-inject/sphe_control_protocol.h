#ifndef SPHE_CONTROL_PROTOCOL_H
#define SPHE_CONTROL_PROTOCOL_H

/*
 * Shared command/result vocabulary for replacement-source control surfaces.
 * These values belong to our transport APIs; they are not stock firmware IDs.
 * Canonical and legacy namespaces stay separate even where values overlap.
 */

enum sphe_audio_control_opcode {
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

enum sphe_audio_control_result {
    SPHE_CTL_OK           = 0,
    SPHE_CTL_BAD_OPCODE   = -1,
    SPHE_CTL_BAD_ARGUMENT = -2,
    SPHE_CTL_BAD_LENGTH   = -3,
};

enum sphe_legacy_control_opcode {
    SPHE_CTRL_SET_MASTER_VOLUME       = 0x01,
    SPHE_CTRL_TOGGLE_MASTER_MUTE      = 0x02,
    SPHE_CTRL_SET_SURROUND            = 0x03,
    SPHE_CTRL_SET_EQ_SELECTION        = 0x04,
    SPHE_CTRL_SET_DOWNSAMPLE          = 0x05,
    SPHE_CTRL_SET_ECHO_LEVEL          = 0x06,
    SPHE_CTRL_SET_MIC1_LEVEL          = 0x07,
    SPHE_CTRL_APPLY_SPDIF_OPTION      = 0x08,
    SPHE_CTRL_SET_DECODER_OUTPUT_MODE = 0x09,
    SPHE_CTRL_SET_EXTERNAL_INPUT_MODE = 0x0A,
    SPHE_CTRL_SET_EXTERNAL_SUBSOURCE  = 0x0B,
};

enum sphe_legacy_control_result {
    SPHE_CONTROL_OK           = 0,
    SPHE_CONTROL_NULL_COMMAND = -1,
    SPHE_CONTROL_BAD_ARGUMENT = -2,
    SPHE_CONTROL_BAD_OPCODE   = -3,
};

#endif
