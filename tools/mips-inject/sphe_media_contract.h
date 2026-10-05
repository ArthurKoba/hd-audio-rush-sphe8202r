#ifndef SPHE_MEDIA_CONTRACT_H
#define SPHE_MEDIA_CONTRACT_H

#include <stdint.h>

/*
 * Shared media/runtime state recovered across the primary MIPS modules.
 * Keep these separate from the audio-control contract so common playback
 * state does not acquire audio-specific names by accident.
 *
 * This file contains the paused media-runtime refactor findings. The saved
 * Analysis project remains canonical; entries not yet represented there are
 * provisional migration debt, not a second semantic authority.
 */

/* Encoded media/playback state: low 14-bit media code plus high flag bits. */
#define SPHE_STATE_MEDIA_STATE_WORD       0x80003254U

/*
 * Shared trick-play scan-speed/state byte. The live Analysis project names
 * this state from AP1; exact physical/time units remain unknown.
 */
#define SPHE_STATE_TRICKPLAY_SCAN_SPEED   0x80003250U

/* Shared 16-bit media/runtime flags; individual bit meanings remain contextual. */
#define SPHE_STATE_MEDIA_RUNTIME_FLAGS       0x8000326AU

/* Shared byte-sized media state machine value; semantic value names remain open. */
#define SPHE_STATE_MEDIA_RUNTIME_SUBSTATE    0x800032A9U

/* Shared byte-sized media mode code; value meanings are not all recovered. */
#define SPHE_STATE_MEDIA_MODE_CODE           0x8000331CU

/* Selected continuation handler copied into the active callback slot by media setup. */
#define SPHE_STATE_MEDIA_SELECTED_CONTINUATION_CALLBACK 0x8000315CU
#define SPHE_STATE_MEDIA_ACTIVE_CONTINUATION_CALLBACK   0x800031E4U

/* Active media-state filter; AP1 invokes this slot through jalr. */
#define SPHE_STATE_MEDIA_STATE_FILTER_CALLBACK 0x8000318CU

/* Confirmed filter implementations stored in the callback slot. */
#define SPHE_ADDR_FILTER_MEDIA_STATE_FOR_CONTEXT 0x806E45D0U
#define SPHE_ADDR_IDENTITY_MEDIA_STATE_FILTER    0x806F4938U

/*
 * Shared media stream-buffer cursor contract.  AP1/CDROM/DRV/WMA use the
 * same base pointer with 16-bit limit/cursor offsets.
 */
#define SPHE_STATE_MEDIA_STREAM_BUFFER_BASE_PTR      0x80003144U
#define SPHE_STATE_MEDIA_STREAM_BUFFER_END_OFFSET    0x8000325CU
#define SPHE_STATE_MEDIA_STREAM_BUFFER_CURSOR_OFFSET 0x80003268U

/* Already-documented CDROM packed-stream classifier contract. */
enum sphe_cdrom_classifier_result {
    SPHE_CDROM_CLASSIFIER_FAILURE     = -1,
    SPHE_CDROM_CLASSIFIER_SIGNATURE_A = 1,
    SPHE_CDROM_CLASSIFIER_SIGNATURE_B = 2,
    SPHE_CDROM_CLASSIFIER_AC3         = 0x0AC3,
};

enum sphe_cdrom_packed_stream_mode {
    SPHE_CDROM_PACKED_MODE_NONE        = 0,
    SPHE_CDROM_PACKED_MODE_SIGNATURE_A = 1,
    SPHE_CDROM_PACKED_MODE_SIGNATURE_B = 2,
    SPHE_CDROM_PACKED_MODE_AC3         = 3,
};

#define SPHE_STATE_CDROM_PACKED_STREAM_WORKING_STATE 0x80003704U
#define SPHE_STATE_CDROM_PACKED_STREAM_MODE          0x80003718U
#define SPHE_STATE_CDROM_SIGNATURE_A_ACTIVE          0x80003719U
#define SPHE_STATE_CDROM_SIGNATURE_B_ACTIVE          0x8000371AU
#define SPHE_STATE_CDROM_SIGNATURE_B_WORDS           0x80002D60U
#define SPHE_STATE_CDROM_SIGNATURE_A_WORDS           0x80002D64U

#define SPHE_ADDR_MAP_CDROM_SUBTYPE_TO_AUDIO_MODE    0x8074C800U
#define SPHE_ADDR_DETECT_CDROM_STREAM_TYPE           0x8074C868U
#define SPHE_ADDR_INITIALIZE_CDROM_PACKED_STREAM     0x8074CB2CU

#endif
