# B1 / B2 — blocked (B5 fixed; no fake PASS)

CBM v0.1.0 does not claim B1 or B2 as complete. B5 is fixed in CBS
`fa1740f` and the canary is flipped.

## B1 — CONTRACT.md §5.1 identity

- State: §5.1 is **not applied** to CONTRACT.md. The proposal is
  `docs/CONTRACT_PROPOSAL_5.1.md`; the contract owner must apply it.
- CBM behavior: `package_id != "cbm"` → exit 3,
  `cbm_gate_status=FAIL`, `reason=REPORT_IDENTITY_MISMATCH`,
  `upload_status=NOT_UPLOADED`.
- Evidence: `tests/test_exit_codes.py::test_identity_mismatch_exits_3`,
  `test_cbp_identity_mismatch_exits_3`, `test_cbs_report_is_not_reused`.

## B2 — real CBE report with `package_id: "cbm"`

- State: the CBP side is now real: `cbp-1.2.0-cbm-manifest.json`, sha
  `bc5461e6…`, `package_id: "cbm"`, `producer_id: "cbp"`, `base`. The CBE
  side is still missing; there is no real CBE report with `package_id: "cbm"`.
- CBM behavior: `load_report` can load the CBP manifest and B3 fields pass,
  but a full `verify` needs both reports; CBM must not synthesize the CBE side.
- Evidence: `tests/test_b3_cbp_rc.py::test_b3_manifest_is_cbm_scoped_but_b2_is_blocked`.
- B3 is **FIELD_LEVEL_COMPLETE**, not B2 complete.

## B5 — fixed (not blocked)

- CBS `fa1740f` emits `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT` (and the exact
  phrase when declared). `tools/check_b5.py --check-upstream` returns
  `STATUS=B5_MAYBE_FIXED`.
- `tests/test_known_fail_silent.py` is flipped; **no KNOWN_FAIL_SILENT canary
  remains**. A `STATUS=KNOWN_FAIL_SILENT` result is a regression and fails the
  test.

## No fake PASS

- No tag, GitHub Release, PyPI upload, or `PASS` claim for B1/B2.
- B3 is marked FIELD_LEVEL_COMPLETE; B4 FAIL_CLOSED_ONLY; B5 FIXED (`tests/test_known_fail_silent.py`).
- `91 passed = 91 normal tests`.
