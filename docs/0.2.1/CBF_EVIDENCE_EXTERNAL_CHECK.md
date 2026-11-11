# CBF evidence external attachment check

Status: **PASS (attachment read only) / CBF gate NOT_RUN / semantic model NOT_RUN**

This check used the **released `cbm-attach 0.2.0`** installed from PyPI. It
loaded a real `cbf-evidence/v1` fixture through the 0.2.0 generic evidence
adapter and checked schema/read/identity only.

- Evidence: `cbc-event/tests/fixtures/cbf-evidence-pass.json`
- CBF `source_result`: `PASS` (the source document's own result)
- Evidence `evidence_sha256`: `bc0b31bc2243f5de5dcdbe67d79a9305f0b41859354ffe66c0dc2685e5ed2825`
- Attachment `schema_read`: **PASS**
- Attachment `generic_attachment_read`: **PASS**
- Attachment `identity`: **PASS**
- `cbf_gate`: **NOT_RUN** (CBF 0.1.0 is not released)
- `semantic_model`: **NOT_RUN**
- CBF evidence hash verification: **NOT_RUN**

The source CBF result is not a CBM CBF PASS and was not converted into one.
No CBF/CBP/CBE package was imported. The result is recorded in
`docs/0.2.1/CBF_EVIDENCE_EXTERNAL_CHECK.json`.
