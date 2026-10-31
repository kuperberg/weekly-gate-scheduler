import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_release_files_and_versions_are_consistent():
    for name in ("README.md", "LICENSE", "hacs.json", ".github/workflows/validate.yml"):
        assert (ROOT / name).is_file(), name
    manifest = json.loads((ROOT / "custom_components/weekly_gate_scheduler/manifest.json").read_text())
    assert manifest["version"] == "0.1.3"
    assert (ROOT / "custom_components/weekly_gate_scheduler/www/weekly-gate-scheduler-card.js").is_file()


def test_public_files_contain_no_token_or_password_material():
    forbidden = ("X-Access-Token", "eyJ0eXAi", "portal_password")
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", ".venv", ".superpowers", "superpowers", "tests", ".pytest_cache"} for part in path.parts):
            continue
        if path.suffix in {".pyc", ".zip"}:
            continue
        text = path.read_text(errors="ignore")
        assert not any(value in text for value in forbidden), str(path)
