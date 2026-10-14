import pandas as pd
import pytest

from integration_rules import (
    APPROVED_STATUS,
    classify_sales_movements,
)


def make_movement(
    product_id="P1",
    quantity_delta=-2,
    approval_status=APPROVED_STATUS,
    reference_id="SALE-1",
):
    return pd.DataFrame([{
        "movement_id": "M1",
        "reference_id": reference_id,
        "product_id": product_id,
        "quantity_delta": quantity_delta,
        "approval_status": approval_status,
    }])


def make_validation(
    decision="ACCEPT",
    matched_product_id="P1",
    quantity_raw=2,
    sale_line_id="SALE-1",
):
    return pd.DataFrame([{
        "sale_line_id": sale_line_id,
        "processing_decision": decision,
        "matched_product_id": matched_product_id,
        "quantity_raw": quantity_raw,
    }])


def test_consistent_approved_sale_is_eligible():
    result = classify_sales_movements(
        make_movement(),
        make_validation(),
    )

    assert result.loc[0, "integration_decision"] == "ELIGIBLE"
    assert (
        result.loc[0, "integration_reason"]
        == "ACCEPTED_SALE_AND_MOVEMENT_MATCH"
    )


def test_review_sale_is_not_eligible():
    result = classify_sales_movements(
        make_movement(),
        make_validation(decision="REVIEW"),
    )

    assert result.loc[0, "integration_decision"] == "REVIEW"
    assert result.loc[0, "integration_reason"] == "SALE_NOT_ACCEPTED"


def test_product_mismatch_is_not_eligible():
    result = classify_sales_movements(
        make_movement(product_id="P2"),
        make_validation(matched_product_id="P1"),
    )

    assert result.loc[0, "integration_decision"] == "REVIEW"
    assert result.loc[0, "integration_reason"] == "PRODUCT_MISMATCH"


def test_quantity_mismatch_is_not_eligible():
    result = classify_sales_movements(
        make_movement(quantity_delta=-3),
        make_validation(quantity_raw=2),
    )

    assert result.loc[0, "integration_decision"] == "REVIEW"
    assert result.loc[0, "integration_reason"] == "QUANTITY_MISMATCH"


def test_unapproved_movement_is_not_eligible():
    result = classify_sales_movements(
        make_movement(approval_status="Pending"),
        make_validation(),
    )

    assert result.loc[0, "integration_decision"] == "REVIEW"
    assert result.loc[0, "integration_reason"] == "MOVEMENT_NOT_APPROVED"


def test_missing_validation_record_requires_review():
    result = classify_sales_movements(
        make_movement(reference_id="UNKNOWN-SALE"),
        make_validation(),
    )

    assert result.loc[0, "integration_decision"] == "REVIEW"
    assert result.loc[0, "integration_reason"] == "NO_VALIDATION_RECORD"


def test_duplicate_validation_sale_ids_raise_error():
    validation = pd.concat(
        [
            make_validation(),
            make_validation(),
        ],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate sale-line IDs"):
        classify_sales_movements(make_movement(), validation)