# v1.7 release-train blockers (CBM perspective)

Status: **B5 fixed; B3 field-level complete; B1/B2 blocked; B4 fail-closed only.**
No tag, release, or PyPI publish. CBM cannot close B1/B2/B4 inside its own
repository.

## Blocker list

| ID | Status | Blocker / evidence |
| --- | --- | --- |
| B1 | **BLOCKED** | CONTRACT.md §5.1 is not applied: `package_id` remains ambiguous. Consumer readiness tests cover package/producer identity and old-field mixing; any violation exits 3 `REPORT_IDENTITY_MISMATCH`. |
| B2 | **BLOCKED** | No real CBE report with `package_id: "cbm"`. The CBP side now exists (`bc5461e6…`); a synthetic CBE fixture/schema readiness test exists but is marked `not_upstream_evidence`. Full identity needs both real sides. |
| B3 | **FIELD_LEVEL_COMPLETE** | CBP 1.2.0 RC `855fed7` produced a CBM-scoped manifest: `body_hash_scope: "base"`, `release_body_hash`, two `artifact_hashes`, `evidence_sha256`. Missing/full scope exits 2. This is not B2. |
| B4 | **FAIL_CLOSED_ONLY** | Cross-repository and missing `artifact_repository` exit 2 `ARTIFACT_REPOSITORY_MISMATCH`; same repository (case-insensitive) continues. Boundary tests added; CBE/CBS are still not unified, so B4 is not complete. |
| B5 | **FIXED** | CBS v1.7.0-integration `fa1740f` (`tests/test_known_fail_silent.py`) emits a visible `## CBM` section with `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT`; canary flipped. Historical `- none` behavior is gone. |

## Dependency order

```text
B1 §5.1 (package_id = subject)
  -> B2 real CBE report with package_id: "cbm" + producer_id
     -> B3 field-level manifest  +  B4 artifact_repository
        (both required for full CBM consumption)

B5 CBS body generator (independent; FIXED in fa1740f; tests/test_known_fail_silent.py)
```

- B1 not landed -> B2 cannot start.
- B2 not landed -> full CBM consumption cannot pass; B3 is field-level only.
- B3 alone or B4 alone -> CBM still exits 2 for full consumption.
- B5 is fixed and no longer a blocker.

## B3 + B4 are a compound blocker for full consumption

| Solved | Not solved | CBM result |
| --- | --- | --- |
| B3 field-level | B4 | exit 2 `ARTIFACT_REPOSITORY_MISMATCH` / `MISSING_*` |
| B4 | B2 | exit 2/3 `REPORT_IDENTITY_MISMATCH` or missing CBE report |
| B3 + B4 | B2 | still blocked by identity; cannot claim full PASS |

## B5 is fixed (historical requirement)

CBS `fa1740f` changes `tools/release_body_v17.py` to synthesize structured CBM
and CBC records. The probe now returns:

```text
STATUS=B5_MAYBE_FIXED
CBM: NOT_UPLOADED
reason: EVIDENCE_ABSENT
declared_attached: false
```

With `declared_components: ["cbm"]`, the exact phrase
`declared as attached but not uploaded` is emitted. The old
`KNOWN_FAIL_SILENT` canary in `tests/test_known_fail_silent.py` is flipped to
assert this fixed state; the file name is retained as history. No
`KNOWN_FAIL_SILENT` marker remains in the suite.

Probe maintenance:

| Output | Exit | Meaning |
| --- | --- | --- |
| `STATUS=B5_MAYBE_FIXED` | 0 | expected fixed state; B5 test green |
| `STATUS=KNOWN_FAIL_SILENT` | 0 | old/failed CBS behavior; B5 test fails as regression |
| `SKIP_REASON=CBS_BODY_GENERATOR_NOT_FOUND` | 0 | CBS checkout missing; test skips |
| `FAIL_REASON=CBS_BODY_GENERATOR_UNIMPORTABLE` | 3 | CBS file exists but import/build fails; test fails |
| `FAIL_REASON=UNEXPECTED_OUTPUT` | 2 | neither old defect nor fixed; inspect |

## Checklist

```text
[x] B3  CBM-scoped manifest fields (body_hash_scope/release_body_hash/
        artifact_hashes/evidence_sha256) — field-level complete
[ ] B1  CONTRACT.md §5.1: package_id = subject, producer_id = producer
[ ] B2  real CBE report with package_id="cbm" + producer_id
[ ] B4  artifact_repository unified for build-once + CBE + CBP artifacts
[x] B5  CBS body generator: missing CBM -> CBM: NOT_UPLOADED + EVIDENCE_ABSENT
```

**102 tests pass (102 normal; no KNOWN_FAIL_SILENT canary).** A-F live E2E is
still not executed. The audit package is `audit/v1.2.0-rc/`.
