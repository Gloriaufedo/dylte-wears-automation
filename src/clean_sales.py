
import pandas as pd
from pathlib import Path

# Locate the project and input workbook
file_path = Path("data/dylte_wears_synthetic_automation_dataset.xlsx")

if not file_path.exists():
    raise FileNotFoundError(
        f"Could not find the workbook: {file_path}"
    )

# Load the raw sales sheet
sales_raw = pd.read_excel(
    file_path,
    sheet_name="Sales_Raw"
)

# Create a separate working copy
sales = sales_raw.copy()

print("Raw sales rows:", len(sales_raw))
print("Working copy rows:", len(sales))
print("Original columns:", list(sales_raw.columns))


# Check for missing values in each column
missing_report = pd.DataFrame({
    "missing_count": sales.isna().sum(),
    "missing_percentage": (
        sales.isna().sum() / len(sales) * 100
    ).round(2)
})

# Show columns with missing values only
missing_report = missing_report[
    missing_report["missing_count"] > 0
].sort_values(
    by="missing_count",
    ascending=False
)

print("\nMISSING VALUE REPORT")
print(missing_report)


# Create a normalised product description
sales["product_description_clean"] = (
    sales["product_description_raw"]
    .astype("string")
    .str.strip()
    .str.lower()
)

print("\nDESCRIPTION NORMALISATION CHECK")
print(
    sales[
        [
            "product_description_raw",
            "product_description_clean"
        ]
    ].head(10)
)


# Normalise SKU and colour without changing raw fields
sales["sku_clean"] = (
    sales["sku_raw"]
    .astype("string")
    .str.strip()
    .str.upper()
)

sales["colour_clean"] = (
    sales["colour_raw"]
    .astype("string")
    .str.strip()
    .str.lower()
)

print("\nSKU AND COLOUR NORMALISATION CHECK")
print(
    sales[
        [
            "sku_raw",
            "sku_clean",
            "colour_raw",
            "colour_clean"
        ]
    ].head(12).to_string(index=False)
)


# Inspect numeric fields before cleaning
print("\nQUANTITY VALUES")
print(sales["quantity_raw"].value_counts(dropna=False).sort_index())

print("\nQUANTITY DATA TYPE")
print(sales["quantity_raw"].dtype)

print("\nSIZE VALUES")
print(sales["size_raw"].value_counts(dropna=False).sort_index())

print("\nSIZE DATA TYPE")
print(sales["size_raw"].dtype)


# Validate quantities before converting to whole numbers
quantity = sales["quantity_raw"]

invalid_quantity_mask = quantity.notna() & (
    (quantity <= 0) | (quantity % 1 != 0)
)

print("\nINVALID QUANTITY COUNT")
print(invalid_quantity_mask.sum())

# Create a clean integer column while preserving missing values
sales["quantity_clean"] = quantity.astype("Int64")

print("\nCLEAN QUANTITY VALUES")
print(
    sales["quantity_clean"]
    .value_counts(dropna=False)
    .sort_index()
)


# Load the canonical product catalogue
products = pd.read_excel(
    file_path,
    sheet_name="Product_Master"
)

print("\nPRODUCT MASTER COLUMNS")
print(products.columns.tolist())

print("\nPRODUCT SIZE AND UNIT EXAMPLES")
columns_to_inspect = [
    col for col in ["product_name", "size", "colour", "unit_of_measure", "sku"]
    if col in products.columns
]

print(products[columns_to_inspect].head(15).to_string(index=False))

print("\nUNIQUE PRODUCT SIZES")
if "size" in products.columns:
    print(products["size"].value_counts(dropna=False))
else:
    print("No column named 'size'; inspect the columns above.")


# Investigate the unusual raw size value
size_12_mask = sales["size_raw"].eq(12)

print("\nSALES ROWS WITH SIZE 12")
print(
    sales.loc[
        size_12_mask,
        [
            "sale_line_id",
            "product_description_raw",
            "sku_raw",
            "colour_raw",
            "size_raw",
            "quantity_raw"
        ]
    ].head(20).to_string(index=False)
)

print("\nTOTAL ROWS WITH SIZE 12")
print(size_12_mask.sum())


# Match recognised sales SKUs to the product catalogue
sales_with_size = sales.loc[
    sales["size_raw"].notna(),
    [
        "sale_line_id",
        "product_description_raw",
        "sku_clean",
        "size_raw"
    ]
]

