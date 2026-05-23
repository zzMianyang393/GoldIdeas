from __future__ import annotations

import os
import shutil
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "release"
STAGING_DIR = RELEASE_DIR / "goldideas-release"
ZIP_PATH = RELEASE_DIR / "goldideas-release.zip"


SERVER_FILES = [
    "ai_jobs.py",
    "ai_providers.py",
    "ai_reports.py",
    "app.py",
    "demand_pipeline.py",
    "requirements.txt",
    "storage.py",
]


def clean() -> None:
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    STAGING_DIR.mkdir(parents=True, exist_ok=True)


def copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def write_text(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def stage_release() -> None:
    server_target = STAGING_DIR / "server"
    server_target.mkdir(parents=True, exist_ok=True)
    for filename in SERVER_FILES:
        shutil.copy2(ROOT / "server" / filename, server_target / filename)

    dist_dir = ROOT / "web" / "dist"
    if not (dist_dir / "index.html").exists():
        raise RuntimeError("web/dist/index.html was not found. Run npm run build in web/ first.")
    copy_tree(dist_dir, STAGING_DIR / "web" / "dist")

    shutil.copy2(ROOT / "README.md", STAGING_DIR / "README.md")
    write_text(STAGING_DIR / "requirements.txt", (ROOT / "server" / "requirements.txt").read_text(encoding="utf-8"))

    write_text(
        STAGING_DIR / "run-server.sh",
        """#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export GOLDIDEAS_HOST="${GOLDIDEAS_HOST:-0.0.0.0}"
export GOLDIDEAS_PORT="${GOLDIDEAS_PORT:-8765}"
python server/app.py
""",
        executable=True,
    )
    write_text(
        STAGING_DIR / "run-server.cmd",
        """@echo off
cd /d "%~dp0"
py -3 -m venv .venv
call .venv\\Scripts\\activate.bat
pip install -r requirements.txt
set GOLDIDEAS_HOST=%GOLDIDEAS_HOST%
if "%GOLDIDEAS_HOST%"=="" set GOLDIDEAS_HOST=0.0.0.0
set GOLDIDEAS_PORT=%GOLDIDEAS_PORT%
if "%GOLDIDEAS_PORT%"=="" set GOLDIDEAS_PORT=8765
python server\\app.py
""",
    )
    write_text(
        STAGING_DIR / "DEPLOY.md",
        """# GoldIdeas Release Deployment

This package contains the Python backend and the prebuilt frontend in `web/dist`.

## Linux server

```bash
unzip goldideas-release.zip
cd goldideas-release
chmod +x run-server.sh
GOLDIDEAS_PUBLIC_BASE_URL=https://your-domain.com ./run-server.sh
```

Default server URL:

```text
http://0.0.0.0:8765
```

Override the port:

```bash
GOLDIDEAS_PORT=8888 ./run-server.sh
```

## Windows server

```cmd
run-server.cmd
```

## Public URL

Set this in production so sitemap, RSS, JSON feed, and llms.txt use your domain:

```bash
export GOLDIDEAS_PUBLIC_BASE_URL=https://your-domain.com
```

## Runtime data

Runtime data is created in:

```text
server/data/
```
""",
    )


def zip_release() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in STAGING_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(RELEASE_DIR))


def main() -> None:
    clean()
    stage_release()
    zip_release()
    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"Created {ZIP_PATH} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
