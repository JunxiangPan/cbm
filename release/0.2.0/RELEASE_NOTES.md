# cbm-attach 0.2.0

Status: **stable release (owner accepted); sidecar attachment only.**

- wheel `cbm_attach-0.2.0-py3-none-any.whl` sha256 `bc3d68ae0c3db5cb2dce4ae4d68d1b8c771b90707fca46212be88b1bf14a50bc`
- sdist `cbm_attach-0.2.0.tar.gz` sha256 `dd2c2af9be6da7096b52cf09f248f7529201aa4bbacd2ed61cb47307f7a6eccb`
- Distribution `cbm-attach`, import `cbm_attach`, console `cbm-attach`.
- Scope: generic evidence adapters; wheel + zip-bundle; schema v2; unsigned in-toto Statement v1.

## Compatibility

- 0.1.1 reports remain readable under `schemas/cbm-report-v1.schema.json`.
- 0.2.0 reports use schema_version `"2"` and add `artifact_type` /
  `bundle_manifest_sha256`; no 0.1.1 field is silently removed.
- `v0.1.0` and `v0.1.1` tags/releases are unchanged.

## in-toto

The emitted Statement is **UNSIGNED**. It has no signatures and makes no
signed-attestation claim. `cbm-attach verify-statement` verifies structure and
report binding only.

## Live E2E

Live upload/readback was performed only against the private test repository
`JunxiangPan/cbm-e2e` (test release `e2e-v0.2.0rc1`). No production release was
used for live testing.

## Non-goals / limits

- No runtime DLP, network traffic protection, or CBP/CBE replacement.
- No forced CBS/CBE/CBP dependency.
- No A-F live E2E claim and no full-product certification.
- No signed attestation.
