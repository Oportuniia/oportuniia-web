"""Static smoke check for MI OPORTUNIIA's private portal browser code."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
html = (ROOT / "frontend/public/mi-oportuniia.html").read_text(encoding="utf-8")
for required in [
    "/api/mi/auth/login", "/api/mi/auth/recovery/request",
    "/api/mi/private/documents/upload-intent",
    "/api/mi/private/premium/pdf/",
    "/api/mi/private/documents/",
    "oportuniia-logo.webp", 'id="profile-form"'
]:
    assert required in html, f"Missing private portal feature: {required}"

scripts = re.findall(r"<script(?:\\s[^>]*)?>(.*?)</script>", html, re.DOTALL)
assert len(scripts) == 1, "Expected exactly one inline portal script"
with tempfile.TemporaryDirectory() as d:
    path = Path(d) / "portal.js"
    path.write_text(scripts[0], encoding="utf-8")
    subprocess.run(["node", "--check", str(path)], check=True)
print("Private portal contracts and JavaScript syntax: OK")
