# v1.7 release-train integration requirements for CBM

Status: **v1.7 release-train hard blockers (B3+B4)**. CBM cannot satisfy these
inside its own repository.

## 1. CBM needs a CBM-scoped CBE/CBP report

CBM is a sidecar attachment, not the CBS subject. It must consume reports whose
`package_id` is the CBM subject:

```json
{"package_id": "cbm", "producer_id": "cbe", "version": "v0.1.0", "tag": "v0.1.0"}
{"package_id": "cbm", "producer_id": "cbp", "version": "v0.1.0"}
```

It must **not** reuse the CBS reports (`package_id: "cbs"`). Reuse is a hard
failure:

```text
exit 3
cbm_gate_status = FAIL
reason = REPORT_IDENTITY_MISMATCH
upload_status = NOT_UPLOADED
```

The train therefore needs a CBE/CBP run for the CBM subject, or an explicitly
CBM-scoped report emitted from the same run. "CBM reuses CBS's report" is not a
supported mode.

## 2. All three artifacts must share one `artifact_repository`

CBM downloads:

| Input | Artifact | Owner |
| --- | --- | --- |
| `build_once_run_id` / `build_once_artifact` | `cbm-build-once` | CBM build-once |
| `cbe_run_id` / `cbe_report_artifact` | `cbe-report` | CBE |
| `cbp_run_id` / `cbp_report_artifact` | `cbp-quality-manifest` | CBP |

GitHub Actions artifact download is repository-bound. All three artifacts must
be uploaded to the **same** repository, passed to CBM as `artifact_repository`.
CBM v0.1.0 takes one `artifact_repository`; split repositories require a copy
step in the train or a v0.2.0 input extension. If they live in separate
repositories, CBM's `verify --fetch` cannot download them and exits 2:

- `MISSING_BUILD_ONCE_ARTIFACT`
- `MISSING_CBE_REPORT`
- `MISSING_CBP_REPORT`

CBM cannot work around this with a token; the repository boundary is part of the
artifact API.

## 3. Audited current state (2026-11-08)

- CBS `reusable-v17-release.yml` is a **mock** orchestration: it uploads only
  `v17-mock-artifact` in the CBS repo and has no CBM job.
- CBP `ci.yml` uploads `quality-manifest-${github.run_id}` in the **CBP**
  repository, not in a shared `artifact_repository`.
- That uploaded manifest is produced by `tools/dogfood_manifest.py` and uses the
  legacy `cbp-quality-manifest/v1` shape. CBP's v1.7 `report_schema.py` names
  `release_body_hash` but has no `body_hash_scope`. Co-locating the artifact is
  not enough; CBP P0-06 must emit the v1.7 fields.
- The CBS mock CBE report uses `package_id: "cbe"` and the mock CBP report uses
  `package_id: "cbs"` (`tests/v17/mock/cbe_cli.py`, `tests/v17/mock/cbp_cli.py`);
  neither is the CBM subject. CBM would exit 3 on either.
- The CBE repository is not present in this workspace, so its upload target
  could not be audited.
- The same-repo artifact contract and the CBM-scoped report are therefore
  **not implemented yet**.

Current CBP artifact name is `quality-manifest-${github.run_id}`; the train may
pass that value to `cbp_report_artifact` (CBM does not hardcode the name). The
build-once and CBE artifacts must be co-located with it.

This is not a CBM defect. It is an orchestration gap in the v1.7 train.

**B3 (CBP P0-06) and B4 (artifact_repository) are a compound blocker.** Solving
only B3 still exits 2 because the artifacts are in different repositories;
solving only B4 still exits 2 because the CBP manifest lacks
`release_body_hash`/`body_hash_scope`. Both must land together; see
[`docs/V17_BLOCKERS.md`](V17_BLOCKERS.md).

## 4. Required train wiring

```yaml
# illustrative; not applied to CBS
cbm-attach:
  needs: [preflight, cbm-build-once, cbm-cbe-gate, cbm-cbp-gate]
  uses: <owner>/<cbm-repo>/.github/workflows/cbm-attach.yml@<40-hex-sha>
  with:
    cbm_version: ${{ needs.preflight.outputs.cbm_version }}
    cbm_tag: ${{ needs.preflight.outputs.cbm_tag }}
    declared_attached: ${{ contains(fromJSON(vars.RELEASE_TRAIN_COMPONENTS), 'cbm') }}
    build_once_run_id: ${{ needs.cbm-build-once.outputs.run_id }}
    build_once_artifact: cbm-build-once
    cbe_run_id: ${{ needs.cbm-cbe-gate.outputs.run_id }}
    cbe_report_artifact: cbe-report
    cbp_run_id: ${{ needs.cbm-cbp-gate.outputs.run_id }}
    cbp_report_artifact: cbp-quality-manifest
    release_tag: ${{ needs.preflight.outputs.tag }}
    upload_target: github-release
    repository: ${{ github.repository }}
    artifact_repository: ${{ vars.CB_ARTIFACT_REPOSITORY }}
```

`publish` must not `needs` CBM. CBM's result is evidence, not a publish gate.

## 5. Contract §11 addition (proposed, not applied)

```text
v1.7 artifact repository:
- CBM build-once, CBE report and CBP quality-manifest MUST be uploaded to the
  same artifact_repository.
- The train MUST provide CBM-scoped CBE/CBP reports with package_id = "cbm";
  CBM MUST NOT reuse the CBS reports.
- A separate-repository layout is not consumable by CBM and is an orchestration
  failure, not a CBM gate failure.
```
