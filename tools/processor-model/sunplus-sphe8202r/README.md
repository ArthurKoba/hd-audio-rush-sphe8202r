# Sunplus SPHE8202R DSP — independent processor archive

This directory preserves the complete working ghidra-mcp source snapshot,
compiled Java extension, compiled and source SLEIGH language, native
Ghidra 12.1.3 decompiler patches and verification tools. The originating
ghidra-mcp repository is NOT required to restore the source or binaries.

Contents:
- ghidra-mcp-rush31-complete-source.tar.gz — all tracked ghidra-mcp source
  at commit d10c129858971cacdfb8ae7be1cfb21431a9d424.
- SunplusSPHEAudioDSP — original SLEIGH source and compiled .sla language.
- runtime/GhidraMCP-7.0.0.jar — the exact locally accepted Java extension.
- native-ghidra-12.1.3-patches.tar.gz — byte-preserved Ghidra C generator patch sources.
- acceptance — four original-program fresh import, save and readback records.
- qa, MODEL_MANIFEST.json and SHA256SUMS — checks and identities.

Restore the complete code: tar -xzf ghidra-mcp-rush31-complete-source.tar.gz
This gives the full Maven source, Java recovery passes, processor language,
and tests. Install Ghidra 12.1.3 and JDK 21 separately. Install the processor
under GHIDRA_INSTALL_DIR/Ghidra/Processors, and install the bundled JAR
under the installed GhidraMCP extension lib folder. For equivalent native C
generation, also apply the included upstream Ghidra native decompiler patches;
installing only SLEIGH is insufficient. Build the restored Maven source with
Ghidra API dependencies via tools.setup, then mvn -DskipTests package.
Verify artifact bytes using sha256sum -c SHA256SUMS before restoration.

Accepted fresh local original PCM/AUX/DTS/AC3 modules: 547/547 C,
548/548 direct DO/CE, zero warnings. Original images unchanged; workers
closed. This is STATIC C/CFG evidence, not complete silicon equivalence
or full RUSH hardware/firmware behavior recovery.
The separately expanded canonical Analyzer 565-function acceptance is
not yet confirmed. Do not delete historical projects or original images.
