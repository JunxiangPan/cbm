# CBF evidence external sidecar check — CBM 0.2.1

Status: **attachment read PASS / semantic attachment NOT_RUN / CBF gate NOT_RUN**

This check used the **published `cbm-attach 0.2.1`** installed from PyPI. It
loaded a real `cbf-evidence/v1` document through the generic evidence adapter.
It is not a `semantic-verdict/v1` attachment and is not a CBF gate PASS.

- Evidence: `cbc-event/tests/fixtures/cbf-evidence-pass.json`
- CBF `source_result`: `PASS` (the source document's own result)
- Evidence `evidence_sha256`: `bc0b31bc2243f5de5dcdbe67d79a9305f0b41859354ffe66c0dc2685e5ed2825`
- `schema_read`: **PASS**
- `generic_attachment_read`: **PASS**
- `identity`: **PASS**
- `cbf_gate`: **NOT_RUN**
- `semantic_model`: **NOT_RUN**
- CBF evidence hash verification: **NOT_RUN**

No semantic model was run. No CBF/CBP/CBE package was imported. The source CBF
result is not a CBM CBF PASS. Machine-readable result:
`docs/0.2.1/CBF_EVIDENCE_RELEASE_CHECK.json`.