catalogue_size_check = sales_with_size.merge(
    products[["sku", "product_name", "size"]],
    left_on="sku_clean",
    right_on="sku",
    how="left",
    indicator=True
)

# Keep rows whose SKU exists in the catalogue
known_sku_rows = catalogue_size_check.loc[
    catalogue_size_check["_merge"] == "both"
]

print("\nSIZE CHECK FOR RECOGNISED SKUS")
print(
    known_sku_rows[
        [
            "sale_line_id",
            "product_description_raw",
            "sku_clean",
            "product_name",
            "size_raw",
            "size"
        ]
    ].head(15).to_string(index=False)
)

print("\nROWS WITH SIZE 12 AND RECOGNISED SKUS")
print(len(known_sku_rows))


# Quantify size conflicts for recognised SKUs
known_sku_rows = known_sku_rows.copy()

known_sku_rows["size_conflict"] = (
    known_sku_rows["size_raw"].astype("string").str.replace(
        r"\.0$", "", regex=True
    ).str.strip().str.upper()
    != known_sku_rows["size"].astype("string").str.strip().str.upper()
)

print("\nSIZE CONFLICT SUMMARY")
print("Recognised SKU rows with recorded sizes:", len(known_sku_rows))
print("Rows with size conflicts:", known_sku_rows["size_conflict"].sum())

print("\nCONFLICT RATE (%)")
if len(known_sku_rows) > 0:
    print(
        round(
            known_sku_rows["size_conflict"].mean() * 100,
            2
        )
    )

print("\nSIZE CONFLICT EXAMPLES")
print(
    known_sku_rows.loc[
        known_sku_rows["size_conflict"],
        ["sale_line_id", "sku_clean", "size_raw", "size"]
    ].head(10).to_string(index=False)
)


# Create a size-validation status for sales with recognised SKUs
known_sku_rows["size_status"] = "CONFLICT"

print("\nSIZE VALIDATION STATUS")
print(known_sku_rows["size_status"].value_counts())

# Keep the raw size and catalogue size visible for review
print("\nSIZE REVIEW QUEUE")
print(
    known_sku_rows[
        [
            "sale_line_id",
            "product_description_raw",
            "sku_clean",
            "size_raw",
            "size",
            "size_status"
        ]
    ].head(10).to_string(index=False)
)


# Build a complete size-validation dataset
size_check = sales[
    ["sale_line_id", "sku_clean", "size_raw"]
].merge(
    products[["sku", "size"]],
    left_on="sku_clean",
    right_on="sku",
    how="left",
    indicator=True
)

# Normalise formats only for comparison
raw_size_compare = (
    size_check["size_raw"]
    .astype("string")
    .str.replace(r"\.0$", "", regex=True)
    .str.strip()
    .str.upper()
)

catalogue_size_compare = (
    size_check["size"]
    .astype("string")
    .str.strip()
    .str.upper()
)

# Assign status based on evidence
size_check["size_status"] = "CONFLICT"

size_check.loc[
    size_check["size_raw"].isna(),
    "size_status"
] = "MISSING_SIZE"

size_check.loc[
    size_check["sku_clean"].isna()
    | (size_check["_merge"] == "left_only"),
    "size_status"
] = "SKU_NOT_FOUND"

size_check.loc[
    (size_check["_merge"] == "both")
    & size_check["size_raw"].notna()
    & raw_size_compare.eq(catalogue_size_compare).fillna(False),
    "size_status"
] = "MATCH"

print("\nCOMPLETE SIZE VALIDATION SUMMARY")
print(size_check["size_status"].value_counts(dropna=False))


# Create independent validation flags
size_check["sku_missing"] = size_check["sku_clean"].isna()

size_check["sku_unknown"] = (
    size_check["sku_clean"].notna()
    & (size_check["_merge"] == "left_only")
)

size_check["size_missing"] = size_check["size_raw"].isna()

size_check["size_conflict"] = (
    (size_check["_merge"] == "both")
    & size_check["size_raw"].notna()
    & raw_size_compare.ne(catalogue_size_compare).fillna(False)
)

print("\nINDEPENDENT DATA-QUALITY COUNTS")
for flag in [
    "sku_missing",
    "sku_unknown",
    "size_missing",
    "size_conflict"
]:
    print(f"{flag}: {size_check[flag].sum()}")


