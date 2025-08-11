from etl.normalize import to_sqm, FT2_TO_M2


def test_to_sqm_ft2():
    r = to_sqm(100, 'ft2')
    assert r is not None
    assert abs(r - 100 * FT2_TO_M2) < 1e-9


def test_to_sqm_m2():
    r = to_sqm(42, 'm2')
    assert r == 42
