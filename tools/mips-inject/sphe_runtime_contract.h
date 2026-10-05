#ifndef SPHE_RUNTIME_CONTRACT_H
#define SPHE_RUNTIME_CONTRACT_H

/*
 * Recovered ROM/runtime module-loader vocabulary.
 * The saved Analysis project is the canonical semantic authority; this header
 * mirrors confirmed runtime constants for replacement-source reuse.
 */

#define SPHE_RUNTIME_GP_RESTORE_WORD      0x88012200U
#define SPHE_ADDR_BUSY_WAIT_OUTER_ITERATIONS 0x880120DCU

#define SPHE_RUNTIME_MODULE_OFFSET_TABLE      0x88014260U
#define SPHE_RUNTIME_PACKED_MODULE_DATA_BASE 0x880142CCU
#define SPHE_BUSY_WAIT_INNER_COUNT          0x6976U

enum sphe_runtime_module_layout {
    SPHE_RUNTIME_MODULE_SLOT_COUNT = 27,
};

enum sphe_runtime_module_slot {
    SPHE_MODULE_SLOT_MPEG      = 1,
    SPHE_MODULE_SLOT_AP1       = 3,
    SPHE_MODULE_SLOT_CDROM     = 4,
    SPHE_MODULE_SLOT_DRV_OTHER = 7,
    SPHE_MODULE_SLOT_AP2       = 9,
    SPHE_MODULE_SLOT_FREE      = 11,
    SPHE_MODULE_SLOT_WMA       = 14,
};

enum sphe_runtime_module_destination {
    SPHE_MODULE_DEST_AP1       = 0x8067B800,
    SPHE_MODULE_DEST_WMA       = 0x8073F000,
    SPHE_MODULE_DEST_CDROM     = 0x8074C800,
    SPHE_MODULE_DEST_DRV_OTHER = 0x80775800,
};

#endif
