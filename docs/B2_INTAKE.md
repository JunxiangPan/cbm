# B2 intake — real CBM-scoped CBE report

Status: **BLOCKED until CBE produces a real report with `package_id: "cbm"`.**
No CBM 0.1.0 RC is created from the synthetic fixture.

## Required inputs

1. A real CBE report produced by CBE, with:
   - `package_id: "cbm"`
   - `producer_id: "cbe"`
   - `version: "v0.1.0"`
   - `tag: "v0.1.0"`
   - `gate_status: "PASS"` (or a real failure that is not waived)
2. The CBP 1.2.2 CBM manifest:
   - `audit/v1.2.0-rc/cbm-quality-manifest.json`
   - sha256 `b41798f07be4dda35e2afa1a810381bcd6f5025fb5d33f5c5a1054834a390c82`
   - `package_id: "cbm"`, `producer_id: "cbp"`, `v0.1.0`, object
     `artifact_repository`, `body_hash_scope: "base"`, `gate_status: "PASS"`.
3. The build-once artifact described by the manifest (wheel
   `cbm_attach-0.1.0-py3-none-any.whl`, sha256
   `02bf840016f5a2630c70ab42286c3ea47c0091c5efb77c0429c3060c0bee8015`)
   or a newly built artifact set whose hashes are recorded consistently.

The synthetic fixture
`tests/fixtures/cbe-cbm-scoped.synthetic.json` is **not** an input. It is marked
`not_upstream_evidence` and may only be used for schema/identity readiness.

## Validation before any RC

```bash
cd D:\qq苏瑾言大肥鱼\cbm
python - <<'PY'
from cbm_attach.reports import identity_errors, load_report
cbe = load_report(r"<real-cbe-report>.json", "cbe")
cbp = load_report(r"audit/v1.2.0-rc/cbm-quality-manifest.json", "cbp")
print("CBE", cbe.package_id, cbe.producer_id, cbe.version, cbe.data.get("tag"))
print("CBP", cbp.package_id, cbp.producer_id, cbp.version)
print("identity_errors", identity_errors(cbe, cbp, version="v0.1.0", tag="v0.1.0"))
PY
```

Expected on real input:

```text
CBE cbm cbe v0.1.0 v0.1.0
CBP cbm cbp v0.1.0
identity_errors []
```

If `identity_errors` is non-empty, or the CBE report is synthetic/missing, B2
stays **BLOCKED**; do not rewrite the result to PASS.

## CBM 0.1.0 RC gate

Only after the real-report check passes:

1. Build the artifact set from the CBM commit under test.
2. Re-run the CBM test suite and CI.
3. Generate the CBM target gate/manifest with CBP 1.2.2 if any input changed.
4. Record the real CBE report hash, gate report hash, manifest hash and artifact
   hashes in `audit/v1.2.0-rc/`.
5. Ask for human approval before any tag/release.

No tag, release, or PyPI upload is created by this intake step.
