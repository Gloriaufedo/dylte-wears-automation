from validate_matches import validate_candidate


def test_unverified_numeric_size_is_flagged():
    product = {
        "colour": "Black",
        "size": "M",
    }

    sale_with_size = {
        "colour_raw": "Black",
        "size_raw": 12.0,
    }

    result = validate_candidate(sale_with_size, product)

    assert result["colour_validation_status"] == "MATCH"
    assert result["size_validation_status"] == "UNVERIFIABLE_SIZE_FORMAT"
    assert result["validation_issues"] == "SIZE_FORMAT_UNVERIFIED"


def test_missing_size_does_not_create_validation_issue():
    product = {
        "colour": "Black",
        "size": "M",
    }

    sale_without_size = {
        "colour_raw": "Black",
        "size_raw": None,
    }

    result = validate_candidate(sale_without_size, product)

    assert result["colour_validation_status"] == "MATCH"
    assert (
        result["size_validation_status"]
        == "MISSING_SIZE_SKU_CAN_IDENTIFY_VARIANT"
    )
    assert result["validation_issues"] == "NONE"