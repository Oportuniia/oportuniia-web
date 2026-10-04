"""Static browser wiring check for premium offer flow."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
page=(ROOT/"frontend/public/preparar-oferta.html").read_text(encoding="utf-8")
for target in ("/api/mi/private/offers/prefill", "/preview-pdf", "id=\"legal_name\"",
               "id=\"property_title\"", "id=\"generate-pdf\"", "tres días"):
    assert target in page, target
scripts=re.findall(r"<script(?:\\s[^>]*)?>(.*?)</script>", page, re.DOTALL)
assert len(scripts)==1
with tempfile.TemporaryDirectory() as temp:
    source=Path(temp)/"offer.js"
    source.write_text(scripts[0],encoding="utf-8")
    subprocess.run(["node","--check",str(source)],check=True)
print("Premium offer browser wiring and JavaScript syntax: OK")
