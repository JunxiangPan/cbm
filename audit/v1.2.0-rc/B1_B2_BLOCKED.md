# B1 active / B2 blocked (claims fixed; artifact binding not fixed)

CBM v0.1.0 consumer status after CONTRACT v1.7.1 froze §5.1.

## B1 — CONTRACT_ACTIVE

- Contract: `contract-v1.7.1` / `209d75b4`; §5.1 is frozen and active.
- Subject: `package_id: "cbm"`; producer: `producer_id: "cbe"` / `"cbp"`.
- Tests: `tests/test_b1_identity.py` (6 tests) accept the pair; reject old
  `package_id: "cbe"/"cbp"` and producer mismatch; mixed reports exit 3
  `REPORT_IDENTITY_MISMATCH`.

## B2 — BLOCKED (claims/F3 fixed; artifact binding not)

Inputs:

- Real CBE report: `cbe-report.json`, sha256
  `6b4dc1efd8433535efe70d4de9337910aa537fbcc982ebba3a014284f27fc76e`;
  `package_id=cbm`, `producer_id=cbe`, `version/tag=v0.1.0`, `gate_status=PASS`.
- CBP 1.2.2 manifest: `cbm-quality-manifest.json`, sha256
  `b41798f07be4dda35e2afa1a810381bcd6f5025fb5d33f5c5a1054834a390c82`.

Progress:

- `identity_errors == []`.
- CBP claims gate PASS via `cbm-claims-manifest.json` /
  `cbm-claims-notes.md` (3/5; B2/B4 not claimed).
- Real F3 configs in `.cbp/config.json`:
  - binary: no binaries -> PASS N/A
  - docs: `cbm-docs-manifest.json` real hashes -> PASS
  - custom: rule `no-notimplemented` -> PASS
- `cbm-target-gate-with-f3.json`: claims/binary/encoding/docs/custom PASS;
  `CBP_GATE_STATUS=PASS`.

Remaining blocker: **exact artifact binding**.

- Required wheel `65174c9b…` is not retained.
- Required CBP manifest wheel `02bf8400…` is not retained.
- Fresh f605808 builds produced `94391185…` then
  `bf367708…`; neither is the required 94391185 and neither is adopted.
- No new CBM manifest is generated from a third hash; no mixed manifest/RC.

B2 stays **BLOCKED** until one exact retained artifact is bound to a
regenerated manifest and CBM's own gate exits 0.

Evidence: `cbe-report.json`, `cbm-claims-manifest.json`, `cbm-claims-notes.md`,
`cbm-target-gate-with-claims.json`, `cbm-target-gate-with-f3.json`,
`.cbp/config.json`, `cbm-docs-manifest.json`,
`b2-gate-failure.json`, `handoff/CBM_B2_CLAIMS_HANDOFF.md`.

## B4 — fail-closed only

Object `artifact_repository` shape is parsed and 12 boundary tests pass; the
overall CBM gate is not passed, so B4 is not PASS. CBE/CBS unification is not
claimed.

## B5 — fixed

CBS `fa1740f` emits `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`; the canary is
flipped and no `KNOWN_FAIL_SILENT` marker remains.

## No fake PASS

- No tag, GitHub Release, PyPI upload, or CBM 0.1.0 RC.
- `110 passed = 110 normal tests` (with the pinned CBS fixture).
