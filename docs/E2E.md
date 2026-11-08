# CBM E2E matrix (v0.1.0 skeleton)

Run everything with:

```bash
python -m pytest
```

**Status: 84 offline/static tests pass; A-F live E2E has not been executed.**
The GitHub Actions workflow is statically audited, not executed; the live path
(real `gh` artifact download, release upload, digest re-read) is the next
acceptance step and must use a private test repository and a draft release,
never a production tag.

CBM 0.1.0 cannot consume real CBE/CBP reports until CONTRACT.md §5.1/§5.2 land
and CBE/CBP P0-06 is implemented. Current real reports would exit 3
`REPORT_IDENTITY_MISMATCH` or exit 2 `MISSING_RELEASE_BODY_HASH` /
`MISSING_BODY_HASH_SCOPE`; the suite below uses generated mock fixtures.

## A. Input / format (exit 2)

| ID | Scenario | Test |
| --- | --- | --- |
| A-01 | CBE report missing while claimed | `test_exit_codes.py::test_missing_cbe_report_claimed_exits_2` |
| A-02 | `declared_attached` missing | `test_exit_codes.py::test_missing_declared_attached_exits_2` |
| A-03 | Invalid JSON | `test_exit_codes.py::test_invalid_json_exits_2` |
| A-04 | `gate_status=PASS` with `exit_code=3` | `test_exit_codes.py::test_pass_with_nonzero_exit_code_is_input_error` |
| A-05 | Top-level `SKIPPED` (not a CBE/CBP status) | `test_exit_codes.py::test_gate_status_skipped_is_schema_error` |
| A-06 | Claimed but build-once artifact missing | `test_exit_codes.py::test_claimed_without_artifact_exits_2` |
| A-07 | Report hash/evidence hash are different things | `test_hashes.py::test_report_hash_is_not_the_evidence_field` |
| A-08 | Whitespace changes the raw report hash | `test_hashes.py::test_whitespace_changes_report_hash` |
| A-09 | CBP manifest missing `release_body_hash` | `test_exit_codes.py::test_missing_release_body_hash_exits_2` |
| A-10 | CBP manifest missing `body_hash_scope` | `test_exit_codes.py::test_missing_body_hash_scope_exits_2` |
| A-11 | CBP manifest uses `body_hash_scope: "full"` | `test_exit_codes.py::test_full_body_hash_scope_exits_2` |
| A-12 | CBP body hash fields are recorded | `test_exit_codes.py::test_cbp_body_hash_fields_are_recorded` |

## B. Gate / identity (exit 3/4, no upload)

| ID | Scenario | Test |
| --- | --- | --- |
| B-01 | CBE FAIL | `test_exit_codes.py::test_cbe_fail_exits_3_and_never_authorises` |
| B-02 | CBP FAIL | `test_exit_codes.py::test_cbp_fail_exits_3` |
| B-03 | Upstream SKIPPED_INFRA | `test_exit_codes.py::test_upstream_skipped_infra_exits_3_with_infra_section` |
| B-04 | skip ratio > 20% | `test_exit_codes.py::test_skip_ratio_over_threshold_exits_4` |
| B-05 | blocking_skip=true | `test_exit_codes.py::test_blocking_skip_exits_3` |
| B-06 | CBE package_id is the producer | `test_exit_codes.py::test_identity_mismatch_exits_3` |
| B-07 | CBP package_id is the producer | `test_exit_codes.py::test_cbp_identity_mismatch_exits_3` |
| B-08 | Not claimed but reports use producer identity | `test_exit_codes.py::test_not_claimed_with_wrong_identity_reports_exits_3` |
| B-09 | Producer fields are traceability only | `test_exit_codes.py::test_producer_id_is_recorded_but_not_subject_identity` |
| B-10 | Missing producer fields are tolerated | `test_exit_codes.py::test_missing_producer_id_is_allowed` |
| B-11 | CBP top-level PASS contradicts a failed gate | `test_exit_codes.py::test_cbp_top_level_pass_with_failed_gate_exits_3` |
| B-12 | CBP blocking gate SKIPPED | `test_exit_codes.py::test_cbp_blocking_gate_skipped_exits_3` |
| B-13 | CBS report is not reused (`package_id: "cbs"`) | `test_exit_codes.py::test_cbs_report_is_not_reused` |

## C. Artifact / upload (exit 0/3)

| ID | Scenario | Test |
| --- | --- | --- |
| C-01 | CBP lacks the wheel digest | `test_exit_codes.py::test_cbp_artifact_hash_missing_exits_3` |
| C-02 | CBP digest differs from build-once | `test_exit_codes.py::test_cbp_artifact_hash_mismatch_exits_3` |
| C-03 | `dist/` prefix is accepted | `test_exit_codes.py::test_cbp_artifact_hash_with_dist_prefix_is_accepted` |
| C-04 | `sha256:` prefix and `*` path accepted | `test_hashes.py::test_artifact_hash_prefix_and_star_are_accepted` |
| C-05 | Tampered wheel | `test_hashes.py::test_artifact_tamper_is_detected` |
| C-06 | Tampered extra release asset | `test_hashes.py::test_release_assets_extra_tamper_is_detected` |
| C-07 | Gate failure never constructs an uploader | `test_gate_before_upload.py::test_gate_failure_never_loads_the_uploader` |
| C-08 | No-upload decision refuses upload | `test_gate_before_upload.py::test_no_upload_decision_refuses_before_uploader` |
| C-09 | Tampered artifact after approval | `test_gate_before_upload.py::test_tampered_artifact_is_refused_before_uploader` |
| C-10 | Upload after approval | `test_gate_before_upload.py::test_upload_happens_only_after_approval` |
| C-11 | Same digest is idempotent | `test_gate_before_upload.py::test_same_digest_is_idempotent` |
| C-12 | Conflicting digest is not overwritten | `test_gate_before_upload.py::test_conflicting_digest_is_not_overwritten` |

