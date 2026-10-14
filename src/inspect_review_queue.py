
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
review_path = project_root / "outputs" / "review_queue.csv"

review = pd.read_csv(review_path)

columns_to_inspect = [
    "sale_line_id",
    "product_description_raw",
    "sku_raw",
    "matched_sku",
    "matched_product_name",
    "colour_raw",
    "catalogue_colour",
    "size_raw",
    "catalogue_size",
    "quantity_raw",
    "validation_issues",
]

print("\nREVIEW QUEUE SAMPLE — RAW SALE VS CANDIDATE")
print(review[columns_to_inspect].head(20).to_string(index=False))

print("\nREVIEW QUEUE SIZE")
print(f"Rows: {len(review)}")
print(f"Columns: {len(review.columns)}")


print("\nRAW SIZE VALUE INSPECTION")

sales_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)

raw_sales = pd.read_excel(sales_path, sheet_name="Sales_Raw")

print("Column data type:", raw_sales["size_raw"].dtype)
print("\nMost common original size values:")
print(raw_sales["size_raw"].value_counts(dropna=False).head(15))

print("\nSample rows with recorded sizes:")
print(
    raw_sales.loc[
        raw_sales["size_raw"].notna(),
        ["sale_line_id", "product_description_raw", "size_raw"]
    ].head(15).to_string(index=False)
)
