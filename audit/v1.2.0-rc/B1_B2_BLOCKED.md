# B1 active / B2 blocked (claims fixed; artifact binding not fixed)

CBM v0.1.0 consumer status after CONTRACT v1.7.1 froze §5.1.

## B1 — CONTRACT_ACTIVE

- Contract: `contract-v1.7.1` / `209d75b4`; §5.1 is frozen and active.
- Subject: `package_id: "cbm"`; producer: `producer_id: "cbe"` / `"cbp"`.
- Tests: `tests/test_b1_identity.py` (6 tests) accept the pair; reject old
  `package_id: "cbe"/"cbp"` and producer mismatch; mixed reports exit 3
  `REPORT_IDENTITY_MISMATCH`.

## B2 — BLOCKED

Inputs:

- Real CBE report: `cbe-report.json`, sha256
  `6b4dc1efd8433535efe70d4de9337910aa537fbcc982ebba3a014284f27fc76e`;
  `package_id=cbm`, `producer_id=cbe`, `version/tag=v0.1.0`, `gate_status=PASS`.
- CBP 1.2.2 manifest: `cbm-quality-manifest.json`, sha256
  `b41798f07be4dda35e2afa1a810381bcd6f5025fb5d33f5c5a1054834a390c82`.
- CBM readiness claims: `cbm-claims-manifest.json` + `cbm-claims-notes.md`
  (3 PASS / 5 claims; B2/B4 explicitly not claimed).

Progress:

- `identity_errors == []`.
- CBP claims gate now **PASS**: `claims=3/5` (manifest + notes).
- CBM target gate with claims:
  `cbm-target-gate-with-claims.json`, `gate_status=PASS`;
  `claims` PASS, `encoding` PASS; binary/docs/custom/coverage/dependency/
  comments/upgrade still SKIPPED not configured.

Remaining blockers:

1. **Artifact binding**: the exact wheel `65174c9b…` (f605808) is not retained.
   Rebuilding f605808 now produces different wheels (`94391185…` in the latest
   build); CBP manifest wheel `02bf8400…` is also not retained. The instruction
   requires using one exact artifact; using a newly built wheel would mix
   hashes, so no new CBM manifest is generated.
2. **Other F3 gates**: even after claims PASS, CBM F3 still sees
   `binary`, `docs`, and `custom` as `SKIPPED (not configured)`. These need
   real configs or a contract decision; they were not waived.

B2 therefore stays **BLOCKED**; no CBM 0.1.0 RC, no tag/release.

Evidence: `cbe-report.json`, `cbm-claims-manifest.json`,
`cbm-claims-notes.md`, `cbm-target-gate-with-claims.json`,
`b2-gate-failure.json`, `b2-gate-failure.stdout.txt`; handoff
`handoff/CBM_B2_CLAIMS_HANDOFF.md`.

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
