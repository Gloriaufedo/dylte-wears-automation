
from pathlib import Path

import pandas as pd

from matching import match_by_sku
from validate_matches import validate_candidate
from candidate_matching import (
    find_description_candidates,
    filter_candidates_by_colour,
)


def validate_quantity(quantity):
    """Validate a recorded sale quantity."""
    if pd.isna(quantity):
        return "MISSING_QUANTITY"
    if quantity <= 0 or quantity % 1 != 0:
        return "INVALID_QUANTITY"
    return "VALID_QUANTITY"



def decide_sale(row):
    """Make a conservative decision after matching and validation."""

    if row["quantity_validation_status"] == "INVALID_QUANTITY":
        return "HOLD", "INVALID_QUANTITY"

    if row["quantity_validation_status"] == "MISSING_QUANTITY":
        return "REVIEW", "MISSING_QUANTITY"

    if row["colour_validation_status"] == "CONFLICT":
        return "HOLD", "COLOUR_CONFLICT"

    # A SKU that is present but not in the catalogue cannot be accepted.
    if row["sku_match_status"] == "SKU_NOT_FOUND":
        return "REVIEW", "SKU_NOT_FOUND"

    # Check whether the current pipeline has a resolved product.
    # The key check also supports older unit tests that omit this field.
    if "matched_product_id" in row and pd.isna(row["matched_product_id"]):
        return "REVIEW", row.get(
            "candidate_match_status",
            row["sku_match_status"],
        )

    if (
        row["sku_match_status"] == "SKU_MISSING"
        and "matched_product_id" not in row
    ):
        return "REVIEW", "SKU_MISSING"

    if row["size_validation_status"] == "UNVERIFIABLE_SIZE_FORMAT":
        return "REVIEW", "SIZE_FORMAT_UNVERIFIED"

    if row["colour_validation_status"] == "MISSING_RECORDED_COLOUR":
        return "REVIEW", "MISSING_RECORDED_COLOUR"

    if row["colour_validation_status"] != "MATCH":
        return "REVIEW", "UNRESOLVED_VALIDATION"

    if row.get("matched_by") == "DESCRIPTION_AND_COLOUR":
        return "ACCEPT", "VALIDATED_DESCRIPTION_COLOUR_AND_QUANTITY"

    if row["sku_match_status"] == "SKU_MATCHED":
        return "ACCEPT", "VALIDATED_SKU_COLOUR_AND_QUANTITY"

    return "REVIEW", "UNRESOLVED_VALIDATION"


