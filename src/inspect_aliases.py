
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

# Normalize alias text for comparison.
aliases["alias_text_clean"] = (
    aliases["alias_text"]
    .astype("string")
    .str.strip()
    .str.lower()
)

# Count how many distinct products each alias can refer to.
alias_summary = (
    aliases.groupby("alias_text_clean")
    .agg(
        product_count=("product_id", "nunique"),
        alias_rows=("alias_id", "count"),
    )
    .reset_index()
    .sort_values("product_count", ascending=False)
)

print("\nMOST AMBIGUOUS ALIASES")
print(alias_summary.head(15).to_string(index=False))

print("\nALIAS SUMMARY")
print("Total alias rows:", len(aliases))
print("Distinct normalized aliases:", aliases["alias_text_clean"].nunique())
print(
    "Aliases mapping to multiple products:",
    (alias_summary["product_count"] > 1).sum(),
)

# Show catalogue details for the most ambiguous alias.
if not alias_summary.empty:
    example_alias = alias_summary.iloc[0]["alias_text_clean"]
    print(f"\nPRODUCTS LINKED TO '{example_alias}'")

    matching_aliases = aliases[
        aliases["alias_text_clean"] == example_alias
    ]

    details = matching_aliases.merge(
        products[
            [
                "product_id",
                "sku",
                "product_name",
                "colour",
                "size",
                "unit_of_measure",
            ]
        ],
        on="product_id",
        how="left",
        validate="many_to_one",
    )


    print(
        details[
            [
                "product_id",
                "sku",
                "product_name",
                "colour",
                "size",
                "unit_of_measure",
            ]
        ].to_string(index=False)
    )

print("\nALIAS TYPES FOR THIS PHRASE")
print(
    matching_aliases[
        ["product_id", "alias_text", "alias_type"]
    ].to_string(index=False)
)

print("\nDUPLICATE COUNTS")
print(
    "Exact duplicate rows:",
    aliases.duplicated().sum()
)

print(
    "Repeated product + normalized alias pairs:",
    aliases.duplicated(
        subset=["product_id", "alias_text_clean"]
    ).sum()
)


print("\nCANDIDATE COUNTS AFTER VARIANT DETAILS")

# First, remove repeated alias records for the same product.
unique_candidates = details.drop_duplicates(
    subset=["product_id"]
)

print("Unique products for alias:", len(unique_candidates))

# How many unique products remain for each
# product-name + colour + size combination?
variant_summary = (
    products.groupby(
        ["product_name", "colour", "size"],
        dropna=False
    )
    .agg(unique_skus=("sku", "nunique"))
    .reset_index()
)

print(
    "Catalogue name-colour-size combinations:",
    len(variant_summary)
)

print(
    "Combinations linked to multiple SKUs:",
    (variant_summary["unique_skus"] > 1).sum()
)

print("\nEXAMPLES OF AMBIGUOUS VARIANTS")
print(
    variant_summary.loc[
        variant_summary["unique_skus"] > 1
    ].head(10).to_string(index=False)
)
