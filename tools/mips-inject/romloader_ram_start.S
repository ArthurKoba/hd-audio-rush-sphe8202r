.set noreorder
.set noat

.section .text.start, "ax", @progbits
.globl _start
.ent _start
_start:
    lui     $sp, 0x8000
    addiu   $sp, $sp, 0x1000

    lui     $s6, 0xbffe
    ori     $s6, $s6, 0x8000

    jal     ram_main
    nop

1:
    b       1b
    nop
.end _start
