# B1 / B2 / B5 — blocked (no fake PASS)

CBM v0.1.0 does not claim B1, B2, or B5 as complete. The following are the
exact fail-closed behaviors and the reason they remain blocked.

## B1 — CONTRACT.md §5.1 identity

- State: §5.1 is **not applied** to CONTRACT.md. The proposal is
  `docs/CONTRACT_PROPOSAL_5.1.md`; the contract owner must apply it.
- CBM behavior: `package_id != "cbm"` → exit 3,
  `cbm_gate_status=FAIL`, `reason=REPORT_IDENTITY_MISMATCH`,
  `upload_status=NOT_UPLOADED`.
- Evidence: `tests/test_exit_codes.py::test_identity_mismatch_exits_3`,
  `test_cbp_identity_mismatch_exits_3`, `test_cbs_report_is_not_reused`.

## B2 — CBM-scoped CBE/CBP report

- State: no `package_id: "cbm"` + `producer_id` report exists in the train.
  The available CBP 1.2.0 RC-era manifest is `package_id: "cbp"`,
  `version: "v1.2.0"`.
- CBM behavior: the raw manifest is structurally accepted for B3 field checks
  but is **not** a CBM subject; `identity_errors` against `cbm` is non-empty.
- Evidence: `tests/test_b3_cbp_rc.py::test_b3_manifest_is_not_cbm_scoped`.
- B3 is therefore **PARTIAL**, not complete.

## B5 — CBS body generator

- State: CBS `tools/release_body_v17.py:20,39` still uses
  `not_uploaded = report.get("not_uploaded", [])` and
  `or ["- none"]`; a missing CBM is invisible.
- CBM behavior: `tests/test_known_fail_silent.py` is a `KNOWN_FAIL_SILENT`
  canary; `tools/check_b5.py --check-upstream` reports
  `STATUS=KNOWN_FAIL_SILENT` and exits 0. When CBS changes, it reports
  `B5_MAYBE_FIXED` and the canary must be flipped.
- No CBS file was modified by CBM.

## No fake PASS

- No tag, GitHub Release, PyPI upload, or `PASS` claim for B1/B2/B5.
- B3 is marked PARTIAL; B4 is marked FAIL_CLOSED_ONLY.
- `91 passed = 90 normal tests + 1 KNOWN_FAIL_SILENT canary`.
