"""Public catalogue must never serialize PRESENTACIÓN's private storage data."""
import catalog_data as cat

def test_published_catalogue_sanitizes_document_metadata():
    item = dict(cat.OPPORTUNITIES[0])
    item.update({
        "slug": "synthetic-publication",
        "internal_id": "OP-PRIVATE",
        "source_output_id": "m2m-private-id",
        "source_output_hash": "hash-private",
        "source_output_version": "revision-private",
        "documents": {"PC": {"status": "READY", "artifact_key": "r2/private.pdf",
                             "content_hash": "document-private-hash"}},
    })
    public = cat.enrich(item)
    for field in ("internal_id", "source_output_id", "source_output_hash",
                  "source_output_version", "documents"):
        assert field not in public
    public_items = cat.filter_opportunities(cat.normalize_filters(
        universe=item["universe"]), extra=[item])
    synthetic = next(i for i in public_items if i["slug"] == item["slug"])
    assert "r2/private" not in repr(synthetic)
    assert "documents" not in synthetic
