    .set noreorder
    .set noat
    .text
    .globl _start
    .ent _start
_start:
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