# Inspect combinations of SKU and size issues
print("\nSKU AND SIZE ISSUE COMBINATIONS")

print(
    pd.crosstab(
        [
            size_check["sku_missing"],
            size_check["sku_unknown"]
        ],
        size_check["size_missing"],
        rownames=["SKU missing", "SKU unknown"],
        colnames=["Size missing"],
        dropna=False
    )
)

print("\nEXAMPLE ROWS WITH MISSING SKU AND SIZE")
print(
    size_check.loc[
        size_check["sku_missing"] & size_check["size_missing"],
        ["sale_line_id", "sku_clean", "size_raw"]
    ].head(10).to_string(index=False)
)


# Build a trusted SKU lookup from the product catalogue
sku_lookup = products.set_index("sku")[
    ["product_id", "product_name", "colour", "size", "unit_of_measure"]
]

# Attach canonical details using the cleaned sales SKU
sales_with_catalogue = sales.merge(
    sku_lookup,
    left_on="sku_clean",
    right_index=True,
    how="left",
    validate="many_to_one"
)

# Flag whether the SKU matched the catalogue
sales_with_catalogue["sku_match_status"] = "SKU_NOT_FOUND"

sales_with_catalogue.loc[
    sales_with_catalogue["sku_clean"].isna(),
    "sku_match_status"
] = "SKU_MISSING"

sales_with_catalogue.loc[
    sales_with_catalogue["product_id"].notna(),
    "sku_match_status"
] = "SKU_MATCHED"

print("\nSKU LOOKUP SUMMARY")
print(sales_with_catalogue["sku_match_status"].value_counts())

print("\nSKU LOOKUP EXAMPLES")
print(
    sales_with_catalogue[
        [
            "sale_line_id",
            "sku_clean",
            "product_id",
            "product_name",
            "sku_match_status"
        ]
    ].head(15).to_string(index=False)
)


# Normalise canonical product names for comparison
sales_with_catalogue["product_name_clean"] = (
    sales_with_catalogue["product_name"]
    .astype("string")
    .str.strip()
    .str.lower()
)

# Flag exact description/name agreement
sales_with_catalogue["description_exact_match"] = (
    sales_with_catalogue["product_description_clean"]
    == sales_with_catalogue["product_name_clean"]
)

# Exact comparison is a diagnostic, not a final matching rule
matched_sku_rows = sales_with_catalogue.loc[
    sales_with_catalogue["sku_match_status"] == "SKU_MATCHED"
]

print("\nDESCRIPTION AGREEMENT FOR MATCHED SKUS")
print(
    matched_sku_rows["description_exact_match"]
    .value_counts(dropna=False)
)

print("\nEXAMPLES WHERE SKU MATCHES BUT DESCRIPTION DIFFERS")
print(
    matched_sku_rows.loc[
        ~matched_sku_rows["description_exact_match"],
        [
            "sale_line_id",
            "product_description_raw",
            "sku_clean",
            "product_name",
            "colour_raw",
            "size_raw"
        ]
    ].head(15).to_string(index=False)
)


# Compare recorded colour with catalogue colour
sales_with_catalogue["colour_raw_clean"] = (
    sales_with_catalogue["colour_raw"]
    .astype("string")
    .str.strip()
    .str.lower()
)

sales_with_catalogue["catalogue_colour_clean"] = (
    sales_with_catalogue["colour"]
    .astype("string")
    .str.strip()
    .str.lower()
)

sales_with_catalogue["colour_match_status"] = "NOT_CHECKED"

# Only compare colours where the SKU matched a catalogue product
matched_sku_mask = (
    sales_with_catalogue["sku_match_status"] == "SKU_MATCHED"
)

sales_with_catalogue.loc[
    matched_sku_mask
    & sales_with_catalogue["colour_raw_clean"].isna(),
    "colour_match_status"
] = "MISSING_RECORDED_COLOUR"

sales_with_catalogue.loc[
    matched_sku_mask
    & sales_with_catalogue["colour_raw_clean"].notna()
    & sales_with_catalogue["catalogue_colour_clean"].notna()
    & sales_with_catalogue["colour_raw_clean"].eq(
        sales_with_catalogue["catalogue_colour_clean"]
    ),
    "colour_match_status"
] = "MATCH"

