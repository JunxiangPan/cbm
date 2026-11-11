# ADR 0001 — 0.2.0 sidecar attachment upgrade

Status: accepted for 0.2.0rc1, not stable

## Context

0.1.x consumed CBE/CBP-specific report fields and verified only Python wheels.
The next step needs generic evidence, CBS zip-bundles, and independently
verifiable in-toto Statements, without becoming a runtime DLP or a second CBP.

## Decision

1. Keep `cbm_attach` as the import package and `cbm-attach` as the distribution
   and console script.
2. Add pluggable evidence adapters. CBE/CBP remain built-in adapters, but are
   optional inputs; no CBE/CBP package is imported.
3. Add `artifact_type: wheel | zip-bundle`. Zip bundles verify
   `RELEASE_ASSETS.sha256`, record the bundle digest and manifest SHA256, and
   reject tampered/missing inventory entries.
4. Emit schema_version `"2"` reports with `artifact_type` and
   `bundle_manifest_sha256`; keep `schemas/cbm-report-v1.schema.json` for
   0.1.1 reports. Never silently remove a 0.1.x field.
5. Emit unsigned in-toto Statement v1 with
   `predicateType=https://cbm.dev/attachment/v1`; add an independent
   `verify-statement` command. No signatures are invented.
6. Use a private test repository for live GitHub Release upload/readback.
   Production releases are never used for live tests.

## Consequences

- 0.1.1 reports remain readable; 0.2.0 outputs require consumers to accept
  schema_version `"2"`.
- Zip-bundle support covers the CBS profile's inventory and manifest, not the
  RSA signing ceremony (that remains a CBS/CBP responsibility).
- External verifiers can validate the Statement structure and report binding,
  but cannot verify a signature that was never produced.
