# CBM B2 claims handoff to CBP

Status: **BLOCKED on artifact choice; claims gate is fixed.**

## Claims inputs (CBM-provided, real)

- `cbm-claims-manifest.json` sha256: see `audit/v1.2.0-rc/SHA256SUMS`
  - 3 PASS / 5 claims: B1 contract active, B3 field-level, B5 fixed;
    B2 and B4 are SKIPPED and explicitly not claimed.
- `cbm-claims-notes.md` — exactly one `QUALITY_COUNTS: 3/5` and
  `across 5 gates`.

Official CBP 1.2.2 target gate with these inputs:

```text
claims: PASS claims=3/5
CBP_GATE_STATUS=PASS
```

Evidence: `audit/v1.2.0-rc/cbm-target-gate-with-claims.json`.

## Artifact choice — unresolved

The instruction requires one exact artifact, no mixing:

- f605808 wheel `65174c9b6deab9f962fb63cb21721d1077c634b021fcec879731127e49558c65`
  — **not retained**. Fresh builds from f605808 produce different hashes
  (`94391185881bf975ba6735272b9c41d6635a68183eb19a13118b32db2f35e751` in the
  latest build).
- CBP manifest wheel `02bf840016f5a2630c70ab42286c3ea47c0091c5efb77c0429c3060c0bee8015`
  — **not retained**.

No new CBM manifest was generated, because doing so would bind a fresh wheel to
an old manifest. CBP/owner must provide or retain exactly one of the two
artifacts, then regenerate the target manifest with that exact file.

## Remaining F3 gates

The claims-PASS gate report still has `binary`, `docs`, and `custom` as
`SKIPPED (not configured)`. CBM F3 treats those as blocking; they need real CBP
configuration or a contract-owner decision.

## No publish

No CBM tag, release, PyPI upload, or RC. B2/B4 remain blocked until an exact
artifact is bound and CBM's own gate exits 0.
