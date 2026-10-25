"""Fixed public registration texts; no retrospective acceptance fabrication."""
import json
from pathlib import Path

def bundle():
    return json.loads((Path(__file__).parent / "legal/alta-20261025-2.json").read_text(encoding="utf-8"))

def receipt_text(acceptance):
    snapshot = acceptance.get("snapshot")
    if not snapshot:
        return "No hay una copia histórica del texto disponible para esta alta. No se ha reconstruido una aceptación."
    return "COPIA DE TU ALTA GRATUITA · OPORTUNIIA\nVersión: " + snapshot["version"] + "\nFecha: " + str(acceptance["accepted_at"]) + "\n\n" + "\n\n".join(d["title"] + "\n" + d["text"] for d in snapshot["documents"])
