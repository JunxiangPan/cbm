# cbm-attach 0.2.0 — release audit

Status: **stable release published on GitHub and PyPI; uploads verified.**

| Item | Value |
| --- | --- |
| tag | `v0.2.0` at `261635e42806dc4569e8f3d7bfa4796bdd4de19f` |
| GitHub Release | https://github.com/JunxiangPan/cbm/releases/tag/v0.2.0 |
| PyPI | https://pypi.org/project/cbm-attach/0.2.0/ (JSON 200) |
| pypi-publish | [43103291928](https://github.com/JunxiangPan/cbm/actions/runs/43103291928) success |
| wheel | `cbm_attach-0.2.0-py3-none-any.whl` |
| wheel sha256 | `bc3d68ae0c3db5cb2dce4ae4d68d1b8c771b90707fca46212be88b1bf14a50bc` |
| sdist | `cbm_attach-0.2.0.tar.gz` |
| sdist sha256 | `dd2c2af9be6da7096b52cf09f248f7529201aa4bbacd2ed61cb47307f7a6eccb` |
| v0.1.0 tag | `89f94440787da29aa63f9a6a275f34559199a54e` (unchanged) |
| v0.1.1 tag | `573640fa2eaae98abb4690ee515f79d85315f111` (unchanged) |

## Verification

- PyPI JSON 200; both file digests match the GitHub Release and `release/0.2.0`.
- Clean venv `pip install cbm-attach==0.2.0`; `cbm-attach 0.2.0`; help/import work.
- No CBE/CBP installed.
- 0.1.1 report readable via v1 schema and clean-venv `statement`/`verify-statement`.
- 139 passed, 1 skipped; main CI 43103259730.
- Live upload E2E only private `JunxiangPan/cbm-e2e`.

## Explicit boundaries

- in-toto Statement is **UNSIGNED**; no signed-attestation claim.
- No A-F full live PASS or full-product certification.
- No runtime DLP, CBP/CBE replacement, or forced CBS dependency.
- No tag/asset move or re-upload for v0.1.0/v0.1.1/v0.2.0.
