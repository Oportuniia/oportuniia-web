from presentation_document_authz import VerifiedDocumentPrincipal, can_read_presentation_pdf

ITEM = {
    "internal_id": "OP-TEST-001",
    "source_output_id": "output-private",
    "documents": {"PC": {"status": "READY"}, "RE": {"status": "READY"},
                  "IC": {"status": "FAILED"}, "RF": {"status": "READY"}},
}

def test_anonymous_inactive_and_unverified_fail_closed():
    assert not can_read_presentation_pdf(None, ITEM, "PC")
    assert not can_read_presentation_pdf(VerifiedDocumentPrincipal("", True), ITEM, "PC")
    assert not can_read_presentation_pdf(VerifiedDocumentPrincipal(
        "actor1", False, {"OP-TEST-001": frozenset({"PC"})}), ITEM, "PC")

def test_exact_operation_and_document_grant_required():
    p = VerifiedDocumentPrincipal("actor1", True, {"OP-TEST-001": frozenset({"PC"})})
    assert can_read_presentation_pdf(p, ITEM, "PC")
    assert not can_read_presentation_pdf(p, ITEM, "RE")
    assert not can_read_presentation_pdf(p, ITEM, "IC")
    assert not can_read_presentation_pdf(p, ITEM, "RF")
    assert not can_read_presentation_pdf(p, {**ITEM, "internal_id": "OP-TEST-002"}, "PC")
    assert not can_read_presentation_pdf(p, {**ITEM, "source_output_id": ""}, "PC")
    assert not can_read_presentation_pdf(p, {**ITEM, "documents": {"PC": {"status": "PENDING"}}}, "PC")
    assert not can_read_presentation_pdf(p, ITEM, "../PC")
    assert not can_read_presentation_pdf(p, ITEM, "pc")
