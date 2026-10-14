
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
file_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)

sales = pd.read_excel(file_path, sheet_name="Sales_Raw")
products = pd.read_excel(file_path, sheet_name="Product_Master")

# Keep only sales lines where a SKU exists in the catalogue.
matched = sales.merge(
    products[["sku", "product_name", "size", "colour"]],
    left_on="sku_raw",
    right_on="sku",
    how="inner",
)

# Focus on rows with a recorded numeric size.
sized = matched.loc[matched["size_raw"].notna()].copy()

print("\nRECORDED SIZE 12 — MATCHED SKU DETAILS")
print(
    sized[
        [
            "sale_line_id",
            "product_description_raw",
            "sku_raw",
            "product_name",
            "size_raw",
            "size",
            "colour_raw",
            "colour",
        ]
    ].head(25).to_string(index=False)
)

print("\nRECORDED SIZE VS CATALOGUE SIZE")
print(
    sized.groupby(["size_raw", "size"], dropna=False)
    .size()
    .rename("line_count")
    .reset_index()
    .to_string(index=False)
)

print("\nDESCRIPTION CONTAINS SIZE 12")
description_has_12 = sales["product_description_raw"].astype("string").str.contains(
    r"\b12\b", regex=True, na=False
)
print("All sales with size recorded:", int(sales["size_raw"].notna().sum()))
print(
    "Descriptions containing the standalone number 12:",
    int((sales["size_raw"].notna() & description_has_12).sum()),
)
