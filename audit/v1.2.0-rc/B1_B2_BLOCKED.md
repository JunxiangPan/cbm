# B1 active / B2 blocked (B5 fixed; no fake PASS)

CBM v0.1.0 consumer status after CONTRACT v1.7.1 froze §5.1.

## B1 — CONTRACT_ACTIVE

- Contract: `contract-v1.7.1` / `209d75b4`; §5.1 is frozen and active.
- Subject: `package_id: "cbm"`.
- Producer: `producer_id: "cbe"` or `"cbp"`.
- CBM readiness tests (`tests/test_b1_identity.py`, 6 tests): accept the
  subject/producer pair; reject old `package_id: "cbe"/"cbp"` and producer
  mismatch; mixed reports exit 3 `REPORT_IDENTITY_MISMATCH`.
- This is consumer-side active; it does not by itself prove the full train.
  `REPORT_IDENTITY_MISMATCH` tests are retained.

## B2 — BLOCKED

- Still no real CBE report with `package_id: "cbm"` + `producer_id: "cbe"`.
- `tests/test_b2_readiness.py` uses
  `cbe-cbm-scoped.synthetic.json`, explicitly marked
  `not_upstream_evidence`. It proves schema/identity readiness only.
- Do not claim B2 PASS; no synthetic CBE report is presented as real evidence.

## B5 — fixed

CBS `fa1740f` emits `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`; the canary is
flipped and no `KNOWN_FAIL_SILENT` marker remains.

## No fake PASS

- No tag, GitHub Release, or PyPI upload.
- B2 remains blocked; B4 remains fail-closed only.
- `108 passed = 108 normal tests` (with the pinned CBS fixture).
