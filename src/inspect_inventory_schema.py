
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
workbook = (
    project_root
    / "data"
    / "dylte_wears_synthetic_automation_dataset.xlsx"
)

sheets_to_inspect = [
    "Opening_Stock_Known",
    "Opening_Stock_Imperfect",
    "Stock_Receipts_Raw",
    "Stock_Adjustments_Raw",
    "Expected_Balances_Known",
    "Expected_Balances_Imperfect",
    "Synthetic_Movement_Fixture",
]

for sheet_name in sheets_to_inspect:
    df = pd.read_excel(workbook, sheet_name=sheet_name)

    print(f"\n{'=' * 65}")
    print(f"SHEET: {sheet_name}")
    print(f"Rows: {len(df)}")
    print("Columns:", df.columns.tolist())
    print("\nSample rows:")
    print(df.head(3).to_string(index=False))
