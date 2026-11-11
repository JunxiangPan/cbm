# Live upload E2E (test repository only)

- Repository: `JunxiangPan/cbm-e2e` (private, test-only)
- Release: https://github.com/JunxiangPan/cbm-e2e/releases/tag/e2e-v0.2.0rc1
- Asset: `cbm_attach-0.2.0rc1-py3-none-any.whl`
- Asset sha256: `d666c328121e1d3808010f5ea239d1db17bf9eeb12ae666e03c84f94a0e48d73`
- Test: `tests/live/test_live_upload.py`
- Covered: upload, readback digest/name, same-digest retry, missing-release
  failure (InputError `MISSING_RELEASE`).
- Production releases were not touched.
