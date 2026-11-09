## CBM

- CBM: NOT_UPLOADED
  - cbm_gate_status: `NOT_UPLOADED`
  - upload_status: `NOT_UPLOADED`
  - reason: `EVIDENCE_ABSENT`
  - declared_attached: `true`
- Skip accounting: NOT_UPLOADED is not counted in the SKIP ratio (F6).
declared as attached but not uploaded

## CBC

- CBC: NOT_UPLOADED
  - cbc_gate_status: `NOT_UPLOADED`
  - upload_status: `NOT_UPLOADED`
  - reason: `EVIDENCE_ABSENT`
  - declared_attached: `false`
- Skip accounting: NOT_UPLOADED is not counted in the SKIP ratio (F6).

## Section B: AI audit (non-blocking)

- AI gate results are audit-only; they do not replace Section A.

## Honesty boundary

CBE verifies the rule framework, CBP verifies evidence coherence. Neither
proves that the code is secure. NOT_UPLOADED is not PASS, SKIPPED_INFRA is
not PASS, and a green CI run is not a substitute for VM acceptance.
