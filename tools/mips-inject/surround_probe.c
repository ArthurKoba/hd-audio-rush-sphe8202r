#include <stdint.h>

typedef int (*audio_dispatch_fn)(uint32_t action, uint32_t value, uint32_t aux);

/*
 * Compiler/ABI validation replacement for the original
 * ApplySurroundModeIndex @ 0x80702D0C.
 *
 * It intentionally preserves the original externally visible behavior:
 *   action = 5
 *   value  = index & 0xff
 *   aux    = 0
 *
 * No new feature is introduced by this replacement.
 */
__attribute__((used, noinline, aligned(4)))
int injected_apply_surround(uint32_t index)
{
    audio_dispatch_fn dispatch =
        (audio_dispatch_fn)(uintptr_t)0x806FFD1CU;
    return dispatch(5U, index & 0xffU, 0U);
}
