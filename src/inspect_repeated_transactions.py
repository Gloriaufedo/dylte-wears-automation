
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
workbook_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)
candidate_path = (
    project_root
    / "outputs"
    / "candidate_evaluation.csv"
)

candidates = pd.read_csv(candidate_path)

unique = candidates[
    candidates["candidate_status"] == "UNIQUE_CANDIDATE"
].copy()

sales = pd.read_excel(workbook_path, sheet_name="Sales_Raw")

# Attach the original transaction ID and quantity to each candidate.
check = unique[["sale_line_id"]].merge(
    sales[
        [
            "sale_line_id",
            "transaction_id_raw",
            "product_description_raw",
            "quantity_raw",
        ]
    ],
    on="sale_line_id",
    how="left",
    validate="one_to_one",
)

transaction_ids = (
    check["transaction_id_raw"]
    .astype("string")
    .str.strip()
)

has_id = transaction_ids.notna() & transaction_ids.ne("")

repeated = check[
    has_id
    & transaction_ids.duplicated(keep=False)
].copy()

print("\nREPEATED TRANSACTION RECORDS")
print("Rows involved:", len(repeated))

print(
    repeated[
        [
            "sale_line_id",
            "transaction_id_raw",
            "product_description_raw",
            "quantity_raw",
        ]
    ]
    .sort_values(["transaction_id_raw", "sale_line_id"])
    .to_string(index=False)
)

print("\nTRANSACTION GROUP SIZES")
print(
    repeated.groupby("transaction_id_raw")
    .size()
    .sort_values(ascending=False)
    .to_string()
)
