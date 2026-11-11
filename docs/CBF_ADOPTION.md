# CBF adoption — CBM

Status: **PENDING_CBF_0.1.0**

- surfaces: `git` / `api` / `local-ai`
- planned gate: `cbf gate --surface git`
- planned CI job: `cbf-privacy-gate`
- evidence format: `cbf-evidence/v1`

CBM has **not** integrated CBF. There is **no CBF PASS**, and CBM does not
claim CBF compatibility. CBF is an independent project; CBM does not import
it and does not require it to be installed.

## Phase 0 (current)

- Adoption documented here.
- The `cbf-privacy-gate` CI job name is reserved in this document only; no
  workflow file is added in Phase 0.
- Existing CI does not fake a CBF result and does not use `continue-on-error`
  or `if: false` to bypass it.
- No GitHub Release, PyPI upload, or git push is claimed to have CBF evidence.

## Phase 1 (after CBF 0.1.0rc1)

- Add `cbf.policy.json` pinned to the CBF policy version/hash.
- Wire `cbf-privacy-gate` into the release/upload path and add the local
  pre-push `cbf gate --surface git`.
- Block upload/release on CBF failure; record `cbf-evidence/v1`.

## CBM contract boundary

- CBF evidence may be attached as an **optional artifact**. It is not a required
  field and does not change the CBM 0.1.1 or 0.2.0 sidecar contract, schema,
  report, or upload decision.
- CBM does not import CBF and does not require CBF to be installed.
- After CBF adoption, GitHub push / Release / PyPI / cloud-AI / local-AI use
  must have CBF PASS. CBF 0.1.0 is not released yet, so there is no CBF PASS and
  this repository remains Phase 0 documentation-only.
