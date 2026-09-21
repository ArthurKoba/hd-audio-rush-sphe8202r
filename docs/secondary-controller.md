# Secondary controller / AC695N evidence

Physical package marking recorded from the board:
`AK24BP24230`

No exact public part number has yet been proven from that marking alone.

## Captured firmware log

A UART capture from the device contains source/build strings from a JieLi AC69xx soundbox codebase, including:

`E:\Project\AC69XX\Software\AC695N_soundbox_sdk_release_3.1.0_LineIn_IIS\SDK\apps\soundbox\board\br23\board_ac695x_demo\board_ac695x_demo.c`

Other observed anchors include:
- `jl_soundbox_lihui`
- `audio_enc_init`
- `audio_dec_init`
- `audio_dac_init`
- `ALINK_SR = 44100`
- `spdif_dec_start`
- volume config: max 31, default 25
- `VOL_SAVE`

This proves AC695N/BR23 software exists in the running system. It does not yet prove which external header is directly connected to that controller.

## Open questions

- exact JL public SKU;
- internal flash size and dump method for this specific marked part;
- exact transport between secondary controller and SPHE;
- which device owns each UART/service pad;
- whether the secondary controller participates in compressed S/PDIF decode or only routing/control.
