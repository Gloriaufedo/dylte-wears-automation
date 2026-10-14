    # Handle missing SKU
import pandas as pd


def match_by_sku(sku_value, sku_lookup):
    """
    Look up a sale's SKU in the product catalogue.
    This identifies a candidate only; it does not approve the sale.
    """

    if pd.isna(sku_value) or str(sku_value).strip() == "":
        return {
            "sku_match_status": "SKU_MISSING",
            "matched_product_id": None,
            "matched_sku": None,
        }

    sku = str(sku_value).strip().upper()

    if sku not in sku_lookup:
        return {
            "sku_match_status": "SKU_NOT_FOUND",
            "matched_product_id": None,
            "matched_sku": None,
        }

    return {
        "sku_match_status": "SKU_MATCHED",
        "matched_product_id": sku_lookup[sku]["product_id"],
        "matched_sku": sku,
    }
