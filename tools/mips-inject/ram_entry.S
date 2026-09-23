    .set noreorder
    .set noat

    .section .text.entry, "ax", @progbits
    .globl _start
    .ent _start
_start:
    /* Match the recovered Sunplus RAM-loader execution environment. */
    lui     $s6, 0xbffe
    ori     $s6, $s6, 0x8000
    lui     $sp, 0x8000
    addiu   $sp, $sp, 0x1000

    jal     ram_main
    nop

1:
    b       1b
    nop
    .end _start
