
from pathlib import Path

import pandas as pd

from matching import match_by_sku


# Locate the project workbook
project_root = Path(__file__).resolve().parent.parent
file_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)

# Load sales and product catalogue
sales = pd.read_excel(file_path, sheet_name="Sales_Raw")
products = pd.read_excel(file_path, sheet_name="Product_Master")

# Build a dictionary for quick SKU lookups
sku_lookup = (
    products.set_index("sku")[["product_id"]]
    .to_dict(orient="index")
)

# Match each sales line using its raw SKU
results = sales["sku_raw"].apply(
    lambda sku: match_by_sku(sku, sku_lookup)
)

# Convert the matching results into columns
results_df = pd.DataFrame(results.tolist())

# Combine original sales data with the matching results
sales_results = pd.concat(
    [sales.reset_index(drop=True), results_df],
    axis=1,
)

print("\nSKU MATCHING SUMMARY")
print(sales_results["sku_match_status"].value_counts(dropna=False))

print("\nMATCHING RESULT SAMPLE")
print(
    sales_results[
        [
            "sale_line_id",
            "sku_raw",
            "sku_match_status",
            "matched_product_id",
            "matched_sku",
        ]
    ].head(15).to_string(index=False)
)

# Save results to a separate output file
output_dir = project_root / "outputs"
output_dir.mkdir(exist_ok=True)

output_file = output_dir / "sku_matching_results.csv"
sales_results.to_csv(output_file, index=False)

print(f"\nResults saved to: {output_file}")


print("\nRAW SIZE VALUES")
print(sales["size_raw"].value_counts(dropna=False).head(10))

print("\nCATALOGUE SIZE VALUES")
print(products["size"].value_counts(dropna=False))

print("\nSALE COLUMNS AVAILABLE")
print(sales.columns.tolist())