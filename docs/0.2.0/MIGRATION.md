# Migration: 0.1.1 -> 0.2.0

## Reports

- 0.1.1 reports have `schema_version: "1"` and are still valid under
  `schemas/cbm-report-v1.schema.json`.
- 0.2.0 reports use `schema_version: "2"` and add:
  - `artifact_type`: `"wheel"` or `"zip-bundle"` (null only on early error).
  - `bundle_manifest_sha256`: hash of `bundle-manifest.json` /
    `update-manifest.json` for zip-bundles, otherwise null.
- No 0.1.1 field is removed or renamed.
- Old readers that hard-code `schema_version == "1"` must accept `"2"` or use
  the v1 schema only for old reports.

## Artifacts

- Wheel:
  `cbm-attach verify --build-once-dir ... --artifact-type wheel`
- Zip-bundle:
  `cbm-attach verify --build-once-dir ... --artifact-type zip-bundle`
- Zip-bundle requires `RELEASE_ASSETS.sha256`; `BUNDLE_SHA256` is optional.
  The bundle manifest is read from `bundle-manifest.json` or
  `update-manifest.json` (root or inside the zip).

## Evidence

Built-in `cbe`/`cbp` adapters keep the existing CLI. Custom adapters can call
`cbm_attach.evidence.register_adapter(kind, loader)` and
`load_generic(path, kind)`; they do not need CBE/CBP installed.

## in-toto

`verify`/`upload` write `<report>.statement.json` by default. Validate with:

```bash
cbm-attach verify-statement --statement cbm-report.statement.json \
  --report cbm-report.json
```

The Statement is unsigned. Do not describe it as signed or attested.
