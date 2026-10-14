
from matching import match_by_sku


sku_lookup = {
    "DW-CAS-0010": {
        "product_id": "PRD-0010",
    },
    "DW-LIN-0004": {
        "product_id": "PRD-0004",
    },
}


def test_known_sku():
    result = match_by_sku("DW-CAS-0010", sku_lookup)
    assert result["sku_match_status"] == "SKU_MATCHED"
    assert result["matched_product_id"] == "PRD-0010"


def test_sku_with_extra_spaces_and_lowercase():
    result = match_by_sku(" dw-cas-0010 ", sku_lookup)
    assert result["sku_match_status"] == "SKU_MATCHED"
    assert result["matched_sku"] == "DW-CAS-0010"


def test_missing_sku():
    result = match_by_sku(None, sku_lookup)
    assert result["sku_match_status"] == "SKU_MISSING"


def test_nan_sku():
    result = match_by_sku(float("nan"), sku_lookup)
    assert result["sku_match_status"] == "SKU_MISSING"


def test_unknown_sku():
    result = match_by_sku("DW-UNKNOWN-9999", sku_lookup)
    assert result["sku_match_status"] == "SKU_NOT_FOUND"


if __name__ == "__main__":
    test_known_sku()
    test_sku_with_extra_spaces_and_lowercase()
    test_missing_sku()
    test_nan_sku()
    test_unknown_sku()
    print("All five SKU matching tests passed.")
