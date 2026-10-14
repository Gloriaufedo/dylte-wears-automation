
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
workbook_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)
evaluation_path = (
    project_root
    / "outputs"
    / "candidate_accuracy_evaluation.csv"
)

sales = pd.read_excel(workbook_path, sheet_name="Sales_Raw")
products = pd.read_excel(workbook_path, sheet_name="Product_Master")
evaluation = pd.read_csv(evaluation_path)

# Keep only cases where exactly one candidate was generated.
unique = evaluation[
    evaluation["candidate_status"] == "UNIQUE_CANDIDATE"
].copy()

unique["candidate_product_id"] = (
    unique["candidate_product_ids"].fillna("").astype(str)
)

unique = unique.merge(
    sales[
        [
            "sale_line_id",
            "sku_raw",
            "size_raw",
            "colour_raw",
            "product_description_raw",
            "quantity_raw",
        ]
    ],
    on="sale_line_id",
    how="left",
    validate="one_to_one",
)

unique = unique.merge(
    products[
        ["product_id", "sku", "product_name", "colour", "size"]
    ].rename(
        columns={
            "product_id": "candidate_product_id",
            "sku": "candidate_sku",
            "product_name": "candidate_product_name",
            "colour": "candidate_colour",
            "size": "candidate_size",
        }
    ),
    on="candidate_product_id",
    how="left",
    validate="many_to_one",
)


# Check whether candidate rows have usable quantities.
unique["quantity_check"] = "VALID_QUANTITY"

unique.loc[
    unique["quantity_raw"].isna(),
    "quantity_check",
] = "MISSING_QUANTITY"

unique.loc[
    unique["quantity_raw"].notna()
    & (
        (unique["quantity_raw"] <= 0)
        | (unique["quantity_raw"] % 1 != 0)
    ),
    "quantity_check",
] = "INVALID_QUANTITY"

print("\nQUANTITY CHECK")
print(unique["quantity_check"].value_counts().to_string())

# Inspect repeated recorded transaction IDs.

# Load transaction IDs directly from the original sales sheet.
sales_for_transactions = pd.read_excel(
    workbook_path,
    sheet_name="Sales_Raw",
)

transaction_check = unique[["sale_line_id"]].merge(
    sales_for_transactions[["sale_line_id", "transaction_id_raw"]],
    on="sale_line_id",
    how="left",
    validate="one_to_one",
)

transaction_ids = (
    transaction_check["transaction_id_raw"]
    .astype("string")
    .str.strip()
)

has_transaction_id = transaction_ids.notna() & transaction_ids.ne("")

repeated_transaction_id = (
    has_transaction_id
    & transaction_ids.duplicated(keep=False)
)

print("\nTRANSACTION ID CHECK")
print("Rows with a transaction ID:", int(has_transaction_id.sum()))
print(
    "Rows with repeated transaction IDs:",
    int(repeated_transaction_id.sum()),
)


# Compare the recorded colour with the candidate's catalogue colour.
unique["colour_check"] = (
    unique["colour_raw"].astype("string").str.strip().str.casefold()
    == unique["candidate_colour"].astype("string").str.strip().str.casefold()
)

# Flag records where a recorded colour disagrees with the candidate.
unique["colour_check"] = unique["colour_check"].map(
    {True: "COLOUR_AGREES", False: "COLOUR_CONFLICT_OR_MISSING"}
)

print("\nCOLOUR CHECK")
print(unique["colour_check"].value_counts(dropna=False).to_string())

print("\nDESCRIPTION AND CANDIDATE REVIEW")
print(
    unique[
        [
            "sale_line_id",
            "product_description_raw",
            "candidate_product_name",
            "colour_raw",
            "candidate_colour",
            "size_raw",
            "candidate_size",
            "colour_check",
        ]
    ].head(25).to_string(index=False)
)


# Check recorded SKU independently from the candidate-generation result.
unique["recorded_sku_status"] = "SKU_MISSING"

has_sku = (
    unique["sku_raw"].notna()
    & unique["sku_raw"].astype("string").str.strip().ne("")
)

unique.loc[has_sku, "recorded_sku_status"] = (
    unique.loc[has_sku, "sku_raw"].astype(str).str.strip().str.upper()
    == unique.loc[has_sku, "candidate_sku"].astype(str).str.upper()
).map({True: "SKU_AGREES", False: "SKU_CONFLICT"})

print("\nUNIQUE-CANDIDATE CROSS-CHECK")
print("Rows:", len(unique))

print("\nRecorded SKU status")
print(unique["recorded_sku_status"].value_counts().to_string())

print("\nRecorded versus catalogue size")
print(
    unique[
        ["size_raw", "candidate_size"]
    ].value_counts(dropna=False).head(15).to_string()
)

print("\nSample cases for review")
print(
    unique[
        [
            "sale_line_id",
            "product_description_raw",
            "sku_raw",
            "colour_raw",
            "size_raw",
            "candidate_sku",
            "candidate_colour",
            "candidate_size",
            "recorded_sku_status",
        ]
    ].head(20).to_string(index=False)
)
