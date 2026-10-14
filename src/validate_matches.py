
import pandas as pd


def validate_candidate(sale, product):
    """
    Validate a sale against a candidate catalogue product.

    A known SKU may establish the exact variant when size is missing.
    An unverified size format or conflicting colour requires review.
    This function does not approve stock movements.
    """
    issues = []

    sale_colour = sale.get("colour_raw")
    product_colour = product.get("colour")

    if pd.isna(sale_colour) or str(sale_colour).strip() == "":
        colour_status = "MISSING_RECORDED_COLOUR"
    elif pd.isna(product_colour) or str(product_colour).strip() == "":
        colour_status = "MISSING_CATALOGUE_COLOUR"
    elif str(sale_colour).strip().casefold() == str(product_colour).strip().casefold():
        colour_status = "MATCH"
    else:
        colour_status = "CONFLICT"
        issues.append("COLOUR_CONFLICT")

    sale_size = sale.get("size_raw")

    if pd.isna(sale_size):
        size_status = "MISSING_SIZE_SKU_CAN_IDENTIFY_VARIANT"
    else:
        size_status = "UNVERIFIABLE_SIZE_FORMAT"
        issues.append("SIZE_FORMAT_UNVERIFIED")

    return {
        "colour_validation_status": colour_status,
        "size_validation_status": size_status,
        "validation_issues": "|".join(issues) if issues else "NONE",
    }
