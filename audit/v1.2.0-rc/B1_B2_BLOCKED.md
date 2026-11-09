# B1 active / B2 & B4 uploaded and verified

CBM v0.1.0 consumer status after CONTRACT v1.7.1 froze §5.1.

## B1 — CONTRACT_ACTIVE

- Contract: `contract-v1.7.1` / `209d75b4`; §5.1 is active.
- Subject `package_id: "cbm"`; producer `producer_id: "cbe"` / `"cbp"`.
- Tests: 6 identity tests; old-field mixing exits 3
  `REPORT_IDENTITY_MISMATCH`.

## B2 — GATE_VERIFIED

Inputs:

- Real CBE report `cbe-report.json`, sha256
  `6b4dc1efd8433535efe70d4de9337910aa537fbcc982ebba3a014284f27fc76e`;
  `package_id=cbm`, `producer_id=cbe`, v0.1.0 PASS.
- CBP 1.2.2 manifest `cbm-quality-manifest.json`, sha256
  `0e0d37bd083afc0a5e868d654d4b8808f9f91c91f45dd20d4dbad029945e7a9b`;
  schema `"1"`, object repo, base, PASS.
- Exact artifact: fresh f605808 build, permanently retained:
  wheel `72254704f5dc88688056fd3e4dac481edfa45f13e4bf5ae1aa8810cdaa48f45b`,
  sdist `6a7b6fe360b86e75a4c7bba0a2765f50e2195263735825e251ec91404927dd81`.
  Build record `cbm-build-once.json`.

Validation:

```text
identity_errors []
claims PASS 3/5
binary PASS (N/A, no binaries)
docs PASS (3 files)
custom PASS (1 rule)
artifact hash matches CBP manifest
CBM_VERIFY exit 0
cbm_gate_status=NOT_UPLOADED
decision=UPLOAD
```

CBM upload report: `cbm_gate_status=PASS`, `upload_status=UPLOADED_VERIFIED`.
Release https://github.com/JunxiangPan/cbm/releases/tag/v0.1.0.

## B4 — GATE_VERIFIED

Object `artifact_repository` matches `JunxiangPan/cbm`; 12 boundary tests
pass; cross/missing exit 2, same continues. CBE/CBS unification is not claimed.

## B5 — fixed

CBS `fa1740f` emits `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`; canary flipped.

## Release

`release/0.1.0/` contains the exact wheel/sdist, manifest, gate report, claims,
F3 configs, BUILD_ONCE and CBE report. GitHub Release v0.1.0 is published;
assets verified. No PyPI; CBS v1.7.0 tag unchanged.

## No fake PASS

- `110 passed = 110 normal tests` (pinned CBS).
- No tag, GitHub Release, PyPI upload, or upload PASS.
