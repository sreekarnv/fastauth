import shutil
import sys
from datetime import datetime
from pathlib import Path

import pytest


def run_tests_with_coverage() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("test-results") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    args = [
        "--cov=fastauth",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term-missing:skip-covered",
        "--cov-fail-under=95",
        "-v",
    ]
    args.extend(sys.argv[1:])

    exit_code = pytest.main(args)

    for src, dst_name in [
        ("htmlcov", "htmlcov"),
        ("coverage.xml", "coverage.xml"),
        (".coverage", ".coverage"),
    ]:
        src_path = Path(src)
        if src_path.exists():
            dst_path = output_dir / dst_name
            if dst_path.exists():
                shutil.rmtree(dst_path) if dst_path.is_dir() else dst_path.unlink()
            shutil.move(str(src_path), str(dst_path))

    print(f"\nCoverage reports saved to: {output_dir}")
    sys.exit(exit_code)


if __name__ == "__main__":
    run_tests_with_coverage()
