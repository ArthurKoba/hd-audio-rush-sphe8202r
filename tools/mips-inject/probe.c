#include <stdint.h>

/*
 * Harmless ABI/toolchain probe only.
 * No MMIO access, no calls into the existing firmware.
 */
__attribute__((used, noinline))
uint32_t sphe_probe_add(uint32_t a, uint32_t b)
{
    return a + b;
}
