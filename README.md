# CBM attach evidence (v0.1.0)

[![cbm-ci](https://github.com/JunxiangPan/cbm/actions/workflows/ci.yml/badge.svg)](https://github.com/JunxiangPan/cbm/actions/workflows/ci.yml)

CBM is a **sidecar attachment attestation** for the v1.7 release train. It is
not the 10th traditional gate, it is not a CBP gate, and it is not in the CBS
`publish` `needs` graph. It consumes CBE/CBP reports that already exist and
decides whether the optional CBM build-once artifact may be attached.

The frozen F1-F6 source is `docs/v1.7/CONTRACT.md` in the CBS repository,
commit `4a437df`, SHA-256
`a561f19e0a8e4dba92af82400b5696da18e000ba5362571cb0b40243b9a3afca`.
CBM does not define a private variant of F1-F6.

During CBM v0.1.0 the CBS repository advanced past `eeb3645` and added an
additive §11 (build-once profiles); F1-F6 and §5 are unchanged. CBM's artifact
verifier accepts §11's basename `RELEASE_ASSETS.sha256` inventory and skips a
self-listed manifest. The contract identity proposal in
`docs/CONTRACT_PROPOSAL_5.1.md` is still an unapplied change-control input.

## Current status: B1 contract active; B5 fixed; B3 field-level; B2/B4 open

CBM v0.1.0 is a **skeleton**. It has **110 offline/static tests passing**. A-F
live E2E is still not executed (private test repo + scoped tokens).

2026-11-09 status:

- **B1 CONTRACT_ACTIVE** — `contract-v1.7.1` / `209d75b4` freezes §5.1.
  Consumer tests cover `package_id: "cbm"` + `producer_id: "cbe"/"cbp"` and
  retain exit 3 `REPORT_IDENTITY_MISMATCH` for old-field mixing.
- **B2 BLOCKED** — there is no real CBE report with `package_id: "cbm"`; the
  CBP side now exists, but full identity needs both. A synthetic fixture/schema
  readiness test exists (`not_upstream_evidence`); it is not B2 evidence.
- **B3 FIELD_LEVEL_COMPLETE** — CBP 1.2.0 RC `855fed7` produced a CBM-scoped
  manifest `bc5461e6…` (`package_id: "cbm"`, `producer_id: "cbp"`, `base`).
  `body_hash_scope`, `release_body_hash`, `artifact_hashes` and
  `evidence_sha256` are accepted; missing/full scope exits 2. This is
  field-level B3, not B2.
- **B4 FAIL_CLOSED_ONLY** — CBP 1.2.2 `artifact_repository` object is parsed;
  cross-repository and missing object exit 2 `ARTIFACT_REPOSITORY_MISMATCH`;
  same repository (case-insensitive) continues. 8 boundary tests; CBE/CBS are
  still not unified.
- **B5 FIXED** — CBS v1.7.0-integration `fa1740f` (regression `tests/test_known_fail_silent.py`) renders
  `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`; the canary is flipped to assert the
  fixed behavior.

No tag, GitHub Release, or PyPI upload. Evidence:
`audit/v1.2.0-rc/`. Dependency order: B1 -> B2 -> B3+B4; B5 was independent and
is now fixed.

### CBS body generator (B5 fixed)

CBS v1.7.0-integration `fa1740f` adds explicit CBM/CBC records: a missing CBM
renders a dedicated `## CBM` section with `CBM: NOT_UPLOADED`, `reason:
EVIDENCE_ABSENT`, `upload_status: NOT_UPLOADED`, and the exact
`declared as attached but not uploaded` phrase when declared. The old
`- none`-only behavior is historical.

`tools/check_b5.py --check-upstream` now prints `STATUS=B5_MAYBE_FIXED`, which
means the fixed behavior is present. `tests/test_known_fail_silent.py` was
flipped to assert `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT` and is no longer a
KNOWN_FAIL_SILENT canary. The historical requirement is retained in
`docs/CBS_BODY_REQUIREMENT.md`.

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

**110 tests pass**: exit-code mapping, gate-before-upload (including a mock
uploader that records calls), NOT_UPLOADED body rendering, hashes, workflow
static audit, schema/report lockstep, and a mock end-to-end
verify/upload/finalize flow. These are offline/static tests, not real E2E.

`tests/test_known_fail_silent.py` is now the flipped B5 regression test: it
asserts the fixed CBS output (`CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`, no
`- none`) and the exact phrase when CBM is declared attached. It still checks the
probe's missing/import/unexpected modes; a missing CBS checkout skips with
`SKIP_REASON=CBS_BODY_GENERATOR_NOT_FOUND`, and an unimportable file fails with
`FAIL_REASON=CBS_BODY_GENERATOR_UNIMPORTABLE`.

**110 passed = 110 normal tests; no `KNOWN_FAIL_SILENT` canary remains.** Do not
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
frozen contract. **Full CBM consumption still waits for B1/B2 (and B4 for the
unified repository); B3 field-level and B5 are complete.**
