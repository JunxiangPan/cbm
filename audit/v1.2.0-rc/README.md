# CBM v0.1.0 — CBP 1.2.0 RC audit package

Status: **STOPPED FOR HUMAN AUDIT**. No tag, GitHub Release, PyPI upload, or
CBM PASS claim was made. No CBS/CBE/CBP/CBC repository was modified.

## Identity

| Item | Value |
| --- | --- |
| CBM repository | https://github.com/JunxiangPan/cbm (public) |
| CBM branch | `main` |
| CBM code commit | `6c77bc764edd79f31cb3baa80d0e4bd2fe7d63f1` |
| CBM audit package commit | `65ae31f` |
| CBM tag / release | none |
| CBP RC code used for gate evidence | `5da8b87` (`1.2.0-dev`) |
| CBP 1.2.0 publish state | not tagged, not released, PyPI 404 |
| CBS pin for B5 canary | `88ec90fcafd1548b7810d0c446899ecd75f6b95a` |

The local CBP audit package records a later candidate (`9ee52fb`) that
supersedes `5da8b87`; this audit uses `5da8b87` for the CBM gate evidence and
does **not** claim that `5da8b87` is the final CBP 1.2.0 build.

## CI

| Run | Commit | Result |
| --- | --- | --- |
| [42543756142](https://github.com/JunxiangPan/cbm/actions/runs/42543756142) | `beffaef` | failure: PyYAML missing; fixed by `d03c439` |
| [42543902925](https://github.com/JunxiangPan/cbm/actions/runs/42543902925) | `d03c439` | success: 84 passed on ubuntu-latest and windows-latest |
| [42544444367](https://github.com/JunxiangPan/cbm/actions/runs/42544444367) | `6c77bc7` | success: **91 passed** on ubuntu-latest and windows-latest |
| [42544797487](https://github.com/JunxiangPan/cbm/actions/runs/42544797487) | `65ae31f` | success: 91 passed on ubuntu-latest and windows-latest (audit docs) |

`91 passed = 90 normal tests + 1 KNOWN_FAIL_SILENT canary`. The canary asserts
that the B5 defect exists; it is not a PASS for B5.

## CBP-CI-001 — before and after

Before (CBP 1.2.0 E2E matrix, CBM `00d984e`):

```text
CBP-CI-001 TEST_ROOTS_IN_CI: FAIL(1)
tests: test root is not executed by any workflow
```

After the CBM CI workflow and the test run:

```text
$ python -m cbp.cli --root <cbm> --v12 --v12-only CBP-CI-001
CBP-CI-001 TEST_ROOTS_IN_CI: PASS
CBP_V12_RESULT=PASS rules=1 blocking_failed=false warning_failed=false
exit 0
```

Full 12-rule run against CBM (`5da8b87`, read-only), captured at code commit
`6c77bc7` before this audit package's docs-only commit:

```text
CBP_V12_RESULT=WARN rules=12 blocking_failed=false warning_failed=true
PASS 11, WARN 1 (CBP-DOC-001, 12 findings), FAIL 0
```

The DOC warnings are known 1.2.0 warning-only findings (documentation paths that
resolve only in other repositories or at runtime). They are not blocking in
1.2.0 and are not being waived here.

## B3 — PARTIAL (real CBP 1.2.0 RC-era manifest, field-level)

Real manifest used:

```text
cbp-action-release/quality-manifest.json
sha256 53d80bb1a73b91b7205f4bc4b96817f7d83ae341164fb10ba1464372801d55ba
package_id cbp, producer_id cbp, version v1.2.0
body_hash_scope base
release_body_hash 6cca0e560af9a1239b619bb6cb8d1d2b90e102e51cd058fbb83f00114da8a09b
manifest wheel sha256 40ae798a9e480383b7069f8a488225ea8ac806e8dd2cc9120abf9fdb5a76b3ba
manifest sdist sha256 7a9b5db62229ecaf3073ed62c556080583f2a5c283b729a8297ded308423c2fb
manifest ci_commit_sha 904494452458bde3bb4d2174abc2664413e41100
```

Results:

| Scope | CBM result |
| --- | --- |
| `base` | accepted (`release_body_hash` + `body_hash_scope` pass) |
| missing | exit 2 `MISSING_BODY_HASH_SCOPE` |
| `full` | exit 2 `BODY_HASH_SCOPE_UNSUPPORTED` |

Tests: 4 passed (`tests/test_b3_cbp_rc.py`). **B3 is PARTIAL**: the manifest is
`package_id: "cbp"` / `version: "v1.2.0"`, not a CBM-scoped or attested CBM
manifest. Full B3 remains blocked by B1/B2. The manifest is RC-era evidence, not
proof that the attested CBP 1.2.0 wheel was consumed by CBM.

## B4 — FAIL_CLOSED_ONLY

| Case | CBM result |
| --- | --- |
| cross-repository `artifact_repository` | exit 2 `ARTIFACT_REPOSITORY_MISMATCH` |
| missing `artifact_repository` | exit 2 `ARTIFACT_REPOSITORY_MISMATCH` |
| same repository | continues to `UPLOAD_PENDING` |

Tests: 3 passed (`tests/test_exit_codes.py`). This is **not** B4 completion:
CBE/CBS artifacts are still not uploaded to one repository. CBM only refuses a
cross-repository manifest and cannot unify the train alone.

## B1 / B2 / B5 — blocked

See [`B1_B2_B5_BLOCKED.md`](B1_B2_B5_BLOCKED.md). No fail-silent behavior is
being converted into PASS:

- B1 §5.1 is not in CONTRACT.md; producer `package_id` exits 3.
- B2 no CBM-scoped report exists; the B3 manifest is `package_id: "cbp"`.
- B5 CBS body generator still renders `- none`; `KNOWN_FAIL_SILENT` canary.

## Reproduce

```bash
cd D:\qq苏瑾言大肥鱼\cbm
python -m pytest                                  # 90 passed, 1 skipped locally without CBS
CBS_REPO=<pinned-cbs-checkout> python -m pytest   # 91 passed
python tools/check_b5.py --check-upstream         # STATUS=KNOWN_FAIL_SILENT; exit 0
python -m pytest tests/test_b3_cbp_rc.py          # 4 passed
python -m pytest \
  tests/test_exit_codes.py::test_cross_repository_artifact_exits_2 \
  tests/test_exit_codes.py::test_missing_artifact_repository_exits_2 \
  tests/test_exit_codes.py::test_same_artifact_repository_continues  # 3 passed
```

The CBP commands used a read-only `git archive` of `5da8b87`; no CBP working
tree was modified.

## No publish

No tag, no GitHub Release, no PyPI upload, no release asset. Human audit is
required before any of those actions.
