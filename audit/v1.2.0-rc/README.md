# CBM v0.1.0 — CBP 1.2.2 audit package

Status: **STOPPED FOR HUMAN AUDIT**. No tag, GitHub Release, PyPI upload, or
CBM PASS claim was made. No CBS/CBE/CBP/CBC repository was modified.

## Identity

| Item | Value |
| --- | --- |
| CBM repository | https://github.com/JunxiangPan/cbm (public) |
| CBM branch | `main` |
| CBM manifest target commit | `f71d3b5` (object repository support) |
| CBM audit commit | `304d4e7` |
| CBM tag / release | none |
| CBP 1.2.2 release | `v1.2.2` / `d4bfefb` |
| CBP 1.2.2 publish state | released (tag, GitHub Release, PyPI) |
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
| [42595276523](https://github.com/JunxiangPan/cbm/actions/runs/42595276523) | `ae0ad13` | success: **102/102 on ubuntu-latest and windows-latest** (B1/B2 readiness + B4 boundary) |
| [42607873304](https://github.com/JunxiangPan/cbm/actions/runs/42607873304) | `503986b` | success: **102/102 on ubuntu-latest and windows-latest** (official CBP 1.2.0 manifest) |
| [42639676069](https://github.com/JunxiangPan/cbm/actions/runs/42639676069) | `22831d6` | success: **105/105 on ubuntu-latest and windows-latest** (CBP 1.2.2 object manifest) |
| [42645029320](https://github.com/JunxiangPan/cbm/actions/runs/42645029320) | `0f84aae` | success: **108/108 on ubuntu-latest and windows-latest** (object B4 boundaries) |
| [42647681396](https://github.com/JunxiangPan/cbm/actions/runs/42647681396) | `8b5c52b` | success: **109/109 on ubuntu-latest and windows-latest** (B4 fail-closed + B2 object readiness) |
| [42656004220](https://github.com/JunxiangPan/cbm/actions/runs/42656004220) | `304d4e7` | success: **110/110 on ubuntu-latest and windows-latest** (different-owner object cross) |

**110 passed = 110 normal tests. No `KNOWN_FAIL_SILENT` canary remains.** The B5
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

Full 13-rule run (official v1.2.2, `d4bfefb`, read-only archive):

```text
PASS 12, WARN 1 (CBP-DOC-001, 12 findings), FAIL 0
CBP-BODY-001 PASS
CBP_V12_RESULT=WARN rules=13 blocking_failed=false
exit 0
```

CBP-DEBT-001 was a true positive on `docs/V17_BLOCKERS.md` (the word `FIXED`
without a file); it now passes after the claim cites
`tests/test_known_fail_silent.py`. DOC warnings are 1.2.2 warning-only, not
waived.

## Encoding fix

`b5-probe.stdout.txt` and `b5-probe-declared.stdout.txt` were GBK bytes; both
were decoded as GBK and re-encoded as UTF-8 without changing the text. A scan of
the repository found no other non-UTF-8 text file. The official CBP 1.2.0 gate
now reports:

```text
encoding: PASS encoding=63 UTF-8 files without BOM
```

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

## B3 — FIELD_LEVEL_COMPLETE (CBP 1.2.2 object manifest)

Official CBP 1.2.2 (tag `v1.2.2`, commit `d4bfefb`) target gate on CBM
`f71d3b5`:

```text
file cbm-target-gate.json
sha256 f58ba9a4d38c3a66779c6a609f4f17fd9880c5cd682f071c74e40a4c1b4ddcd7
package_id cbm, producer_id cbp, version v0.1.0
gate_status PASS
encoding PASS (63 UTF-8 files without BOM)
```

Generated manifest:

```text
file cbm-quality-manifest.json
sha256 b41798f07be4dda35e2afa1a810381bcd6f5025fb5d33f5c5a1054834a390c82
schema_version "1"
package_id cbm, producer_id cbp, version v0.1.0
gate_status PASS
body_hash_scope base
release_body_hash 97784c54872b32f89ac1f0ecb2300b51c1c625d31fd6ebb322940e8bb44963c2
artifact_repository {"repository": "JunxiangPan/cbm",
                     "run_id": "local-cbm-build-once",
                     "artifact_name": "cbm-build-once"}
artifact_repository.repository JunxiangPan/cbm
wheel sha256 02bf840016f5a2630c70ab42286c3ea47c0091c5efb77c0429c3060c0bee8015
sdist sha256 89379c009f3c0cfca072ceaf861e03923e00cbe15e617c55846ed7ec78fbad6e
evidence_sha256 84ea0b081a29dcc54fb92a74fb68eb178d576fc7267d04aa5b30c7612ceaa57f
ci_commit_sha f71d3b53df8f3fd8b1ee51ef1698f58392bc5c59
```

The base body is `cbm-base-body.md`, assembled from the CBM README and labelled
as such; it is not an official GitHub Release body. `load_report` returns PASS;
missing scope -> exit 2 `MISSING_BODY_HASH_SCOPE`; `full` -> exit 2
`BODY_HASH_SCOPE_UNSUPPORTED`. Tests: 4 passed (`tests/test_b3_cbp_rc.py`).

The older `6da7e848…` (CBP 1.2.0) manifest is **superseded** and retained at
`cbm-quality-manifest-1.2.0.json` as history. The older `bc5461e6…` RC-era
manifest is also historical.

**B3 field-level is complete. B2 is still blocked**: there is no real CBE
report with `package_id: "cbm"`; CBM does not synthesize it.

## B4 — FAIL_CLOSED_ONLY

| Case | Result |
| --- | --- |
| object cross-repository (different owner or repo) | exit 2 `ARTIFACT_REPOSITORY_MISMATCH` |
| object missing `artifact_repository`/`repository` | exit 2 `ARTIFACT_REPOSITORY_MISMATCH` |
| object same repository (exact) | continues to `UPLOAD_PENDING` |
| object same repository (case-insensitive) | continues to `UPLOAD_PENDING` |

Tests: 12 passed (5 legacy/string + 7 object). CBE/CBS repositories are not unified; B4 is not complete.

## B1 CONTRACT_ACTIVE / B2 blocked

See [`B1_B2_BLOCKED.md`](B1_B2_BLOCKED.md). No fake PASS:

- **B1 CONTRACT_ACTIVE** — `contract-v1.7.1` / `209d75b4` freezes §5.1;
  `tests/test_b1_identity.py` (6 tests) accepts `package_id: "cbm"` with
  `producer_id: "cbe"/"cbp"`; old-field mixing exits 3
  `REPORT_IDENTITY_MISMATCH`. This is consumer-side active, not a full train
  PASS.
- **B2 readiness** — `tests/test_b2_readiness.py` (4 tests): the synthetic CBE
  fixture (`tests/fixtures/cbe-cbm-scoped.synthetic.json`) is explicitly marked
  `not_upstream_evidence`; it validates the schema/identity path together with
  the real CBP 1.2.2 CBM manifest. There is still no real CBE report with
  `package_id: "cbm"`, so B2 remains blocked.
- B4 remains fail-closed only.

## Reproduce

```bash
cd D:\qq苏瑾言大肥鱼\cbm
python -m pytest                                  # 110 passed (CBS present)
python tools/check_b5.py --check-upstream         # STATUS=B5_MAYBE_FIXED; exit 0
python tools/check_b5.py --check-upstream --declared-cbm
python -m pytest tests/test_b3_cbp_rc.py          # 4 passed
python -m pytest tests/test_b1_identity.py        # 6 passed
python -m pytest tests/test_b2_readiness.py       # 3 passed (synthetic)
python -m pytest \
  tests/test_exit_codes.py::test_cross_repository_artifact_exits_2 \
  tests/test_exit_codes.py::test_cross_repository_different_repo_exits_2 \
  tests/test_exit_codes.py::test_missing_artifact_repository_exits_2 \
  tests/test_exit_codes.py::test_same_artifact_repository_continues \
  tests/test_exit_codes.py::test_same_repository_case_insensitive_continues \
  tests/test_exit_codes.py::test_object_artifact_repository_same_continues \
  tests/test_exit_codes.py::test_object_artifact_repository_cross_exits_2 \
  tests/test_exit_codes.py::test_object_artifact_repository_missing_repository_exits_2 \
  tests/test_exit_codes.py::test_object_artifact_repository_same_exact_continues \
  tests/test_exit_codes.py::test_object_artifact_repository_missing_field_exits_2 \
  tests/test_exit_codes.py::test_object_artifact_repository_empty_repository_exits_2 \n  tests/test_exit_codes.py::test_object_artifact_repository_different_owner_same_repo_exits_2  # 12 passed
```

The CBP runs used a read-only `git archive` of the official `v1.2.2`
commit `d4bfefb`; no CBP working tree was modified.

## No publish

No tag, no GitHub Release, no PyPI upload, no release asset. Human audit is
required before any of those actions.
