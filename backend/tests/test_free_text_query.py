import catalog_data as cat


def test_query_combines_with_product_and_preserves_facets():
    filters = cat.normalize_filters(products=['NPL'], q='Sevilla')
    results = cat.filter_opportunities(filters)
    assert results and all(o['product'] == 'NPL' and o['municipio'] == 'sevilla' for o in results)
    assert cat.facet_counts(filters)['product']['NPL'] == len(results)


def test_query_ignores_case_and_accents_and_requires_all_words():
    results = cat.filter_opportunities(cat.normalize_filters(q='APÁRTAMENTOS turisticos'))
    assert len(results) == 1
    assert results[0]['slug'] == 'alicante-cdr-apartamentos-turisticos'
    assert cat.filter_opportunities(cat.normalize_filters(q='apartamentos sevilla')) == []


def test_unknown_query_returns_empty_results_and_facets():
    filters = cat.normalize_filters(q='noexistentedemo123')
    assert cat.filter_opportunities(filters) == []
    assert all(n == 0 for n in cat.facet_counts(filters)['product'].values())


def test_empty_query_keeps_existing_catalogue():
    assert cat.filter_opportunities(cat.normalize_filters(q='  ')) == cat.filter_opportunities(cat.normalize_filters())
