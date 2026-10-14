import pandas as pd
from pathlib import Path

# Locate the original workbook
file_path = Path("data/dylte_wears_synthetic_automation_dataset.xlsx")

# Check that the file exists
if not file_path.exists():
    raise FileNotFoundError(f"Workbook not found: {file_path}")

# Load all worksheets into a dictionary of DataFrames
workbook = pd.read_excel(file_path, sheet_name=None)

# Inspect each worksheet
print("WORKSHEET OVERVIEW")
print("-" * 40)

for sheet_name, df in workbook.items():
    print(f"{sheet_name}: {df.shape[0]} rows, {df.shape[1]} columns")

# ------------------------------------------
# SALES DATA QUALITY PROFILE
# ------------------------------------------

# Select the raw sales worksheet
sales_df = workbook["Sales_Raw"]

# Build a profile for every column
quality_profile = pd.DataFrame({
    "column_name": sales_df.columns,
    "data_type": sales_df.dtypes.astype(str).values,
    "missing_count": sales_df.isna().sum().values,
    "missing_percentage": (
        sales_df.isna().mean().values * 100
    ).round(2),
    "distinct_values": sales_df.nunique().values
})

# Display the results
print("\nSALES DATA QUALITY PROFILE")
print("-" * 80)
print(quality_profile.to_string(index=False))

# ------------------------------------------
# INVESTIGATE SUSPICIOUS COLUMNS
# ------------------------------------------

columns_to_inspect = [
    "size_raw",
    "quantity_raw",
    "entry_status"
]

for column in columns_to_inspect:
    print(f"\nVALUES IN {column}")
    print("-" * 40)

    print(
        sales_df[column]
        .value_counts(dropna=False)
        .to_string()
    )

# ------------------------------------------
# DUPLICATE CHECKS
# ------------------------------------------

# Check for rows duplicated across every column
exact_duplicates = sales_df.duplicated().sum()

# Check whether sale_line_id is duplicated
duplicate_sale_ids = sales_df["sale_line_id"].duplicated().sum()

print("\nDUPLICATE CHECKS")
print("-" * 40)
print(f"Exact duplicate rows: {exact_duplicates}")
print(f"Duplicate sale_line_id values: {duplicate_sale_ids}")

# ------------------------------------------
# REFERENCE DATA VALIDATION
# ------------------------------------------

products_df = workbook["Product_Master"]

# Count duplicate product identifiers
duplicate_product_ids = products_df["product_id"].duplicated().sum()

# Count duplicate SKUs
duplicate_product_skus = products_df["sku"].duplicated().sum()

# Identify unknown SKUs across the full sales DataFrame
known_skus = set(products_df["sku"].dropna())

unknown_sku_mask = (
    sales_df["sku_raw"].notna()
    & ~sales_df["sku_raw"].isin(known_skus)
)

print(
    "Sales rows with unknown non-missing SKUs:",
    unknown_sku_mask.sum()
)

# ------------------------------------------
# INSPECT UNKNOWN SKU RECORDS
# ------------------------------------------

unknown_sku_records = sales_df.loc[
    unknown_sku_mask,
    [
        "sale_line_id",
        "product_description_raw",
        "sku_raw",
        "colour_raw",
        "size_raw",
        "quantity_raw",
    ],
]

print("\nUNKNOWN SKU RECORDS")
print("-" * 80)
print(unknown_sku_records.to_string(index=False))

# ------------------------------------------
# INVESTIGATE REPEATED DESCRIPTIONS
# ------------------------------------------

print("\nMOST COMMON RAW PRODUCT DESCRIPTIONS")
print("-" * 50)

print(
    sales_df["product_description_raw"]
    .value_counts()
    .head(15)
    .to_string()
)

print("\nTRANSACTION ID SUMMARY")
print("-" * 50)

print(
    "Missing transaction IDs:",
    sales_df["transaction_id_raw"].isna().sum()
)

print(
    "Distinct non-missing transaction IDs:",
    sales_df["transaction_id_raw"].nunique()
)

# ------------------------------------------
# TRANSACTION STRUCTURE
# ------------------------------------------

# Exclude rows with missing transaction IDs
valid_transactions = sales_df.dropna(
    subset=["transaction_id_raw"]
)

# Count the number of sale lines per transaction
lines_per_transaction = (
    valid_transactions
    .groupby("transaction_id_raw")["sale_line_id"]
    .count()
)

# Summarize transaction sizes
print("\nTRANSACTION STRUCTURE")
print("-" * 50)

print("Distinct transactions:", len(lines_per_transaction))

print(
    "Transactions with multiple sale lines:",
    (lines_per_transaction > 1).sum()
)

print(
    "Maximum sale lines in one transaction:",
    lines_per_transaction.max()
)

print("\nTRANSACTIONS WITH THE MOST SALE LINES")

print(
    lines_per_transaction
    .sort_values(ascending=False)
    .head(10)
    .to_string()
)
