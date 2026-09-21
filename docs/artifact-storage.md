# Artifact storage

The current GitHub MCP transport rejects large binary payloads. Immutable firmware evidence is therefore stored as base64 text parts.

This is a transport representation only. The decoded bytes are canonical.

`firmware/artifacts.json` records:
- output filename;
- exact byte size;
- SHA-256;
- ordered base64 part files.

`tools/materialize_artifacts.py` decodes every part and fails unless the reconstructed size and SHA-256 match the original evidence.

The representation can later be replaced by direct binary or Git LFS storage without changing any canonical hashes.