sales_with_catalogue.loc[
    matched_sku_mask
    & sales_with_catalogue["colour_raw_clean"].notna()
    & sales_with_catalogue["catalogue_colour_clean"].notna()
    & sales_with_catalogue["colour_raw_clean"].ne(
        sales_with_catalogue["catalogue_colour_clean"]
    ),
    "colour_match_status"
] = "CONFLICT"

print("\nCOLOUR VALIDATION FOR MATCHED SKUS")
print(
    sales_with_catalogue.loc[
        matched_sku_mask, "colour_match_status"
    ].value_counts(dropna=False)
)

print("\nEXAMPLES OF COLOUR CONFLICTS")
print(
    sales_with_catalogue.loc[
        matched_sku_mask
        & (sales_with_catalogue["colour_match_status"] == "CONFLICT"),
        [
            "sale_line_id",
            "product_description_raw",
            "sku_clean",
            "product_name",
            "colour_raw",
            "colour",
        ],
    ].head(15).to_string(index=False)
)


# Load the approved product aliases
aliases = pd.read_excel(
    file_path,
    sheet_name="Product_Aliases"
)

print("\nALIAS TABLE SHAPE")
print(aliases.shape)

print("\nALIAS TABLE COLUMNS")
print(aliases.columns.tolist())

print("\nFIRST 15 ALIASES")
print(aliases.head(15).to_string(index=False))

print("\nALIASES PER PRODUCT")
print(
    aliases.groupby("product_id")
    .size()
    .describe()
)


# Normalise aliases without changing the original alias text
aliases["alias_text_clean"] = (
    aliases["alias_text"]
    .astype("string")
    .str.strip()
    .str.lower()
)

# Count how many distinct products each alias identifies
alias_product_counts = (
    aliases.groupby("alias_text_clean")["product_id"]
    .nunique()
    .sort_values(ascending=False)
)

print("\nALIAS UNIQUENESS PROFILE")
print("Total alias rows:", len(aliases))
print("Distinct normalised aliases:", alias_product_counts.size)
print(
    "Aliases linked to multiple products:",
    (alias_product_counts > 1).sum()
)

print("\nMOST AMBIGUOUS ALIASES")
print(alias_product_counts.head(15).to_string())

# Show the actual products behind the ambiguous aliases
ambiguous_aliases = alias_product_counts[
    alias_product_counts > 1
].index

ambiguous_alias_details = (
    aliases.loc[
        aliases["alias_text_clean"].isin(ambiguous_aliases),
        ["alias_text", "product_id", "alias_type"]
    ]
    .drop_duplicates()
    .sort_values(["alias_text", "product_id"])
)

print("\nEXAMPLES OF AMBIGUOUS ALIASES")
print(ambiguous_alias_details.head(30).to_string(index=False))


# Join ambiguous aliases to the product catalogue
alias_product_details = aliases.merge(
    products[
        [
            "product_id",
            "sku",
            "product_name",
            "category",
            "colour",
            "size",
            "unit_of_measure",
            "active_status",
        ]
    ],
    on="product_id",
    how="left",
    validate="many_to_one",
)

print("\nPRODUCT DETAILS FOR AMBIGUOUS ALIASES")

example_alias = "alo top"

print(
    alias_product_details.loc[
        alias_product_details["alias_text_clean"] == example_alias,
        [
            "alias_text",
            "product_id",
            "sku",
            "product_name",
            "category",
            "colour",
            "size",
            "unit_of_measure",
            "active_status",
        ],
    ]
    .drop_duplicates()
    .to_string(index=False)
)


# Test whether product name + colour + size uniquely identifies a SKU
variant_columns = ["product_name", "colour", "size"]

variant_counts = (
    products.groupby(variant_columns, dropna=False)
    .agg(
        sku_count=("sku", "nunique"),
        product_count=("product_id", "nunique"),
        skus=("sku", lambda values: ", ".join(sorted(values))),
    )
    .reset_index()
)

print("\nVARIANT UNIQUENESS SUMMARY")
print("Total catalogue products:", len(products))
print(
    "Distinct name-colour-size combinations:",
    len(variant_counts),
)
print(
    "Combinations linked to multiple SKUs:",
    (variant_counts["sku_count"] > 1).sum(),
)

print("\nEXAMPLES OF NON-UNIQUE VARIANTS")
print(
    variant_counts.loc[
        variant_counts["sku_count"] > 1
    ]
    .head(15)
    .to_string(index=False)
)
