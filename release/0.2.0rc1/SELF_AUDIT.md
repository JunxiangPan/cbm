# 0.2.0rc1 self-audit

Status: **candidate accepted for owner review; no tag, no PyPI.**

| Item | Value |
| --- | --- |
| version | `0.2.0rc1` |
| wheel | `cbm_attach-0.2.0rc1-py3-none-any.whl` |
| wheel sha256 | `ff437c6d55ab688517dfc01e3ca0e7313798e7bca821ca3162f4c519e2f78b92` |
| sdist | `cbm_attach-0.2.0rc1.tar.gz` |
| sdist sha256 | `2527193e85323178d2ab4b1d04f9d281eef5a962571c0c1a568e2371914dbb7a` |
| tests | 139 passed, 1 skipped (live E2E opt-in) |
| CI | 43100603891 ubuntu+windows green |

## Scope evidence

- Generic evidence adapter: `tests/test_generic_adapter.py`; no CBE/CBP needed.
- Zip-bundle positive/negative: `tests/test_zip_bundle.py`.
- Schema v2 + 0.1.1 v1 compatibility: `tests/test_schema_migration.py`.
- Unsigned in-toto Statement + verifier: `tests/test_intoto.py`.
- 0.1.1 report readability: clean-venv `statement` + `verify-statement` on
  `release/0.1.1/smoke/verify-report.json`.
- Clean venv: `cbm-attach 0.2.0rc1`, help; `cbe` and `cbp` not installed.

## Live E2E (test repo only)

- `JunxiangPan/cbm-e2e` private test repo
- release `e2e-v0.2.0rc1`; asset sha256
  `d666c328121e1d3808010f5ea239d1db17bf9eeb12ae666e03c84f94a0e48d73`
- production release untouched.

## Explicit limits

- in-toto Statement is **UNSIGNED**; no signature/attestation claim.
- No A-F live E2E claim; no stable 0.2.0 claim.
- Runtime DLP / CBP / CBE replacement are out of scope.
