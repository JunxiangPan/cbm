# semantic-verdict/v1 sidecar

Status: optional attachment; **CBM does not run a semantic model**.

`semantic-verdict/v1` is a standalone JSON artifact supplied by an external
reviewer. CBM validates its schema and canonical `evidence_sha256`, then copies
it as an attachment. It does not modify the CBM report, the 0.1.1 schema or the
0.2.0 sidecar contract.

## Schema

Required fields:

- `schema`: `semantic-verdict/v1`
- `verdict`: `PASS` / `FAIL` / `NOT_RUN`
- `subject.package_id`
- `subject.artifact_sha256` (64 hex)
- `generated_at`
- `evidence_sha256`: SHA-256 of canonical JSON excluding this field

Optional: `subject.version`, `findings`, `policy`.

## CLI

```bash
cbm-attach verify-semantic --verdict semantic-verdict.json
cbm-attach attach-semantic --verdict semantic-verdict.json --output-dir semantic-out
```

The attach command writes `semantic-verdict.json` and a standalone
`semantic-attachment.json` manifest. It does not change `cbm-report.json`.
CBM never imports CBF/CBP/CBE and never runs a semantic model.
