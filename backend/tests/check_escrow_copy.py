"""Static validation that escrow copy is conditional, not a live-payment claim."""
from pathlib import Path

root=Path(__file__).resolve().parents[2]
page=(root/"frontend/public/como-funciona.html").read_text(encoding="utf-8")
architecture=(root/"docs/MASTER_B2B_ESCROW_API_PAYMENT_ARCHITECTURE_20261003.md").read_text(encoding="utf-8")
for value in (
    'id="pagos-protegidos"', "fianza de un coche de alquiler",
    "tipo escrow", "mediante API", "todavía no está contratado ni activado",
    "OPORTUNIIA no se presenta como depositaria",
    "Una retención en tarjeta, un depósito y una cuenta escrow son mecanismos diferentes",
):
    assert value in page, value
for value in (
    "Pago B2B con Infraestructura Escrow (vía API)",
    "Cláusula matriz propuesta para contratos",
    "sujeta a aprobación de LEGAL",
    "personas físicas no son necesariamente empresas",
    "no inferir que cualquier pasarela API equivale a escrow regulado",
):
    assert value in architecture, value
assert "proveedor tercero debidamente habilitado" in architecture
print("WEB escrow explanation and MASTER contract draft constraints: OK")
