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

/* Shared 32-bit code pointer used as the active media parser/continuation callback. */
#define SPHE_STATE_MEDIA_CONTINUATION_CALLBACK 0x800031E4U

/*
 * Shared media stream-buffer cursor contract.  AP1/CDROM/DRV/WMA use the
 * same base pointer with 16-bit limit/cursor offsets.
 */
#define SPHE_STATE_MEDIA_STREAM_BUFFER_BASE_PTR      0x80003144U
#define SPHE_STATE_MEDIA_STREAM_BUFFER_END_OFFSET    0x8000325CU
#define SPHE_STATE_MEDIA_STREAM_BUFFER_CURSOR_OFFSET 0x80003268U

#endif
