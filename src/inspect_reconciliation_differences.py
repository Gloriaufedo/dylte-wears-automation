
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs"

comparison = pd.read_csv(
    OUTPUT_DIR / "inventory_reconciliation_comparison.csv"
)
audit = pd.read_csv(
    OUTPUT_DIR / "inventory_movement_audit.csv"
)

differences = comparison[
    (~comparison["closing_balance_matches"])
    | (~comparison["movement_count_matches"])
].copy()

columns = [
    "product_id",
    "sku",
    "opening_qty",
    "calculated_closing_qty",
    "expected_closing_qty",
    "applied_movement_count",
    "included_movement_count",
    "excluded_shortage_movement_count",
]

print(f"PRODUCTS WITH DIFFERENCES: {len(differences)}")
print("\nBALANCE AND MOVEMENT-COUNT DIFFERENCES")
print(differences[columns].to_string(index=False))

product_ids = differences["product_id"].tolist()
related = audit[audit["product_id"].isin(product_ids)].copy()

print("\nMOVEMENT HISTORY FOR THESE PRODUCTS")
print(
    related[
        [
            "movement_id",
            "movement_date_raw",
            "movement_date_parsed",
            "movement_type",
            "product_id",
            "quantity_delta",
            "unit_of_measure",
            "decision",
            "decision_reason",
            "balance_after_decision",
        ]
    ].to_string(index=False)
)

print("\nREVIEWED MOVEMENTS FOR THESE PRODUCTS")
reviewed = related[related["decision"] == "REVIEW"]
print(
    reviewed[
        [
            "movement_id",
            "movement_date_raw",
            "movement_type",
            "product_id",
            "quantity_delta",
            "decision_reason",
        ]
    ].to_string(index=False)
)
