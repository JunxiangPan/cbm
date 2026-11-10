# PyPI status — cbm-attach 0.1.1

Status: **BLOCKED_NO_PYPI_CREDENTIALS**

- No `TWINE_USERNAME` / PyPI token / trusted-publisher workflow is configured.
- `https://pypi.org/pypi/cbm-attach/json` returns HTTP 404.
- No `twine upload` was attempted and no PyPI PASS is claimed.
- Distribution and console script are available via the exact GitHub Release
  wheel; `pip install cbm-attach==0.1.1` cannot succeed until publication.
- GitHub Release: https://github.com/JunxiangPan/cbm/releases/tag/v0.1.1
