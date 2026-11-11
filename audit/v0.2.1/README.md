# cbm-attach 0.2.1 — release audit

Status: **stable release published on GitHub and PyPI; CBF evidence attachment check recorded.**

| Item | Value |
| --- | --- |
| tag | `v0.2.1` at `7eaee9522121e9b21db94bb7180c1da05767731d` |
| GitHub Release | https://github.com/JunxiangPan/cbm/releases/tag/v0.2.1 |
| PyPI | https://pypi.org/project/cbm-attach/0.2.1/ (JSON 200) |
| pypi-publish | 43123043868 success |
| wheel | `cbm_attach-0.2.1-py3-none-any.whl` |
| wheel sha256 | `b84b90a8c884e3ed8495dc5ca4c9061545e36752c3a20d26bbd5fac89551847f` |
| sdist | `cbm_attach-0.2.1.tar.gz` |
| sdist sha256 | `b4ba27e7b864989c07775bc354efda6c3c57687b59993a2c9e8c682c42476b1a` |
| v0.2.0 tag | `261635e42806dc4569e8f3d7bfa4796bdd4de19f` (unchanged) |
| v0.1.1 tag | `573640fa2eaae98abb4690ee515f79d85315f111` (unchanged) |
| v0.1.0 tag | `89f94440787da29aa63f9a6a275f34559199a54e` (unchanged) |

## Verification

- PyPI JSON 200; wheel/sdist digests match GitHub Release and `release/0.2.1`.
- Clean venv `pip install cbm-attach==0.2.1`; `cbm-attach 0.2.1`; semantic CLI available.
- No CBE/CBP installed; no CBF/CBP/CBE import.
- `semantic-verdict/v1` schema/hash validation tests pass; 145 passed, 1 skipped.
- CBF evidence external check: attachment read PASS; CBF gate NOT_RUN; semantic model NOT_RUN; source result reported separately.
- No signed attestation or A-F full live claim.

## Explicit boundaries

- `semantic-verdict/v1` is an optional standalone attachment; CBM 0.1.1/0.2.0 sidecar report contract unchanged.
- No semantic model was run.
- CBF gate was not run; no CBM CBF PASS exists.
