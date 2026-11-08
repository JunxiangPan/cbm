# v1.7 release-train hard blockers (CBM perspective)

Status: **hard blockers for the v1.7 release train**, not CBM documentation
risks. CBM cannot close these inside its own repository.

## Blocker list

| ID | Blocker | Owner | CBM behaviour until fixed |
| --- | --- | --- | --- |
| B1 | CONTRACT.md §5.1 is not applied: `package_id` is still ambiguous | CBS contract owner | CBM requires `package_id == "cbm"`; producer names exit 3 `REPORT_IDENTITY_MISMATCH` |
| B2 | CBE/CBP do not emit a CBM-scoped report (`package_id: "cbm"` + `producer_id`) | CBE/CBP + CBS train | CBM cannot reuse CBS reports; it exits 3 or has no input |
| B3 | CBP P0-06 is not implemented: no `release_body_hash` + `body_hash_scope: "base"` | CBP | exit 2 `MISSING_RELEASE_BODY_HASH` / `MISSING_BODY_HASH_SCOPE` / `BODY_HASH_SCOPE_UNSUPPORTED` |
| B4 | `artifact_repository` is not unified: CBE/CBP/CBS artifacts live in separate repositories | CBS orchestration + CBE/CBP | exit 2 `MISSING_BUILD_ONCE_ARTIFACT` / `MISSING_CBE_REPORT` / `MISSING_CBP_REPORT` |
| B5 | CBS body generator writes `- none` when the CBM report is completely missing | CBS | fail-silent: CBM is invisible instead of `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT` |

## B3 + B4 are a compound blocker

They must be solved together. Solving only one still leaves CBM at exit 2:

| Solved | Not solved | CBM result |
| --- | --- | --- |
| B3 only | B4 | exit 2 `MISSING_BUILD_ONCE_ARTIFACT` / `MISSING_CBE_REPORT` / `MISSING_CBP_REPORT` |
| B4 only | B3 | exit 2 `MISSING_BODY_HASH_SCOPE` (or `MISSING_RELEASE_BODY_HASH`) |
| B3 + B4 | — | artifact/body stage can pass |

Do not report "CBM is one step away" after solving only one of them.

## B5 is fail-silent, not fail-closed

Audited CBS source:

```text
public-release/tools/release_body_v17.py:20
  not_uploaded = report.get("not_uploaded", [])
public-release/tools/release_body_v17.py:39
  lines += [f"- {item}" for item in not_uploaded] or ["- none"]
```

If CBM never runs (or its evidence is completely absent), the body renders
`- none`; it does not render `CBM: NOT_UPLOADED` or `EVIDENCE_ABSENT`. F6 says
NOT_UPLOADED must be visible; `- none` is a third, invisible state.

Proof in this repository:

- `tests/test_known_fail_silent.py::test_known_fail_silent_cbs_body_omits_missing_cbm`
  loads the real CBS `release_body_v17.py` and asserts the current `- none`
  output, no `CBM`, and no `EVIDENCE_ABSENT`; marker `known_fail_silent`.
- If the CBS checkout is absent, the test uses a mock that reproduces the exact
  audited lines, so the known gap is still recorded rather than skipped.
- Proposed CBS fix and test: `docs/CBS_BODY_REQUIREMENT.md`.

## Hard-blocker checklist

```text
[ ] B1  CONTRACT.md §5.1: package_id = subject, producer_id = producer
[ ] B2  CBE/CBP emit CBM-scoped package_id="cbm" reports; no CBS-report reuse
[ ] B3  CBP P0-06: release_body_hash + body_hash_scope="base"
[ ] B4  artifact_repository unified for build-once + CBE + CBP artifacts
[ ] B5  CBS body generator: missing CBM -> CBM: NOT_UPLOADED + EVIDENCE_ABSENT,
        not "- none"; exact phrase when the train claims CBM attached
```

Until all five are checked, CBM's 84 static tests prove logic on fixtures, not
real-data readiness. A–F live E2E remains unexecuted.
