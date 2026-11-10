# cbm-attach

[![cbm-ci](https://github.com/JunxiangPan/cbm/actions/workflows/ci.yml/badge.svg)](https://github.com/JunxiangPan/cbm/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**For** release engineers who already run CBE/CBP gates and need a defensible
sidecar attachment decision.

**Problem:** a release can be "green" while the optional CBM artifact was never
built, was built from a different hash, or was attached with a stale manifest.
`cbm-attach` consumes the existing evidence, verifies the canonical hashes and
the build-once wheel, and emits a machine-readable report plus a human-readable
body fragment. It never re-runs CBE/CBP and is not a gate in their `needs`
graph.

**Start:**

```bash
pip install cbm-attach
cbm-attach --help
```

Until the PyPI release is available, install the exact released wheel:

```bash
pip install https://github.com/JunxiangPan/cbm/releases/download/v0.1.1/cbm_attach-0.1.1-py3-none-any.whl
cbm-attach --help
```

From a checkout:

```bash
python -m pip install -e .
cbm-attach --help
```

The import package remains `cbm_attach`; the distribution and CLI are
`cbm-attach`.

## Current status: v0.1.1 GitHub Release

CBM v0.1.1 is a **sidecar attachment** tool, not a complete product
certification and not an A-F live E2E proof. GitHub Release:

https://github.com/JunxiangPan/cbm/releases/tag/v0.1.1

v0.1.0 remains published and unchanged. PyPI upload is blocked pending a
trusted publisher/credentials; use the exact wheel above until then.

- **B1 CONTRACT_ACTIVE** — contract-v1.7.1 §5.1 active; identity tests retained.
- **0.1.1 changes** — Apache-2.0 license, canonical evidence-hash trust root,
  `cbm-attach` distribution/console script, uploader failure tests, in-toto
  Statement, generic evidence adapters.
- **B3 FIELD_LEVEL_COMPLETE** — CBP 1.2.2 object manifest, base scope,
  artifact/evidence hashes.
- **B4 UPLOADED_VERIFIED** — object artifact repository matched; fail-closed
  boundaries retained.
- **B5 FIXED** — CBS body generator emits `CBM: NOT_UPLOADED` +
  `EVIDENCE_ABSENT`.

PyPI: **BLOCKED_NO_PYPI_CREDENTIALS** (no trusted publisher/credentials).

**131 offline/static tests pass.** The source is Apache-2.0. No A-F live E2E
or full-product certification is claimed. Evidence lives in
`audit/v1.2.0-rc/`.

## Trust root

CBE and CBP `evidence_sha256` values are recomputed from canonical JSON before
the gate decides; a format-valid but wrong hash exits 3
`EVIDENCE_HASH_MISMATCH`. CBM's own report is sealed the same way. Raw-byte
report hashes remain separate from canonical evidence hashes.

## in-toto and generic evidence

`verify` and `upload` write an in-toto v1 Statement next to the CBM report
(`cbm-report.statement.json` by default, or `--statement PATH`). Its
`predicateType` is `https://cbm.dev/attachment/v1`; the existing
`cbm-report.json` is preserved inside the predicate.

For non-CBM subjects, `cbm_attach.evidence` exposes `EvidenceInput`,
`load_evidence()` and `identity_errors_for(subject_package_id=..., producers=...)`.
This is an adapter layer; the four-piece CBE/CBP/CBM path is unchanged.

## Non-goals

- CBM does not run CBE or CBP, and does not re-compute their gates.
- CBM does not prove code security.
- CBM does not rebuild the package. It verifies the build-once artifact and
  refuses an artifact that is not listed in `WHEEL_SHA256` and
  `RELEASE_ASSETS.sha256`. CBM 0.1.0 supports `artifact_type=wheel` only; a
  zip-bundle is rejected as an input error.
- CBM does not write the whole CBS Release body. It emits one marker-delimited
  fragment; the CBS body generator merges it.

## Two-axis status

| Situation | `cbm_gate_status` | `upload_status` | exit |
| --- | --- | --- | --- |
| not claimed, no failure | `NOT_UPLOADED` | `NOT_UPLOADED` | 0 |
| CBE/CBP FAIL blocks upload | `FAIL` | `NOT_UPLOADED` | 3 |
| own hash/upload verification failure | `FAIL` | `NOT_UPLOADED` or `UPLOADED_UNVERIFIED` | 3 |
| infrastructure failure | `SKIPPED_INFRA` | `NOT_UPLOADED` | 3 |
| missing/invalid input | `PRECONDITION_FAIL` | `NOT_UPLOADED` | 2 |
| skip ratio above 20% | `FAIL` | `NOT_UPLOADED` | 4 |
| uploaded and digest verified | `PASS` | `UPLOADED_VERIFIED` | 0 |

The Release body labels the attachment from `upload_status`, so a gate failure
is still shown as `NOT_UPLOADED` without being laundered into PASS.

## Commands

```bash
# verify: consume reports, enforce the gate, write report/body/decision
python -m cbm_attach verify \
  --version v0.1.0 --tag v0.1.0 --release-tag v1.7.0 \
  --declared-attached true --upload-target github-release \
  --cbe-report cbe.json --cbp-report cbp.json --build-once-dir build-once \
  --output cbm-evidence/cbm-report.json \
  --body cbm-evidence/cbm-body.md \
  --decision cbm-evidence/cbm-decision.json

# upload: re-verify the build-once artifact, then upload idempotently
python -m cbm_attach upload \
  --report cbm-evidence/cbm-report.json \
  --decision cbm-evidence/cbm-decision.json \
  --build-once-dir build-once \
  --upload-target github-release \
  --repository owner/repo --release-tag v1.7.0 \
  --output cbm-evidence/cbm-report.final.json \
  --body cbm-evidence/cbm-body.final.md

# finalize: choose the best report, regenerate the body fragment
python -m cbm_attach finalize \
  --input cbm-evidence --output cbm-evidence-out/cbm-report.json \
  --body cbm-evidence-out/cbm-body.md --declared-attached true
```

`verify --fetch` and `upload --fetch` download run artifacts through `gh api`.
`artifact_repository` must hold all three run artifacts (CBM build-once, CBE
report, CBP manifest); split repositories need an input extension in a later
version. Cross-repository download needs a token with `actions:read` on the
artifact repository; cross-repository release upload needs `contents:write` on
the release repository. Use a scoped GitHub App/PAT, not a broad personal token.

GitHub artifact downloads are repository-bound. The v1.7 release train must
upload the **CBM build-once artifact, CBE report and CBP manifest to the same
`artifact_repository`**. If CBE/CBP upload in their own repositories, CBM cannot
download them; `verify --fetch` will exit 2 with `MISSING_BUILD_ONCE_ARTIFACT`,
`MISSING_CBE_REPORT` or `MISSING_CBP_REPORT`. This is a release-train
orchestration requirement, not something CBM can fix alone. It should be added
to CONTRACT.md §11.

Audited on 2026-11-08: the checked-in CBS mock train
(`reusable-v17-release.yml`) uploads only `v17-mock-artifact` in the CBS repo
and has no CBM job; CBP `ci.yml` uploads `quality-manifest-${run_id}` in the
**CBP** repo. The artifacts are not co-located, so the same-repo contract is
**not implemented yet**; this is **blocker B4**, and it must be solved together
with **B3** (CBP P0-06), not separately. CBM v0.1.0 takes one
`artifact_repository`; split repos need a copy step or a v0.2.0 input
extension. Required names:
`cbm-build-once`, `cbe-report`, `cbp-quality-manifest` (the actual CBP artifact
may be `quality-manifest-<run_id>`; pass it as `cbp_report_artifact`). See
`docs/INTEGRATION_REQUIREMENTS.md`.

CBM 0.1.0 supports `artifact_type=wheel` only. A CBS `artifact_type=zip-bundle`
requires CBM 0.2.0. CBM does not sign and does not consume CBS's
`update-manifest.sig`; that is a CBS release asset and must be listed in CBS's
own `RELEASE_ASSETS.sha256` per §11. CBM reads only the CBM build-once
artifact's manifest.

## Workflow integration (v0.1.0)

The reusable workflow is `.github/workflows/cbm-attach.yml`. It has three jobs:

- `verify` consumes CBE/CBP reports, enforces the gate, and writes a **draft**
  `cbm-evidence/cbm-report.json` plus `cbm-evidence/cbm-body.md`.
- `upload` runs only when `needs.verify.result == 'success'` **and**
  `needs.verify.outputs.decision == 'UPLOAD'`; it re-verifies the build-once
  artifact, uploads it, and writes `cbm-evidence/cbm-report.final.json` plus
  `cbm-evidence/cbm-body.final.md`. `needs.verify.result` is `failure` for exit
  2/3/4, so missing input, gate failure and skip-over-threshold all skip upload.
- `finalize` runs with `if: ${{ !cancelled() }}`, checks out the CBM tooling
  independently of verify's artifact, recovers every evidence artifact, and
  writes `cbm-evidence-out/cbm-report.json` plus
  `cbm-evidence-out/cbm-body.md` (a marker-delimited fragment). A checkout or
  GitHub API outage can still prevent finalize from writing evidence. In that
  case CBS body generator supplies the `CBM: NOT_UPLOADED` +
  `EVIDENCE_ABSENT` record. CBS v1.7.0-integration `fa1740f` implements this;
  B5 is fixed and the test is flipped. See `docs/V17_BLOCKERS.md` and
  `docs/CBS_BODY_REQUIREMENT.md`.

The CBS body generator must consume the **finalized** `cbm-evidence-out`
artifact, not the verify draft. The verify draft says `NOT_UPLOADED` because the
upload has not happened yet; that is honest, but it is not the final attachment
status.

CBM does **not** edit the CBS Release body in v0.1.0. The fragment includes
`<!-- CBM:START -->` / `<!-- CBM:END -->` so the CBS generator can merge one
block idempotently. If a future asynchronous step updates the body, it must do a
latest-body read-modify-write, replace exactly the marker block, retry on
conflict, and never touch the body when the upload failed. `body.py` already
provides `replace_marker_block` for that future path.

If `finalize` finds no report at all, it writes
`cbm_gate_status=SKIPPED_INFRA`, `reason=EVIDENCE_ABSENT` (detail
`WORKFLOW_FAILED_BEFORE_EVIDENCE`) and `upload_status=NOT_UPLOADED`; it never
writes PASS. If the verify or upload job
failed after writing `UPLOAD_PENDING`, `finalize` turns that stale pending
report into `FAIL` / `UPLOAD_FAILED` (or `EVIDENCE_INVALID` for a
PASS-without-upload contradiction).

## Evidence hashes

`cbe_report_hash` and `cbp_report_hash` are SHA-256 over the **raw bytes** of
the report that CBM read. They are not the report's `evidence_sha256` field and
they are not a canonicalised JSON hash. `evidence_sha256` on the CBM report is
the SHA-256 of the canonical JSON of the report without that field.

## Tests

```bash
python -m pytest
```

**131 tests pass**: exit-code mapping, gate-before-upload (including a mock
uploader that records calls), NOT_UPLOADED body rendering, hashes, workflow
static audit, schema/report lockstep, and a mock end-to-end
verify/upload/finalize flow. These are offline/static tests, not real E2E.

`tests/test_known_fail_silent.py` is now the flipped B5 regression test: it
asserts the fixed CBS output (`CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`, no
`- none`) and the exact phrase when CBM is declared attached. It still checks the
probe's missing/import/unexpected modes; a missing CBS checkout skips with
`SKIP_REASON=CBS_BODY_GENERATOR_NOT_FOUND`, and an unimportable file fails with
`FAIL_REASON=CBS_BODY_GENERATOR_UNIMPORTABLE`.

**131 passed = 131 normal tests; no `KNOWN_FAIL_SILENT` canary remains.** Do not
reintroduce the old `- none` assertion as an accepted state.

Probe CLI:

```bash
python tools/check_b5.py --check-upstream
```

| Output | Exit | Meaning |
| --- | --- | --- |
| `STATUS=B5_MAYBE_FIXED` | 0 | expected fixed state; B5 test is green |
| `STATUS=KNOWN_FAIL_SILENT` | 0 | old/failed CBS behavior; B5 test fails as a regression |
| `SKIP_REASON=CBS_BODY_GENERATOR_NOT_FOUND` | 0 | CBS checkout missing; test skips |
| `FAIL_REASON=CBS_BODY_GENERATOR_UNIMPORTABLE` | 3 | CBS file exists but import/build fails; test fails |
| `FAIL_REASON=UNEXPECTED_OUTPUT` | 2 | output is neither old defect nor fixed; inspect |

## Open contract points

1. **§5.1 report identity.** CBE/CBP reports currently use `package_id`
   ambiguously. CBM requires `package_id == "cbm"` and treats a producer name
   there as `REPORT_IDENTITY_MISMATCH` (exit 3, no upload).
2. **§5.2 CBP body hash scope.** CBM requires `release_body_hash` and
   `body_hash_scope: "base"` in the CBP quality manifest; missing or `"full"`
   exits 2.

The proposals are in
[`docs/CONTRACT_PROPOSAL_5.1.md`](docs/CONTRACT_PROPOSAL_5.1.md); the full
blocker list is [`docs/V17_BLOCKERS.md`](docs/V17_BLOCKERS.md). They are
change-control inputs for the CBS/CBP owners; this repository does not edit the
frozen contract. **CBM 0.1.0 sidecar upload is verified; B3 field-level and B5
are complete; full product/A-F live E2E is not claimed.**
