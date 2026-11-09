# B1 active / B2 blocked at CBM gate (no fake PASS)

CBM v0.1.0 consumer status after CONTRACT v1.7.1 froze §5.1.

## B1 — CONTRACT_ACTIVE

- Contract: `contract-v1.7.1` / `209d75b4`; §5.1 is frozen and active.
- Subject: `package_id: "cbm"`; producer: `producer_id: "cbe"` / `"cbp"`.
- Tests: `tests/test_b1_identity.py` (6 tests) accept the pair; reject old
  `package_id: "cbe"/"cbp"` and producer mismatch; mixed reports exit 3
  `REPORT_IDENTITY_MISMATCH`.

## B2 — BLOCKED (real report received, CBM gate failed)

Inputs:

- Real CBE report: `cbe-report.json`, sha256
  `6b4dc1efd8433535efe70d4de9337910aa537fbcc982ebba3a014284f27fc76e`;
  `package_id=cbm`, `producer_id=cbe`, `version/tag=v0.1.0`, `gate_status=PASS`.
- CBP 1.2.2 manifest: `cbm-quality-manifest.json`, sha256
  `b41798f07be4dda35e2afa1a810381bcd6f5025fb5d33f5c5a1054834a390c82`;
  `package_id=cbm`, `producer_id=cbp`, `v0.1.0`, `PASS`, object repo.

Identity:

```text
identity_errors []
```

CBM gate:

```text
CBM_VERIFY exit 3
reason BLOCKING_SKIP
detail CBP blocking gate 'claims' is SKIPPED (F3)
artifact_sha256 65174c9b...
cbp_artifact_sha256 02bf8400...
decision NO_UPLOAD
```

Two independent blockers remain:

1. CBP 1.2.2 target manifest has `claims` SKIPPED with reason
   `not configured`; CBM F3 treats `claims` as a blocking gate.
2. The manifest wheel `02bf8400…` does not match the wheel rebuilt from the
   CBE-validated CBM source `f605808` (`65174c9b…`).

B2 therefore stays **BLOCKED**; no CBM 0.1.0 RC is created. Evidence:
`audit/v1.2.0-rc/cbe-report.json`, `b2-gate-failure.json`,
`b2-gate-failure.stdout.txt`, `b2-gate-failure-decision.json`.

The synthetic fixture remains marked `not_upstream_evidence`; it is not B2
evidence.

## B4 — fail-closed only

Object manifest shape is parsed and 12 boundary tests pass; the object repository
matches `JunxiangPan/cbm`. Because the overall CBM gate failed, B4 remains
FAIL_CLOSED_ONLY; CBE/CBS repository unification is not claimed.

## B5 — fixed

CBS `fa1740f` emits `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`; the canary is
flipped and no `KNOWN_FAIL_SILENT` marker remains.

## No fake PASS

- No tag, GitHub Release, PyPI upload, or CBM 0.1.0 RC.
- `110 passed = 110 normal tests` (with the pinned CBS fixture).
