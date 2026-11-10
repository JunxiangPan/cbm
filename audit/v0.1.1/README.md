# cbm-attach 0.1.1 — release audit

Status: **PUBLISHED on GitHub Releases and PyPI; uploads verified.**

| Item | Value |
| --- | --- |
| tag | `v0.1.1` at `573640fa2eaae98abb4690ee515f79d85315f111` |
| v0.1.0 tag | `89f94440787da29aa63f9a6a275f34559199a54e` (unchanged) |
| GitHub Release | https://github.com/JunxiangPan/cbm/releases/tag/v0.1.1 |
| PyPI | https://pypi.org/project/cbm-attach/0.1.1/ (JSON 200) |
| PyPI workflow | [42741008466](https://github.com/JunxiangPan/cbm/actions/runs/42741008466) success |
| wheel | `cbm_attach-0.1.1-py3-none-any.whl` |
| wheel sha256 | `eadb94e95e7ca4cbe6fc7ffb27b0c05143379e5062ef51e8c69ee516a1efe7b3` |
| sdist | `cbm_attach-0.1.1.tar.gz` |
| sdist sha256 | `de87f6215e40e95b6ccf5570dba2ac0de70ea7228235795108e64631896f1a88` |

## Verification

- PyPI JSON HTTP 200; both file digests match `release/0.1.1`.
- Clean venv `pip install cbm-attach==0.1.1`; `cbm-attach --version` = 0.1.1; `--help` and `import cbm_attach` work.
- METADATA: `Name: cbm-attach`, `Version: 0.1.1`, `License: Apache-2.0`, entry point `cbm-attach`.
- Forged upstream CBE evidence hash exits 3 `EVIDENCE_HASH_MISMATCH`.
- in-toto Statement JSON parses; `predicateType=https://cbm.dev/attachment/v1`.
- Test suite: 131 passed (ubuntu/windows); latest code CI 42741058166.
- No A-F live E2E or full-product certification claimed.
- No tag move, no asset replacement, no re-upload.
