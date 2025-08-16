from etl.dedupe import generate_listing_hash, dedupe_records, find_duplicates


def test_generate_listing_hash_stable():
    listing = {"url": "https://x/1", "title": "Nice", "price": 100}
    h1 = generate_listing_hash(listing)
    h2 = generate_listing_hash(listing.copy())
    assert h1 == h2 and len(h1) == 32


def test_dedupe_records_basic():
    listings = [
        {"url": "u1", "title": "A"},
        {"url": "u1", "title": "A"},  # dup
        {"url": "u2", "title": "B"},
    ]
    deduped = dedupe_records(listings)
    assert len(deduped) == 2


def test_find_duplicates_indexes():
    listings = [
        {"url": "u1", "title": "A"},
        {"url": "u1", "title": "A"},
        {"url": "u2", "title": "B"},
        {"url": "u2", "title": "B"},
    ]
    dup_map = find_duplicates(listings)
    # Two groups of duplicates
    assert len(dup_map) == 2
    assert all(len(ix) == 2 for ix in dup_map.values())
