# CBS body generator requirement — B5 (fixed)

Status: **FIXED in CBS v1.7.0-integration `fa1740f`** (regression `tests/test_known_fail_silent.py`). This document is retained
as the historical requirement and regression contract. The old
`KNOWN_FAIL_SILENT` canary has been flipped; no `known_fail_silent` marker
remains in the CBM suite.

## Historical gap

At CBS HEAD `88ec90f`, `public-release/tools/release_body_v17.py` did:

```text
not_uploaded = report.get("not_uploaded", [])
lines += [f"- {item}" for item in not_uploaded] or ["- none"]
```

A completely missing CBM rendered `- none`; `CBM: NOT_UPLOADED` and
`EVIDENCE_ABSENT` were absent. That was fail-silent, not fail-closed.

## Fixed behavior (`fa1740f`)

The fixed generator synthesizes structured CBM/CBC records. For a missing CBM:

```markdown
## CBM

- CBM: NOT_UPLOADED
  - cbm_gate_status: `NOT_UPLOADED`
  - upload_status: `NOT_UPLOADED`
  - reason: `EVIDENCE_ABSENT`
  - declared_attached: `false`
- Skip accounting: NOT_UPLOADED is not counted in the SKIP ratio (F6).
```

With `declared_components: ["cbm"]` it sets `declared_attached: true` and emits
the exact phrase:

```text
declared as attached but not uploaded
```

The CBM record is a dedicated `## CBM` section, not necessarily under
`## NOT_UPLOADED`. That is accepted because F6 requires visibility and the exact
phrase when claimed, both of which are present.

## CBM-side evidence (still true)

When `cbm_attach finalize` runs but finds no evidence artifact, it writes:

- `cbm_gate_status = SKIPPED_INFRA`
- `reason = EVIDENCE_ABSENT`
- `reason_detail` contains `WORKFLOW_FAILED_BEFORE_EVIDENCE`
- `upload_status = NOT_UPLOADED`
- body includes `CBM: NOT_UPLOADED` and the exact phrase if claimed

This covers "CBM ran but lost its evidence". CBS `fa1740f` covers "CBM never
ran"; no B5 gap remains.

## Regression test and probe

`tests/test_known_fail_silent.py` is flipped in place:

- asserts `CBM: NOT_UPLOADED`, `EVIDENCE_ABSENT`, no `- none`;
- asserts `declared_attached: true` and the exact phrase in the declared case;
- keeps the probe's missing/import/unexpected maintenance checks;
- a missing CBS checkout skips with
  `SKIP_REASON=CBS_BODY_GENERATOR_NOT_FOUND`; an unimportable CBS file fails
  with `FAIL_REASON=CBS_BODY_GENERATOR_UNIMPORTABLE`.

Probe CLI:

```bash
python tools/check_b5.py --check-upstream
python tools/check_b5.py --check-upstream --declared-cbm
```

| Output | Exit | Meaning |
| --- | --- | --- |
| `STATUS=B5_MAYBE_FIXED` | 0 | expected fixed state; test green |
| `STATUS=KNOWN_FAIL_SILENT` | 0 | old/failed CBS behavior; test fails as regression |
| `SKIP_REASON=CBS_BODY_GENERATOR_NOT_FOUND` | 0 | environment missing; test skips |
| `FAIL_REASON=CBS_BODY_GENERATOR_UNIMPORTABLE` | 3 | CBS import/build failure; test fails |
| `FAIL_REASON=UNEXPECTED_OUTPUT` | 2 | neither old defect nor fixed; inspect |

Do not flip the assertion back to `- none`.
