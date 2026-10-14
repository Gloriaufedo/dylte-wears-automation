
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
workbook_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)

aliases = pd.read_excel(workbook_path, sheet_name="Product_Aliases")
products = pd.read_excel(workbook_path, sheet_name="Product_Master")
sales = pd.read_excel(workbook_path, sheet_name="Sales_Raw")

# Inspect the exact sales descriptions we want to support.
examples = [
    "Alo Top Pink M",
    "Lace Trim Bra Blue 12",
    "Sports Bra White 12",
]

for description in examples:
    print(f"\n{'=' * 60}")
    print("SALE DESCRIPTION:", description)

    # Find catalogue products whose names occur in the description.
    normalized_description = description.casefold()

    candidates = products[
        products["product_name"].str.casefold().apply(
            lambda name: name in normalized_description
        )
    ]

    if candidates.empty:
        print("No product-name candidates found.")
    else:
        print(
            candidates[
                ["product_id", "sku", "product_name", "colour", "size"]
            ].to_string(index=False)
        )

    # Show matching source sales rows, if any.
    sales_matches = sales[
        sales["product_description_raw"].astype("string").str.casefold()
        == normalized_description
    ]

    print("Exact matching sales rows:", len(sales_matches))
