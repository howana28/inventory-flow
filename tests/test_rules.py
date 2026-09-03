from app.services.rules import calculate_difference, classify_difference, zone_from_location

def test_reconciliation_formula():
    assert calculate_difference(12, 15) == -3
    assert calculate_difference(18, 15) == 3
    assert calculate_difference(10, -4) == 10

def test_difference_labels():
    assert classify_difference(0) == 'OK'
    assert classify_difference(-1) == 'FALTA'
    assert classify_difference(2) == 'SOBRA'

def test_zone_extraction():
    assert zone_from_location('07.04.02') == '07'
