"""Build a deterministic integration-only release archive."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components" / "weekly_gate_scheduler"
OUTPUT = ROOT / "dist" / "weekly-gate-scheduler.zip"
OUTPUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(SOURCE.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            archive.write(path, path.relative_to(ROOT))
print(OUTPUT)
