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

#endif
