
from pathlib import Path
import pandas as pd

from candidate_matching import (
    find_description_candidates,
    filter_candidates_by_colour,
)

project_root = Path(__file__).resolve().parent.parent
workbook_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)

sales = pd.read_excel(workbook_path, sheet_name="Sales_Raw")
products = pd.read_excel(workbook_path, sheet_name="Product_Master")
aliases = pd.read_excel(workbook_path, sheet_name="Product_Aliases")

# Inspect only sales without a recorded SKU.
sales_without_sku = sales[
    sales["sku_raw"].isna()
    | sales["sku_raw"].astype("string").str.strip().eq("")
].copy()

results = []

for _, sale in sales_without_sku.iterrows():
    candidates = find_description_candidates(
        sale["product_description_raw"],
        aliases,
        products,
    )

    initial_count = candidates["product_id"].nunique()

    if pd.notna(sale["colour_raw"]) and str(sale["colour_raw"]).strip():
        filtered = filter_candidates_by_colour(
            candidates,
            sale["colour_raw"],
        )
    else:
        filtered = candidates

    candidate_count = filtered["product_id"].nunique()

    results.append({
        "sale_line_id": sale["sale_line_id"],
        "description": sale["product_description_raw"],
        "recorded_colour": sale["colour_raw"],
        "initial_candidate_count": initial_count,
        "candidate_count_after_colour": candidate_count,
        "candidate_product_ids": "|".join(
    sorted(filtered["product_id"].astype(str).unique())
),
        "candidate_status": (
            "NO_CANDIDATES" if candidate_count == 0
            else "UNIQUE_CANDIDATE" if candidate_count == 1
            else "AMBIGUOUS_CANDIDATES"
        ),
    })

results_df = pd.DataFrame(results)

print("\nCANDIDATE-GENERATION SUMMARY")
print("Sales without SKU:", len(results_df))
print("\nCandidates after color filtering:")
print(results_df["candidate_status"].value_counts(dropna=False))

print("\nCandidate count distribution:")
print(
    results_df["candidate_count_after_colour"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nEXAMPLES WITH ONE CANDIDATE")
print(
    results_df.loc[
        results_df["candidate_status"] == "UNIQUE_CANDIDATE"
    ].head(10).to_string(index=False)
)

output_dir = project_root / "outputs"
output_dir.mkdir(exist_ok=True)

output_path = output_dir / "candidate_evaluation.csv"
results_df.to_csv(output_path, index=False)

print("\nDetailed results saved to:", output_path)
