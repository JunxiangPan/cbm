# CBM v0.1.0 — CBP 1.2.2 audit package

Status: **CBM 0.1.0 sidecar released and upload-verified.** CBM GitHub Release
`v0.1.0` is published; no PyPI upload; no CBS/CBE/CBP/CBC repository was
modified.

## Identity

| Item | Value |
| --- | --- |
| CBM repository | https://github.com/JunxiangPan/cbm (public) |
| CBM branch | `main` |
| CBM manifest target commit | `f71d3b5` (b41798 manifest) |
| CBE-validated CBM source | `f605808` (rebuilt wheel 65174c9b…) |
| CBM audit commit | `4c4505d` |
| CBM tag / release | none |
| CBP 1.2.2 release | `v1.2.2` / `d4bfefb` |
| CBP 1.2.2 publish state | released (tag, GitHub Release, PyPI) |
| CBS B5 fix | `fa1740fe03590ec9adfc9ab57cf1485bdc3bea87` (`v1.7.0-integration`) |
| CBE real report | `6b4dc1efd8433535efe70d4de9337910aa537fbcc982ebba3a014284f27fc76e` |

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
| [42660486530](https://github.com/JunxiangPan/cbm/actions/runs/42660486530) | `1bbe892` | success: **110/110 on ubuntu-latest and windows-latest** (B2 real-report gate failure evidence) |
| [42663439528](https://github.com/JunxiangPan/cbm/actions/runs/42663439528) | `a974011` | success: **110/110 on ubuntu-latest and windows-latest** (claims handoff/artifact blocker) |
| [42665717371](https://github.com/JunxiangPan/cbm/actions/runs/42665717371) | `f414b78` | success: **110/110 on ubuntu-latest and windows-latest** (real F3 config; artifact still blocked) |
| [42720843255](https://github.com/JunxiangPan/cbm/actions/runs/42720843255) | `2d87412` | success: **110/110 on ubuntu-latest and windows-latest** (exact artifact B2 gate verified) |
| [42723720005](https://github.com/JunxiangPan/cbm/actions/runs/42723720005) | `c593251` | success: **110/110 on ubuntu-latest and windows-latest** (sidecar upload verified) |
| [42725782667](https://github.com/JunxiangPan/cbm/actions/runs/42725782667) | `4c4505d` | success: **110/110 on ubuntu-latest and windows-latest** (final upload decision) |

**128 passed = 128 normal tests. No `KNOWN_FAIL_SILENT` canary remains.** The B5
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

## B3 — FIELD_LEVEL_COMPLETE (exact artifact)

Official CBP 1.2.2 target gate on CBM `f605808` with real claims/F3 configs:

```text
file cbm-target-gate.json
sha256 af9e4f45b44a96ccabda9bc08606fc2857c14999e1cb3c7edfa543e2d631e826
package_id cbm, producer_id cbp, version v0.1.0
gate_status PASS; claims/binary/encoding/docs/custom PASS
```

Manifest:

```text
file cbm-quality-manifest.json
sha256 0e0d37bd083afc0a5e868d654d4b8808f9f91c91f45dd20d4dbad029945e7a9b
schema_version "1"; gate_status PASS; body_hash_scope base
release_body_hash 97784c54872b32f89ac1f0ecb2300b51c1c625d31fd6ebb322940e8bb44963c2
artifact_repository {repository: JunxiangPan/cbm, run_id: local-cbm-build-once,
                     artifact_name: cbm-build-once}
wheel sha256 72254704f5dc88688056fd3e4dac481edfa45f13e4bf5ae1aa8810cdaa48f45b
sdist sha256 6a7b6fe360b86e75a4c7bba0a2765f50e2195263735825e251ec91404927dd81
evidence_sha256 84a7e8661f8ab9957393efa70991aa45a8c8052cb0e4dd66c67d6c1bc97081e3
ci_commit_sha f605808a89d334b5458c38f92201583004b6fff0
```

`load_report` PASS; B3 fields complete. Old `b41798f0…` manifest is
**superseded** and retained as history. B2 gate uses the exact artifact; no
mixed hash.

## B4 — UPLOADED_VERIFIED

Object `artifact_repository` matched `JunxiangPan/cbm`; 12 boundary tests pass
(cross/missing exit 2, same continues). CBE/CBS repository unification is not
claimed. Upload remains pending.

## B1 CONTRACT_ACTIVE / B2 UPLOADED_VERIFIED

See [`B1_B2_BLOCKED.md`](B1_B2_BLOCKED.md). No fake PASS:

- **B1 CONTRACT_ACTIVE** — `contract-v1.7.1` / `209d75b4` freezes §5.1;
  `tests/test_b1_identity.py` (6 tests) accepts `package_id: "cbm"` with
  `producer_id: "cbe"/"cbp"`; old-field mixing exits 3
  `REPORT_IDENTITY_MISMATCH`. This is consumer-side active, not a full train
  PASS.
- **B2 UPLOADED_VERIFIED** — real CBE report `6b4dc1ef…`, identity [];
  claims PASS 3/5; binary/docs/custom PASS; exact wheel `72254704…` matches
  manifest `0e0d37bd…`; CBM upload `cbm_gate_status=PASS`,
  `upload_status=UPLOADED_VERIFIED`. Release:
  https://github.com/JunxiangPan/cbm/releases/tag/v0.1.0
  Final decision: `upload-decision.json` (`UPLOAD_APPROVED`,
  `UPLOADED_VERIFIED`); `upload-final.json` points to the final report/body.
  `upload-decision.pre-upload.json` is historical.
- The synthetic fixture remains `not_upstream_evidence`; 4 readiness tests do
  not make B2 PASS.
- B4 is UPLOADED_VERIFIED for the exact artifact; CBE/CBS unification is not claimed.

## Reproduce

```bash
cd D:\qq苏瑾言大肥鱼\cbm
python -m pytest                                  # 128 passed (CBS present)
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

## Release / upload

CBM GitHub Release `v0.1.0` is published; wheel/sdist assets verified
`UPLOADED_VERIFIED`. No PyPI upload. Final decision `UPLOAD_APPROVED` /
`UPLOADED_VERIFIED`; pre-upload decision retained as history.
