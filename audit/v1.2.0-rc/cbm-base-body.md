# cbm v0.1.0 — base release body

This base body is assembled from the CBM README for the CBP 1.2.0 target
manifest. It is not an official GitHub Release body; CBM has no release yet.

## Status

- B5: fixed by CBS v1.7.0-integration `fa1740f`; CBM canary flipped.
- B3: field-level complete with a CBM-scoped CBP manifest; B2 is not claimed.
- B4: fail-closed only; CBE/CBS artifact repositories are not unified.
- B1: blocked; CONTRACT.md §5.1 is not applied.
- B2: blocked; there is no real CBE report with `package_id: "cbm"`.
- No tag, GitHub Release, or PyPI upload.

## Tests

102 offline/static tests pass on ubuntu-latest and windows-latest. The suite
contains no KNOWN_FAIL_SILENT canary.
