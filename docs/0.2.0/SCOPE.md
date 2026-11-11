# 0.2.0 scope

## In scope

- Pluggable evidence adapters (`cbm_attach.evidence`).
- Wheel and zip-bundle build-once artifacts.
- Bundle digest + manifest SHA256 in the sidecar report.
- Schema v2 with a frozen v1 compatibility schema.
- Unsigned in-toto Statement v1 + `verify-statement`.
- Live GitHub Release upload/readback in a private test repository.
- 0.1.1 regression and report readability.

## Out of scope / non-goals

- Runtime DLP, network traffic protection, endpoint agents.
- Replacing CBP or CBE; no gate re-execution.
- Forcing CBP/CBE/CBS as dependencies.
- Production release upload tests.
- Signing or a signed-attestation claim.
- A stable 0.2.0 release, tag, or PyPI upload.
- External adoption claims.
