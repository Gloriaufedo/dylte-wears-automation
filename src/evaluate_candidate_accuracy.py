
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
workbook_path = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)
results_path = project_root / "outputs" / "candidate_evaluation.csv"

candidates = pd.read_csv(results_path)
truth = pd.read_excel(workbook_path, sheet_name="Ground_Truth_EVAL")

evaluation = candidates.merge(
    truth[["sale_line_id", "true_product_id", "identification_class"]],
    on="sale_line_id",
    how="left",
    validate="one_to_one",
)

assert evaluation["true_product_id"].notna().all()

unique = evaluation[
    evaluation["candidate_status"] == "UNIQUE_CANDIDATE"
].copy()

unique["candidate_product_id"] = unique["candidate_product_ids"].fillna("")

unique["candidate_is_correct"] = (
    unique["candidate_product_id"] == unique["true_product_id"]
)

print("\nUNIQUE-CANDIDATE EVALUATION")
print("Unique candidates:", len(unique))
print("Correct unique candidates:", int(unique["candidate_is_correct"].sum()))

if len(unique):
    print(
        "Unique-candidate accuracy:",
        f"{unique['candidate_is_correct'].mean():.2%}",
    )

print("\nACCURACY BY IDENTIFICATION CLASS")
print(
    unique.groupby("identification_class")["candidate_is_correct"]
    .agg(["count", "sum", "mean"])
    .to_string()
)

output_path = project_root / "outputs" / "candidate_accuracy_evaluation.csv"
evaluation.to_csv(output_path, index=False)

print("\nDetailed evaluation saved to:", output_path)
