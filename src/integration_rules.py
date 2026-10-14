import pandas as pd

APPROVED_STATUS = "Approved in controlled fixture"


def classify_sales_movements(sales_movements, validation):
    """Determine which sales movements are eligible for reconciliation."""

    required_movements = {
        "movement_id",
        "reference_id",
        "product_id",
        "quantity_delta",
        "approval_status",
    }

    required_validation = {
        "sale_line_id",
        "processing_decision",
        "matched_product_id",
        "quantity_raw",
    }

    missing_movements = required_movements - set(sales_movements.columns)
    missing_validation = required_validation - set(validation.columns)

    if missing_movements:
        raise ValueError(
            f"Missing movement columns: {sorted(missing_movements)}"
        )

    if missing_validation:
        raise ValueError(
            f"Missing validation columns: {sorted(missing_validation)}"
        )

    if sales_movements["movement_id"].duplicated().any():
        raise ValueError("Duplicate movement IDs found.")

    if validation["sale_line_id"].duplicated().any():
        raise ValueError("Duplicate sale-line IDs found in validation.")

    linked = sales_movements.merge(
        validation[
            [
                "sale_line_id",
                "processing_decision",
                "matched_product_id",
                "quantity_raw",
            ]
        ],
        left_on="reference_id",
        right_on="sale_line_id",
        how="left",
        validate="many_to_one",
    )

    product_match = (
        linked["product_id"].notna()
        & linked["matched_product_id"].notna()
        & linked["product_id"].astype(str).str.strip().eq(
            linked["matched_product_id"].astype(str).str.strip()
        )
    )

    movement_quantity = pd.to_numeric(
        linked["quantity_delta"], errors="coerce"
    )
    sale_quantity = pd.to_numeric(
        linked["quantity_raw"], errors="coerce"
    )

    quantity_match = (
        movement_quantity.notna()
        & sale_quantity.notna()
        & movement_quantity.eq(-sale_quantity)
    )

    accepted = linked["processing_decision"].eq("ACCEPT")
    has_validation = linked["sale_line_id"].notna()
    approved = linked["approval_status"].eq(APPROVED_STATUS)

    linked["product_match"] = product_match
    linked["quantity_match"] = quantity_match
    linked["integration_decision"] = "REVIEW"
    linked["integration_reason"] = "SALE_NOT_ACCEPTED"

    linked.loc[~has_validation, "integration_reason"] = (
        "NO_VALIDATION_RECORD"
    )

    linked.loc[
        has_validation & accepted & ~product_match,
        "integration_reason",
    ] = "PRODUCT_MISMATCH"

    linked.loc[
        has_validation & accepted & product_match & ~quantity_match,
        "integration_reason",
    ] = "QUANTITY_MISMATCH"

    consistent_sale = (
        has_validation
        & accepted
        & product_match
        & quantity_match
    )

    linked.loc[
        consistent_sale & ~approved,
        "integration_reason",
    ] = "MOVEMENT_NOT_APPROVED"

    eligible = consistent_sale & approved

    linked.loc[eligible, "integration_decision"] = "ELIGIBLE"
    linked.loc[eligible, "integration_reason"] = (
        "ACCEPTED_SALE_AND_MOVEMENT_MATCH"
    )

    return linked