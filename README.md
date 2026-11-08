# CBM attach evidence (v0.1.0)

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

## Current status: five hard blockers

CBM v0.1.0 is a **skeleton**. It has **84 offline/static tests passing**. The
A-F live E2E matrix has **not** been executed (it needs a private test
repository and scoped tokens); do not claim "CBM passed real upload E2E".

CBM **cannot consume real CBE/CBP reports yet**. Five upstream items are not
implemented:

1. **CONTRACT.md §5.1 is not applied.** Current CBE/CBP reports still put the
   producer name in `package_id` (`"cbe"` / `"cbp"`). CBM requires
   `package_id == "cbm"` and will exit 3 `REPORT_IDENTITY_MISMATCH` and refuse
   to upload a real report. Required order: apply §5.1 to CONTRACT.md -> CBE/CBP
   write `package_id: "cbm"` plus `producer_id` -> CBM can consume them.
2. **CBP P0-06 is not implemented.** CBM requires CBP to publish
   `release_body_hash` and `body_hash_scope: "base"`. Missing
   `release_body_hash` -> exit 2 `MISSING_RELEASE_BODY_HASH`; missing
   `body_hash_scope` -> exit 2 `MISSING_BODY_HASH_SCOPE`; `"full"` -> exit 2
   `BODY_HASH_SCOPE_UNSUPPORTED`. CBP's currently uploaded CI artifact is the
   legacy `cbp-quality-manifest/v1`; P0-06 must emit the v1.7 manifest with both
   fields before CBM can consume it.
3. **CBM needs its own subject report.** CBM must consume CBE/CBP reports with
   `package_id: "cbm"`, not the CBS reports with `package_id: "cbs"`. Reusing
   the CBS report is a hard failure: exit 3 `REPORT_IDENTITY_MISMATCH`. The
   v1.7 train must run CBE/CBP for the CBM subject (or emit a CBM-scoped
   report); it cannot reuse the CBS report.
4. **CBS body generator is fail-silent when CBM is absent.** It currently
   writes `- none` instead of `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`.
5. **`artifact_repository` is not unified.** CBE/CBP/CBS artifacts live in
   different repositories; CBM v0.1.0 takes one repository.

**B3+B4 are a compound blocker and B5 is a fail-silent hard blocker** — these
are v1.7 release-train blockers, not CBM documentation risks. See
`docs/V17_BLOCKERS.md`.

Until all five hard blockers land, the 84 tests prove **logic on mock
fixtures**, not real-data consumption. See `docs/CONTRACT_PROPOSAL_5.1.md`.

### Fail-silent risk: CBS body generator

If CBM evidence is completely absent (workflow never ran, or checkout/API failed
before any evidence), CBM cannot write the body. Current CBS
`tools/release_body_v17.py` renders `- none` when `not_uploaded` is empty; it
does not synthesize `CBM: NOT_UPLOADED` / `EVIDENCE_ABSENT`. Until the CBS thread
adds that default, this case is **fail-silent**, not fail-closed. CBM's own
no-report `finalize` path does write `CBM: NOT_UPLOADED` with `EVIDENCE_ABSENT`
when it can run; see `docs/CBS_BODY_REQUIREMENT.md`. This is **blocker B5** in
`docs/V17_BLOCKERS.md`, proven by `tests/test_known_fail_silent.py` (it asserts
the current `- none` output and is marked `KNOWN_FAIL_SILENT`).

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
  case **CBS body generator must supply** `CBM: NOT_UPLOADED` +
  `EVIDENCE_ABSENT`; CBM cannot. Audited on 2026-11-08: CBS
  `tools/release_body_v17.py` does **not** implement that default — it renders
  `- none` when `not_uploaded` is empty, so a total CBM evidence absence is
  currently fail-silent. This is **blocker B5**, not a documentation risk; see
  `docs/V17_BLOCKERS.md` and `docs/CBS_BODY_REQUIREMENT.md`.

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

**84 tests pass**: exit-code mapping, gate-before-upload (including a mock
uploader that records calls), NOT_UPLOADED body rendering, hashes, workflow
static audit, schema/report lockstep, and a mock end-to-end
verify/upload/finalize flow. These are offline/static tests, not real E2E.

`tests/test_known_fail_silent.py` is a deliberate canary, not an acceptance: it
asserts the current CBS `- none` output and is marked `KNOWN_FAIL_SILENT`. It
uses the real CBS `release_body_v17.py` when present, otherwise a mock that
reproduces the audited lines. Update it to assert the fixed behavior when CBS
implements `docs/CBS_BODY_REQUIREMENT.md`.

## Open contract points

1. **§5.1 report identity.** CBE/CBP reports currently use `package_id`
   ambiguously. CBM requires `package_id == "cbm"` and treats a producer name
   there as `REPORT_IDENTITY_MISMATCH` (exit 3, no upload).
2. **§5.2 CBP body hash scope.** CBM requires `release_body_hash` and
   `body_hash_scope: "base"` in the CBP quality manifest; missing or `"full"`
   exits 2.

Both proposals are in
[`docs/CONTRACT_PROPOSAL_5.1.md`](docs/CONTRACT_PROPOSAL_5.1.md). They are
change-control inputs for the CBS/CBP owners; this repository does not edit the
frozen contract. **CBM 0.1.0 rejects real CBE/CBP reports until both land.**
