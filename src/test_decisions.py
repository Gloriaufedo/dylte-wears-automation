from run_validation import decide_sale

def test_unresolved_product_is_not_accepted():
    row = {
        "quantity_validation_status": "VALID_QUANTITY",
        "colour_validation_status": "NOT_CHECKED",
        "sku_match_status": "SKU_NOT_FOUND",
        "size_validation_status": "NOT_CHECKED",
    }

    decision, reason = decide_sale(row)

    assert decision != "ACCEPT"


def test_missing_quantity_is_not_accepted():
    row = {
        "quantity_validation_status": "MISSING_QUANTITY",
        "colour_validation_status": "MATCH",
        "sku_match_status": "SKU_MATCHED",
        "size_validation_status": "MISSING_SIZE_SKU_CAN_IDENTIFY_VARIANT",
    }

    decision, reason = decide_sale(row)

    assert decision != "ACCEPT"


def test_invalid_quantity_is_held():
    row = {
        "quantity_validation_status": "INVALID_QUANTITY",
        "colour_validation_status": "MATCH",
        "sku_match_status": "SKU_MATCHED",
        "size_validation_status": "MISSING_SIZE_SKU_CAN_IDENTIFY_VARIANT",
    }
    decision, reason = decide_sale(row)
    assert decision == "HOLD"
    assert reason == "INVALID_QUANTITY"


def test_colour_conflict_is_held():
    row = {
        "quantity_validation_status": "VALID_QUANTITY",
        "colour_validation_status": "CONFLICT",
        "sku_match_status": "SKU_MATCHED",
        "size_validation_status": "MISSING_SIZE_SKU_CAN_IDENTIFY_VARIANT",
    }
    decision, reason = decide_sale(row)
    assert decision == "HOLD"
    assert reason == "COLOUR_CONFLICT"


def test_missing_colour_requires_review():
    row = {
        "quantity_validation_status": "VALID_QUANTITY",
        "colour_validation_status": "MISSING_RECORDED_COLOUR",
        "sku_match_status": "SKU_MATCHED",
        "size_validation_status": "MISSING_SIZE_SKU_CAN_IDENTIFY_VARIANT",
    }
    decision, reason = decide_sale(row)
    assert decision == "REVIEW"
    assert reason == "MISSING_RECORDED_COLOUR"


def test_valid_sale_can_be_accepted():
    row = {
        "quantity_validation_status": "VALID_QUANTITY",
        "colour_validation_status": "MATCH",
        "sku_match_status": "SKU_MATCHED",
        "size_validation_status": "MISSING_SIZE_SKU_CAN_IDENTIFY_VARIANT",
    }
    decision, reason = decide_sale(row)
    assert decision == "ACCEPT"
