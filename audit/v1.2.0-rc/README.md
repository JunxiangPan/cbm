# CBM v0.1.0 — CBP 1.2.0 RC audit package

Status: **STOPPED FOR HUMAN AUDIT**. No tag, GitHub Release, PyPI upload, or
CBM PASS claim was made. No CBS/CBE/CBP/CBC repository was modified.

## Identity

| Item | Value |
| --- | --- |
| CBM repository | https://github.com/JunxiangPan/cbm (public) |
| CBM branch | `main` |
| CBM code commit | `3458cb81ffb30a71d6606830e8d8276e993d6ae4` |
| CBM tag / release | none |
| CBP RC code | `855fed7` (`1.2.0-dev`) |
| CBP 1.2.0 publish state | not tagged, not released, PyPI 404 |
| CBS B5 fix | `fa1740fe03590ec9adfc9ab57cf1485bdc3bea87` (`v1.7.0-integration`) |

## CI

| Run | Commit | Result |
| --- | --- | --- |
| [42543756142](https://github.com/JunxiangPan/cbm/actions/runs/42543756142) | `beffaef` | failure: PyYAML missing; fixed by `d03c439` |
| [42543902925](https://github.com/JunxiangPan/cbm/actions/runs/42543902925) | `d03c439` | success: 84/84 |
| [42544444367](https://github.com/JunxiangPan/cbm/actions/runs/42544444367) | `6c77bc7` | success: 91/91 |
| [42544797487](https://github.com/JunxiangPan/cbm/actions/runs/42544797487) | `65ae31f` | success: 91/91 (audit docs) |
| [42544980840](https://github.com/JunxiangPan/cbm/actions/runs/42544980840) | `45c49bc` | success: 91/91 (final old audit) |
| [42593726644](https://github.com/JunxiangPan/cbm/actions/runs/42593726644) | `3458cb8` | success: **91/91 on ubuntu-latest and windows-latest** (B5 flip + CBM manifest) |

**102 passed = 102 normal tests. No `KNOWN_FAIL_SILENT` canary remains.** The B5
canary was flipped to assert the fixed behavior.

## CBP-CI-001 — PASS

Before (CBP 1.2.0 E2E matrix, CBM `00d984e`):

```text
CBP-CI-001 TEST_ROOTS_IN_CI: FAIL(1)
tests: test root is not executed by any workflow
```

After the CBM CI workflow:

```text
CBP-CI-001 TEST_ROOTS_IN_CI: PASS
CBP_V12_RESULT=PASS rules=1 blocking_failed=false warning_failed=false
exit 0
```

Full 12-rule run (`855fed7`, read-only archive):

```text
PASS 11, WARN 1 (CBP-DOC-001, 12 findings), FAIL 0
CBP_V12_RESULT=WARN rules=12 blocking_failed=false
exit 0
```

CBP-DEBT-001 was a true positive on `docs/V17_BLOCKERS.md` (the word `FIXED` without a file);
it now passes after the claim cites `tests/test_known_fail_silent.py`. DOC
warnings are 1.2.0 warning-only, not waived.

## B5 — FIXED (`tests/test_known_fail_silent.py`), canary flipped

CBS `fa1740f` synthesizes a dedicated `## CBM` section for a missing CBM:

```text
## CBM
- CBM: NOT_UPLOADED
  - cbm_gate_status: `NOT_UPLOADED`
  - upload_status: `NOT_UPLOADED`
  - reason: `EVIDENCE_ABSENT`
  - declared_attached: `false`
```

With `declared_components: ["cbm"]` it emits the exact phrase
`declared as attached but not uploaded`.

Evidence:

- `b5-probe.stdout.txt` / `b5-probe-declared.stdout.txt` — `STATUS=B5_MAYBE_FIXED`
- `b5-fixed-body.md` / `b5-fixed-body-declared.md` — rendered output
- `tests/test_known_fail_silent.py` — flipped; 1 passed
- `tools/check_b5.py --check-upstream` is green; `KNOWN_FAIL_SILENT` now means
  a regression and fails the test.

## B3 — FIELD_LEVEL_COMPLETE

Real CBP 1.2.0 RC `855fed7` external-package manifest:

```text
file cbp-1.2.0-cbm-manifest.json
sha256 bc5461e61a4167dfae21fdf12fe169fa8339c7f20eac09f861799d89926196c1
package_id cbm, producer_id cbp, version v0.1.0
body_hash_scope base
release_body_hash b4fa95034d31a84d5fc60a9773852e5ffd002624987947b903ad99ff21e3f077
wheel sha256 a6a812cf6e99a51211ac30b4ef3574ecc7851ff05d3095406a325d1aa8596362
sdist sha256 3fdb074f7739ff9e14b1bb51b6d43561a9e01b5f1395ac6fc1536295ff690d50
evidence_sha256 0edf31e8757d7c6f577efa2a3472c7b33836db9bdc14685634264c201b07732a
```

`load_report` accepts all B3 fields; missing scope -> exit 2
`MISSING_BODY_HASH_SCOPE`; `full` -> exit 2 `BODY_HASH_SCOPE_UNSUPPORTED`.
Tests: 4 passed (`tests/test_b3_cbp_rc.py`).

**B3 field-level is complete. B2 is still blocked**: the CBE side has no real
report with `package_id: "cbm"`; CBM does not synthesize it.

## B4 — FAIL_CLOSED_ONLY

| Case | Result |
| --- | --- |
| cross-repository `artifact_repository` | exit 2 `ARTIFACT_REPOSITORY_MISMATCH` |
| missing `artifact_repository` | exit 2 `ARTIFACT_REPOSITORY_MISMATCH` |
| same repository | continues to `UPLOAD_PENDING` |

Tests: 3 passed. CBE/CBS repositories are not unified; B4 is not complete.

## B1 / B2 — blocked

See [`B1_B2_BLOCKED.md`](B1_B2_BLOCKED.md). No fake PASS:

- B1 §5.1 is not in CONTRACT.md; producer `package_id` exits 3.
- B2 no real CBE report with `package_id: "cbm"`; the CBP side exists.
- B4 remains fail-closed only.

## Reproduce

```bash
cd D:\qq苏瑾言大肥鱼\cbm
python -m pytest                                  # 102 passed (CBS present)
python tools/check_b5.py --check-upstream         # STATUS=B5_MAYBE_FIXED; exit 0
python tools/check_b5.py --check-upstream --declared-cbm
python -m pytest tests/test_b3_cbp_rc.py          # 4 passed
python -m pytest \
  tests/test_exit_codes.py::test_cross_repository_artifact_exits_2 \
  tests/test_exit_codes.py::test_missing_artifact_repository_exits_2 \
  tests/test_exit_codes.py::test_same_artifact_repository_continues  # 3 passed
```

The CBP runs used a read-only `git archive` of `855fed7`; no CBP working tree
was modified.

## No publish

No tag, no GitHub Release, no PyPI upload, no release asset. Human audit is
required before any of those actions.
