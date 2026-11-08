# Fixtures

The report and build-once fixtures are generated inside `tmp_path` by
`tests/helpers.py` so the wheel digest, `WHEEL_SHA256`,
`RELEASE_ASSETS.sha256`, and CBP `artifact_hashes` always agree. Static JSON
fixtures with hard-coded hashes would drift silently.

To add a new scenario, add a `make_cbe` / `make_cbp` override or a small
builder in `tests/helpers.py`, then add the case to `docs/E2E.md`.
