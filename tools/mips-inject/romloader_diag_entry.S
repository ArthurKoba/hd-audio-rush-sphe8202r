    .set noreorder
    .section .text.entry,"ax",@progbits
    .globl romloader_diag_entry
    .type romloader_diag_entry,@function

romloader_diag_entry:
    lui     $s6, 0xBFFE
    ori     $s6, $s6, 0x8000

    lui     $sp, 0x8000
    addiu   $sp, $sp, 0x1000

    lui     $gp, 0x8000
    addiu   $gp, $gp, 0x13E4

    j       romloader_diag_main
    nop

    .size romloader_diag_entry, .-romloader_diag_entry
