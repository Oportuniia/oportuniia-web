"""No R2 secrets or protected PDF identifiers may leak into public document view."""
from presentation_document_view import public_document_status

def test_demo_fixture_has_no_sovereign_document_status():
    assert public_document_status({"slug": "demo", "documents": {"PC": {"status": "READY"}}}) is None

def test_published_document_status_is_sanitized():
    rows = public_document_status({
        "source_output_id": "private-output-id",
        "documents": {
            "PC": {"status": "READY", "artifact_key": "secret/r2/key.pdf", "content_hash": "secret-hash"},
            "RE": {"status": "FAILED"},
            "IC": {"status": "READY"},
        },
    })
    assert [row["code"] for row in rows] == ["PC", "RE", "IC", "RF"]
    assert [row["ready"] for row in rows] == [True, False, True, False]
    assert all(row["access"] == "protected" for row in rows)
    assert "secret" not in repr(rows)
    assert "private-output-id" not in repr(rows)

def test_missing_metadata_fails_closed():
    rows = public_document_status({"source_output_id": "id"})
    assert rows is not None
    assert all(not row["ready"] for row in rows)
