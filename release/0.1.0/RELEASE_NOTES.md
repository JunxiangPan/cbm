# CBM 0.1.0 — sidecar attachment

Status: **UPLOADED_VERIFIED**. Scope: CBM sidecar attachment only.

## Approved artifacts (no rebuild/repack)

- `cbm_attach-0.1.0-py3-none-any.whl`
  sha256 `72254704f5dc88688056fd3e4dac481edfa45f13e4bf5ae1aa8810cdaa48f45b`
- `cbm_attach-0.1.0.tar.gz`
  sha256 `6a7b6fe360b86e75a4c7bba0a2765f50e2195263735825e251ec91404927dd81`

## Evidence

- CBP 1.2.2 manifest: `0e0d37bd083afc0a5e868d654d4b8808f9f91c91f45dd20d4dbad029945e7a9b`
- CBE report: `6b4dc1efd8433535efe70d4de9337910aa537fbcc982ebba3a014284f27fc76e`
- CBM upload report: `cbm_gate_status=PASS`, `upload_status=UPLOADED_VERIFIED`
- Exact wheel/sdist digests verified against the GitHub Release assets.

## Release

- https://github.com/JunxiangPan/cbm/releases/tag/v0.1.0
- assets verified against the local exact wheel/sdist.

## Upload decision

- `UPLOAD_APPROVED` / `UPLOADED_VERIFIED` / `cbm_gate_status=PASS`
- `upload-decision.json` is final; `upload-decision.pre-upload.json` is historical.

## Boundaries

- No rebuild, no repack, no PyPI upload.
- CBS v1.7.0 tag is not moved.
- A-F live E2E is not claimed.
- This is not a claim that the complete CBM product is finished.
