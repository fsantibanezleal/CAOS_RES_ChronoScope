"""Direct bake entry point. Invoke as `python scripts/bake.py [case|all] [--seed N]` instead of
`python -m chronoscopelab.pipeline`: on the Windows build box, the `-m` runpy invocation on the D: drive
opens a transactional-NTFS context that breaks artifact writes (WinError 6714); a direct script call does not.
See docs/architecture/09_known-issues.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-pipeline"))

from chronoscopelab.pipeline import main  # noqa: E402

if __name__ == "__main__":
    main()
