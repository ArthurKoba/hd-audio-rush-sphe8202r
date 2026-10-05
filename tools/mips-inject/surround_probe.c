#include <stdint.h>

#include "sphe_audio_contract.h"

extern int DispatchAudioHardwareAction(
    enum sphe_audio_action action,
    uint32_t value,
    uint32_t aux
);

/*
 * Compiler/ABI validation replacement for the stock
 * ApplySurroundModeIndex @ 0x80702D0C.
 *
 * The C-visible contract is intentionally identical:
 *   DispatchAudioHardwareAction(SPHE_AUDIO_ACTION_SURROUND, (uint8_t)index, 0)
 *
 * The linker binds DispatchAudioHardwareAction to its recovered absolute
 * address so the compiler emits the same direct JAL class used by stock code.
 */
__attribute__((used, noinline, aligned(4)))
int injected_apply_surround(uint32_t index)
{
    return DispatchAudioHardwareAction(\n        SPHE_AUDIO_ACTION_SURROUND,\n        (uint8_t)index,\n        0U\n    );
}
