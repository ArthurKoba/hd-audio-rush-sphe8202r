#include <stdint.h>

extern int DispatchAudioHardwareAction(
    uint32_t action,
    uint32_t value,
    uint32_t aux
);

/*
 * Compiler/ABI validation replacement for the stock
 * ApplySurroundModeIndex @ 0x80702D0C.
 *
 * The C-visible contract is intentionally identical:
 *   DispatchAudioHardwareAction(5, index & 0xff, 0)
 *
 * The linker binds DispatchAudioHardwareAction to its recovered absolute
 * address so the compiler emits the same direct JAL class used by stock code.
 */
__attribute__((used, noinline, aligned(4)))
int injected_apply_surround(uint32_t index)
{
    return DispatchAudioHardwareAction(5U, index & 0xffU, 0U);
}
