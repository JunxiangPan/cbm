# cbm-attach 0.1.1

Status: **GitHub Release v0.1.1; PyPI blocked (no credentials).**

- Distribution: `cbm-attach`
- Version: `0.1.1`
- License: Apache-2.0
- Import package: `cbm_attach`
- Console script: `cbm-attach`
- Base source commit: `afa877d` plus the 0.1.1 release changes

## Artifacts

- `cbm_attach-0.1.1-py3-none-any.whl` sha256 `eadb94e95e7ca4cbe6fc7ffb27b0c05143379e5062ef51e8c69ee516a1efe7b3`
- `cbm_attach-0.1.1.tar.gz` sha256 `de87f6215e40e95b6ccf5570dba2ac0de70ea7228235795108e64631896f1a88`

## Changes

- Apache-2.0 LICENSE and wheel license metadata.
- Canonical `evidence_sha256` verification for upstream CBE/CBP; forged values exit 3 `EVIDENCE_HASH_MISMATCH`.
- `cbm-attach` distribution/console script and README quickstart.
- Uploader failure/digest/timeout tests; uploader coverage 94%.
- in-toto Statement output (`https://cbm.dev/attachment/v1`) and generic evidence adapters.

## Smoke

- Clean venv install: `cbm-attach 0.1.1`, `--help`, `import cbm_attach`, Apache-2.0 metadata.
- Normal verify: exit 0, `decision=UPLOAD`, `upload_status=NOT_UPLOADED`.
- Forged CBE `evidence_sha256`: exit 3 `EVIDENCE_HASH_MISMATCH`.
- in-toto Statement: `_type=https://in-toto.io/Statement/v1`,
  `predicateType=https://cbm.dev/attachment/v1`.

## Release

https://github.com/JunxiangPan/cbm/releases/tag/v0.1.1

## Boundaries

- No A-F live E2E claim; no full-product certification.
- PyPI upload was not performed (no trusted publisher/credentials).
- v0.1.0 tag and assets are untouched.
