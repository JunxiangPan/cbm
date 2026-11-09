# Proposed CONTRACT.md §5.1 — Report identity (not yet applied)

Status: **proposal only**. The frozen v1.7 contract is
`public-release/docs/v1.7/CONTRACT.md` at commit `4a437df`, SHA-256
`a561f19e0a8e4dba92af82400b5696da18e000ba5362571cb0b40243b9a3afca`.
This repository must not edit that file. This document is the change-control
input for the CBS contract owner.

Observed during CBM v0.1.0: the CBS working tree advanced past `eeb3645` and
added an additive §11 (build-once profiles). §5 and F1-F6 are unchanged. This
proposal still targets §5.1 and still requires the change-control process.

The full v1.7 hard-blocker list (identity, CBM-scoped reports, CBP P0-06,
artifact_repository, CBS body fail-silent) is in
[`docs/V17_BLOCKERS.md`](V17_BLOCKERS.md).

## Status warning

**CBM 0.1.0 must not be connected to real CBE/CBP reports yet.**

- Current CBE/CBP reports put the producer name in `package_id` (`"cbe"` /
  `"cbp"`). CBM requires `package_id == "cbm"` and exits 3
  `REPORT_IDENTITY_MISMATCH`, refusing upload.
- Current CBP quality manifests lack `release_body_hash` and
  `body_hash_scope`. CBM exits 2 `MISSING_RELEASE_BODY_HASH` or
  `MISSING_BODY_HASH_SCOPE`.
- Until §5.1 and §5.2 are applied and CBE/CBP P0-06 is implemented, CBM only
  accepts mock fixtures. Its 110 passing tests are static/offline evidence, not
  real-data E2E.

## Problem

§5's examples use `package_id: "cbe"` / `"cbp"` while §7's reusable workflow
uses `package_id` as an input for the package being verified. A consumer cannot
tell whether `package_id` means "the subject under test" or "the component that
produced the report". CBM cannot safely prove that a CBE/CBP report describes
the CBM wheel if the field is ambiguous.

## Proposed text

Add after §5 (Report Minimum Fields):

```text
### 5.1 Report identity

Every CBE report and CBP quality manifest MUST carry:

  package_id       = the subject package being verified (cbm, cbs, cbe, ...)
  producer_id      = the component that produced the report (cbe, cbp)
  producer_version = the producer's version

Consumers MUST validate package_id against their own package name. A mismatch
is a gate failure: exit 3, gate_status = FAIL, reason = REPORT_IDENTITY_MISMATCH.
A consumer MUST NOT guess the subject from the producer name and MUST NOT reuse
another package's report.

producer_id and producer_version are traceability fields only. They are never a
substitute for package_id and never change the subject identity.

Reports that predate this clause may omit producer_id / producer_version, but
they MUST still use the subject package in package_id. A report with a producer
name in package_id is invalid for consumption by another package.
```

## Proposed §5.2 — CBP body hash scope

Add after §5.1:

```text
### 5.2 CBP body hash scope

The CBP quality manifest MUST carry:

  release_body_hash = SHA-256 of the base Release body
  body_hash_scope   = "base" | "full"

CBM consumes base-scoped manifests only. A missing release_body_hash or
body_hash_scope exits 2. body_hash_scope "full" or any unknown value exits 2.
CBP P0-06 must implement both fields before CBM can consume real manifests.
```

## Required-field update

For the next contract revision (new version, not a retroactive edit), add to
the §5 CBE report and CBP quality manifest minimum fields:

```json
{
  "package_id": "cbm",
  "producer_id": "cbe",
  "producer_version": "1.7.0"
}
```

Add to the CBP quality manifest minimum fields:

```json
{
  "release_body_hash": "<64 hex>",
  "body_hash_scope": "base"
}
```

## Release-train artifact repository constraint

GitHub Actions artifact download is repository-bound. The v1.7 release train
must upload the **CBM build-once artifact, CBE report and CBP manifest to the
same `artifact_repository`**. If CBE/CBP upload in their own repositories, CBM
cannot download them. This is an orchestration requirement for the CBS train,
not something CBM can fix alone; add it to CONTRACT.md §11.

CBM 0.1.0 supports `artifact_type=wheel` only. A CBS `artifact_type=zip-bundle`
requires CBM 0.2.0. CBM does not sign and does not consume CBS's
`update-manifest.sig`; that is a CBS release asset, outside CBM's build-once
artifact.

Change control still applies: new contract version, `docs/v1.7/CHANGELOG.md`
entry, updated E2E matrices, no retroactive change to already published
evidence.

## Required train semantics (not yet in CONTRACT.md)

- CBE/CBP MUST run for the CBM subject and emit `package_id: "cbm"`. CBM MUST
  NOT reuse the CBS reports (`package_id: "cbs"`); reuse is exit 3
  `REPORT_IDENTITY_MISMATCH`. The current CBS mock reports use
  `package_id: "cbe"` / `"cbs"`, so they are not CBM inputs.
- If CBM evidence is completely absent, the CBS body generator MUST synthesize
  `CBM: NOT_UPLOADED` + `EVIDENCE_ABSENT` (and the exact "declared as attached
  but not uploaded" phrase when claimed). Current CBS
  `tools/release_body_v17.py` renders `- none`; this is an open CBS dependency,
  documented in `docs/CBS_BODY_REQUIREMENT.md`.

## CBM behaviour until this is applied

- CBM requires `package_id == "cbm"` for both reports.
- A producer name in `package_id` (`"cbe"` / `"cbp"`) produces exit 3,
  `cbm_gate_status=FAIL`, `reason=REPORT_IDENTITY_MISMATCH`, no upload.
- `producer_id` / `producer_version` are recorded when present and recorded as
  `null` when absent. They do not affect the gate.
- CBM requires `release_body_hash` and `body_hash_scope: "base"` from CBP.
  Missing either field exits 2; `"full"` exits 2
  `BODY_HASH_SCOPE_UNSUPPORTED`.
- CBM records `cbp_release_body_hash` and `cbp_body_hash_scope` in its report and
  body fragment for downstream body/CBC checks.
- CBM does not borrow the CBS reports for a CBM attachment, and does not
  synthesize a missing subject field.
