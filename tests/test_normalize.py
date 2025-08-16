from etl.normalize import to_sqm

# Constants for conversion testing - matching the implementation
FT2_TO_M2 = 0.092903

def test_to_sqm_ft2():
    r = to_sqm(100, 'ft2')
    assert r is not None
    assert abs(r - 9.29) < 0.01  # 100 sq ft should be approximately 9.29 sq m


def test_to_sqm_m2():
    r = to_sqm(42, 'm2')
    assert r == 42
