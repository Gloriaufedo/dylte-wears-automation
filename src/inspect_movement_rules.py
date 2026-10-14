
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent.parent
workbook = root / "data" / "dylte_wears_synthetic_automation_dataset.xlsx"

movements = pd.read_excel(workbook, sheet_name="Synthetic_Movement_Fixture")
adjustments = pd.read_excel(workbook, sheet_name="Stock_Adjustments_Raw")
imperfect = pd.read_excel(workbook, sheet_name="Opening_Stock_Imperfect")

print("\nMOVEMENT TYPES")
print(movements["movement_type"].value_counts(dropna=False).to_string())

print("\nMOVEMENT APPROVAL STATUSES")
print(movements["approval_status"].value_counts(dropna=False).to_string())

print("\nMOVEMENT TYPE + APPROVAL STATUS")
print(
    pd.crosstab(
        movements["movement_type"],
        movements["approval_status"],
        dropna=False,
    ).to_string()
)

print("\nMOVEMENT QUANTITY SUMMARY")
print(
    movements.groupby(["movement_type", "approval_status"], dropna=False)
    ["quantity_delta"]
    .agg(["count", "sum", "min", "max"])
    .to_string()
)

print("\nADJUSTMENT APPROVAL STATUSES")
print(adjustments["approval_status"].value_counts(dropna=False).to_string())

print("\nIMPERFECT OPENING BALANCE STATUSES")
print(imperfect["balance_status"].value_counts(dropna=False).to_string())

print("\nMOVEMENT SAMPLE")
print(movements.groupby(["movement_type", "approval_status"], dropna=False).head(2).to_string(index=False))