## D. NOT_UPLOADED / body / P2-04

| ID | Scenario | Test |
| --- | --- | --- |
| D-01 | Claimed failure includes the exact phrase, never PASS | `test_not_uploaded_body.py::test_claimed_failure_contains_exact_phrase_and_no_pass` |
| D-02 | Not claimed has no "declared as attached" phrase | `test_not_uploaded_body.py::test_not_claimed_has_no_declared_phrase` |
| D-03 | Infra section is dedicated, still NOT_UPLOADED | `test_not_uploaded_body.py::test_infra_section_is_dedicated_and_not_pass` |
| D-04 | Uploaded section uses UPLOADED_VERIFIED | `test_not_uploaded_body.py::test_uploaded_section_uses_verified_status` |
| D-05 | Unverified upload is never PASS | `test_not_uploaded_body.py::test_unverified_upload_is_not_pass` |
| D-06 | Marker replacement is idempotent | `test_not_uploaded_body.py::test_marker_block_replacement_is_idempotent` |
| D-07 | Missing marker is not guessed | `test_not_uploaded_body.py::test_missing_marker_returns_none` |
| D-08 | No report -> SKIPPED_INFRA / EVIDENCE_ABSENT | `test_e2e_mock.py::test_finalize_without_report_is_skipped_infra` |
| D-09 | Failed upload does not leave UPLOAD_PENDING | `test_e2e_mock.py::test_finalize_after_failed_upload_rewrites_pending` |
| D-10 | PASS without upload is rejected | `test_e2e_mock.py::test_finalize_rejects_pass_without_upload` |
| D-11 | GITHUB_OUTPUT fields are exported | `test_e2e_mock.py::test_finalize_exports_github_outputs` |
| D-12 | Missing input still writes evidence | `test_e2e_mock.py::test_verify_missing_input_writes_evidence` |

## E. Workflow static audit

| ID | Assertion | Test |
| --- | --- | --- |
| E-01 | Only verify/upload/finalize jobs, no publish | `test_workflow_static.py::test_workflow_is_parseable_and_has_only_three_jobs` |
| E-02 | Upload only on explicit UPLOAD decision | `test_workflow_static.py::test_upload_requires_explicit_verify_decision` |
| E-03 | Finalize runs after failure, not on cancel | `test_workflow_static.py::test_finalize_runs_after_failure_but_not_on_cancel` |
| E-04 | Verify evidence uploads on failure | `test_workflow_static.py::test_verify_artifact_step_runs_on_failure` |
| E-05 | Every workflow_call input optional | `test_workflow_static.py::test_every_workflow_call_input_is_optional` |
| E-06 | No continue-on-error / `|| true` / `--clobber` / `always()` | `test_workflow_static.py::test_no_error_hiding_constructs` |
| E-07 | No rebuild commands | `test_workflow_static.py::test_no_rebuild_commands` |
| E-08 | Actions pinned by SHA | `test_workflow_static.py::test_all_actions_are_sha_pinned` |
| E-09 | Least privilege permissions | `test_workflow_static.py::test_permissions_are_least_privilege` |
| E-10 | Evidence recovery works with no artifact | `test_workflow_static.py::test_finalize_recovers_evidence_even_when_no_artifact_exists` |

## F. Not yet executed (live acceptance)

These require credentials and a private test repository; they are deliberately
outside the offline skeleton:

- real `gh api` artifact download across repositories;
- real `gh release upload` to a draft release, then remote digest re-read;
- cross-repository token scope checks (`actions:read`, `contents:write`);
- a forced 504/timeout to confirm `SKIPPED_INFRA` end-to-end;
- one full release-train run with the CBS body generator merging the finalized
  `cbm-evidence-out` fragment.

CBM v0.1.0 does not modify the CBS Release body and is not in the CBS `publish`
`needs` graph.

Real-data F runs are blocked until the five hard blockers in docs/V17_BLOCKERS.md land. Do not
report a live E2E pass by feeding the current real CBE/CBP reports into CBM and
treating the expected exit 2/3 as a test failure; those exits are the correct
fail-closed behavior.

## G. Upstream defect probe

| ID | Scenario | Test |
| --- | --- | --- |
| G-01 | CBS body generator currently hides a completely missing CBM (`- none`, no `CBM`, no `EVIDENCE_ABSENT`); marked `KNOWN_FAIL_SILENT` | `test_known_fail_silent.py::test_known_fail_silent_cbs_body_omits_missing_cbm` |

G-01 is green while the defect exists; it is a canary, not an acceptance. When
CBS implements `docs/CBS_BODY_REQUIREMENT.md`, change G-01 to assert
`CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`.
