#ifndef SPHE_MEDIA_CONTRACT_H
#define SPHE_MEDIA_CONTRACT_H

#include <stdint.h>

/*
 * Shared media/runtime state recovered across the primary MIPS modules.
 * Keep these separate from the audio-control contract so common playback
 * state does not acquire audio-specific names by accident.
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

#endif
