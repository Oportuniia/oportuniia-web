"""Ensure distinct notarial escrow and independent reservation bank flows."""
from pathlib import Path

root=Path(__file__).resolve().parents[2]
page=(root/"frontend/public/como-funciona.html").read_text(encoding="utf-8")
architecture=(root/"docs/MASTER_B2B_ESCROW_API_PAYMENT_ARCHITECTURE_20261003.md").read_text(encoding="utf-8")

for required in (
    'id="pagos-protegidos"',
    "Firma ante notario",
    "infraestructura tipo escrow mediante API",
    "garantía de un coche de alquiler",
    "una retención en tarjeta, una fianza y un servicio escrow son mecanismos diferentes",
    "Las cantidades de reserva se tramitarán por un circuito independiente",
    "cuenta bancaria exclusiva para reservas",
    "todavía no contratados ni activados",
):
    assert required in page, required

for required in (
    "Pago B2B con Infraestructura Escrow (vía API)",
    "firma ante notario",
    "cuenta bancaria separada y exclusiva para reservas",
    "Cláusula matriz propuesta para contratos (sujeta a aprobación de LEGAL)",
    "Una cuenta exclusiva para reservas",
    "no equivale automáticamente a una cuenta escrow",
    "personas físicas o consumidores",
):
    assert required in architecture, required

assert "no a las reservas" in architecture
print("Separate notarial escrow and reservation-bank messaging: OK")
