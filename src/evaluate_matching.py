
from pathlib import Path

import pandas as pd


# Locate project files
project_root = Path(__file__).resolve().parent.parent
workbook_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)
results_path = project_root / "outputs" / "validation_results.csv"


# Load predictions and ground truth separately
predictions = pd.read_csv(results_path)

ground_truth = pd.read_excel(
    workbook_path,
    sheet_name="Ground_Truth_EVAL",
)

# Keep only the fields needed for evaluation.
truth = ground_truth[
    [
        "sale_line_id",
        "true_product_id",
        "true_sku",
        "identification_class",
        "expected_action",
        "quantity_valid",
        "duplicate_status",
        "ambiguity_reason",
        "expected_stock_effect_if_fully_approved",
    ]
].copy()

# Ensure the evaluation join is one-to-one.
assert predictions["sale_line_id"].is_unique
assert truth["sale_line_id"].is_unique

evaluation = predictions.merge(
    truth,
    on="sale_line_id",
    how="left",
    validate="one_to_one",
    indicator=True,
)

# Confirm every prediction has a ground-truth record.
assert (evaluation["_merge"] == "both").all(), (
    "Some predictions do not have a matching ground-truth record."
)

evaluation = evaluation.drop(columns="_merge")

# A prediction is correct only when its product identity is correct.
evaluation["identity_correct"] = (
    evaluation["matched_product_id"].notna()
    & evaluation["matched_product_id"].eq(
        evaluation["true_product_id"]
    )
)

# Evaluate only automatically accepted lines for precision.
accepted = evaluation[
    evaluation["processing_decision"] == "ACCEPT"
].copy()

accepted_count = len(accepted)
correct_accepted = int(accepted["identity_correct"].sum())

precision = (
    correct_accepted / accepted_count
    if accepted_count
    else float("nan")
)

coverage = len(accepted) / len(evaluation) if len(evaluation) else 0

print("\nMATCHING EVALUATION")
print("Total sales lines:", len(evaluation))
print("Automatically accepted:", accepted_count)
print("Correct accepted product identities:", correct_accepted)
print(f"Accepted-match precision: {precision:.2%}")
print(f"Automatic acceptance coverage: {coverage:.2%}")

print("\nACCEPTED LINES WITH INCORRECT PRODUCT IDENTITIES")
incorrect_accepted = accepted[~accepted["identity_correct"]]

print("Count:", len(incorrect_accepted))

if not incorrect_accepted.empty:
    print(
        incorrect_accepted[
            [
                "sale_line_id",
                "matched_sku",
                "true_sku",
                "matched_product_id",
                "true_product_id",
            ]
        ].to_string(index=False)
    )

print("\nGROUND-TRUTH EXPECTED ACTIONS")
print(ground_truth["expected_action"].value_counts(dropna=False))

print("\nEXPECTED ACTION BY CURRENT DECISION")
print(
    evaluation.groupby(
        ["processing_decision", "expected_action"],
        dropna=False
    ).size().unstack(fill_value=0).to_string()
)

print("\nQUANTITY VALIDITY")
print(ground_truth["quantity_valid"].value_counts(dropna=False))

print("\nDUPLICATE STATUS")
print(ground_truth["duplicate_status"].value_counts(dropna=False))

print("\nEXPECTED HOLD CASES — CURRENT DECISIONS")
expected_holds = evaluation[
    evaluation["expected_action"] == "HOLD"
]

print(
    expected_holds.groupby(
        ["processing_decision", "decision_reason"],
        dropna=False,
    ).size().to_string()
)

print("\nSAMPLE EXPECTED HOLD CASES")
columns_to_inspect = [
    "sale_line_id",
    "product_description_raw",
    "sku_raw",
    "quantity_raw",
    "matched_sku",
    "quantity_validation_status",
    "colour_validation_status",
    "processing_decision",
    "decision_reason",
    "duplicate_status",
    "ambiguity_reason",
]

print(
    expected_holds[columns_to_inspect]
    .head(15)
    .to_string(index=False)
)

print("\nEXPECTED AUTO-ACCEPT CASES CURRENTLY SENT FOR REVIEW")
missed_auto_accepts = evaluation[
    (evaluation["expected_action"] == "AUTO_ACCEPT")
    & (evaluation["processing_decision"] == "REVIEW")
]

print(
    missed_auto_accepts[
        [
            "sale_line_id",
            "product_description_raw",
            "sku_raw",
            "quantity_raw",
            "sku_match_status",
            "colour_validation_status",
            "size_validation_status",
            "quantity_validation_status",
            "decision_reason",
            "duplicate_status",
            "ambiguity_reason",
        ]
    ]
    .head(15)
    .to_string(index=False)
)

# Save the detailed evaluation separately from production predictions.
output_path = project_root / "outputs" / "matching_evaluation.csv"
evaluation.to_csv(output_path, index=False)

print("\nDetailed evaluation saved to:", output_path)

print("\nEXPECTED HOLD — GROUND-TRUTH BREAKDOWN")
print(
    evaluation[
        evaluation["expected_action"] == "HOLD"
    ].groupby(
        [
            "identification_class",
            "quantity_valid",
            "duplicate_status",
            "true_product_id",
        ],
        dropna=False,
    ).size().to_string()
)

print("\nEXPECTED AUTO-ACCEPT — CURRENTLY REVIEWED")
missed = evaluation[
    (evaluation["expected_action"] == "AUTO_ACCEPT")
    & (evaluation["processing_decision"] == "REVIEW")
]

print(
    missed.groupby(
        [
            "decision_reason",
            "identification_class",
            "quantity_valid",
            "duplicate_status",
        ],
        dropna=False,
    ).size().to_string()
)