def main():
    project_root = Path(__file__).resolve().parent.parent
    file_path = (
        project_root
        / "data"
        / "dylte_wears_synthetic_automation_dataset.xlsx"
    )

    sales = pd.read_excel(file_path, sheet_name="Sales_Raw")
    products = pd.read_excel(file_path, sheet_name="Product_Master")
    aliases = pd.read_excel(file_path, sheet_name="Product_Aliases")

    sku_lookup = (
        products.set_index("sku")[["product_id"]].to_dict("index")
    )
    product_lookup = (
        products.set_index("sku", drop=False).to_dict("index")
    )

    results = []

    for _, sale in sales.iterrows():
        match = match_by_sku(sale["sku_raw"], sku_lookup)
        quantity_status = validate_quantity(sale["quantity_raw"])

        row_result = {
            "sale_line_id": sale["sale_line_id"],
            "transaction_id_raw": sale["transaction_id_raw"],
            "product_description_raw": sale["product_description_raw"],
            "sku_raw": sale["sku_raw"],
            "colour_raw": sale["colour_raw"],
            "size_raw": sale["size_raw"],
            "quantity_raw": sale["quantity_raw"],
            "quantity_validation_status": quantity_status,
            "sku_match_status": match["sku_match_status"],
            "matched_product_id": None,
            "matched_sku": None,
            "matched_product_name": None,
            "catalogue_colour": None,
            "catalogue_size": None,
            "colour_validation_status": "NOT_CHECKED",
            "size_validation_status": "NOT_CHECKED",
            "validation_issues": "NOT_CHECKED",
            "candidate_match_status": "NOT_NEEDED",
            "candidate_count": 0,
            "matched_by": "NONE",
        }

        product = None

        # First choice: an exact catalogue SKU.
        if match["sku_match_status"] == "SKU_MATCHED":
            product = product_lookup[match["matched_sku"]]
            row_result["matched_by"] = "SKU"
            row_result["candidate_match_status"] = "SKU_MATCHED"

        # Second choice: exact alias phrase candidates, only when SKU is missing.
        elif match["sku_match_status"] == "SKU_MISSING":
            candidates = find_description_candidates(
                sale["product_description_raw"],
                aliases,
                products,
            )

            candidates = candidates.drop_duplicates(
                subset=["product_id"]
            )

            candidates_after_colour = filter_candidates_by_colour(
                candidates,
                sale["colour_raw"],
            )

            row_result["candidate_count"] = len(candidates_after_colour)

            if candidates.empty:
                row_result["candidate_match_status"] = "NO_CANDIDATES"

            elif candidates_after_colour.empty:
                row_result["candidate_match_status"] = "COLOUR_CONFLICT"
                row_result["colour_validation_status"] = "CONFLICT"

            elif len(candidates_after_colour) > 1:
                row_result["candidate_match_status"] = (
                    "AMBIGUOUS_CANDIDATES"
                )

            else:
                candidate = candidates_after_colour.iloc[0]
                product = candidate.to_dict()
                row_result["matched_by"] = "DESCRIPTION_AND_COLOUR"
                row_result["candidate_match_status"] = "UNIQUE_CANDIDATE"

        else:
            row_result["candidate_match_status"] = "SKU_NOT_FOUND"

        if product is not None:
            row_result["matched_product_id"] = product["product_id"]
            row_result["matched_sku"] = product["sku"]
            row_result["matched_product_name"] = product["product_name"]
            row_result["catalogue_colour"] = product["colour"]
            row_result["catalogue_size"] = product["size"]

            validation = validate_candidate(sale, product)
            row_result.update(validation)

        results.append(row_result)

    results_df = pd.DataFrame(results)

    decisions = results_df.apply(decide_sale, axis=1)
    results_df["processing_decision"] = decisions.apply(
        lambda result: result[0]
    )
    results_df["decision_reason"] = decisions.apply(
        lambda result: result[1]
    )

    # Basic integrity checks.
    assert len(results_df) == len(sales)
    assert results_df["sale_line_id"].is_unique
    assert results_df["processing_decision"].notna().all()

    accepted_sales = results_df[
        results_df["processing_decision"] == "ACCEPT"
    ].copy()

    review_queue = results_df[
        results_df["processing_decision"] == "REVIEW"
    ].copy()

    hold_queue = results_df[
        results_df["processing_decision"] == "HOLD"
    ].copy()

    assert (
        len(accepted_sales) + len(review_queue) + len(hold_queue)
        == len(results_df)
    )

    output_dir = project_root / "outputs"
    output_dir.mkdir(exist_ok=True)

    results_df.to_csv(output_dir / "validation_results.csv", index=False)
    accepted_sales.to_csv(output_dir / "accepted_sales.csv", index=False)
    review_queue.to_csv(output_dir / "review_queue.csv", index=False)
    hold_queue.to_csv(output_dir / "hold_queue.csv", index=False)

    print("\nPROCESSING DECISION SUMMARY")
    print(results_df["processing_decision"].value_counts())

    print("\nDECISION REASONS")
    print(results_df["decision_reason"].value_counts())

    print("\nCANDIDATE MATCH SUMMARY")
    print(results_df["candidate_match_status"].value_counts())

    print("\nMATCHED BY")
    print(results_df["matched_by"].value_counts())

    print("\nFINAL QUEUE SUMMARY")
    print("Total sales lines:", len(results_df))
    print("Accepted:", len(accepted_sales))
    print("Requires review:", len(review_queue))
    print("On hold:", len(hold_queue))

    print("\nOUTPUT FILES SAVED")
    print("Full results:", output_dir / "validation_results.csv")
    print("Accepted sales:", output_dir / "accepted_sales.csv")
    print("Review queue:", output_dir / "review_queue.csv")
    print("Hold queue:", output_dir / "hold_queue.csv")


if __name__ == "__main__":
    main()
