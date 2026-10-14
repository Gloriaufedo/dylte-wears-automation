from pathlib import Path

import pandas as pd

from integration_rules import classify_sales_movements
from reconcile_inventory import load_data, reconcile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    opening, movements, _ = load_data()

    validation_path = OUTPUT_DIR / "validation_results.csv"

    if not validation_path.exists():
        raise FileNotFoundError(
            "Run src/run_validation.py before integrated reconciliation."
        )

    validation = pd.read_csv(validation_path)

    sales_mask = (
        movements["movement_type"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("sale")
    )

    sales_movements = movements.loc[sales_mask].copy()
    other_movements = movements.loc[~sales_mask].copy()

    linked = classify_sales_movements(
        sales_movements,
        validation,
    )

    eligible_sales = linked.loc[
        linked["integration_decision"].eq("ELIGIBLE"),
        sales_movements.columns,
    ].copy()

    movements_for_reconciliation = pd.concat(
        [other_movements, eligible_sales],
        ignore_index=True,
    )

    calculated, inventory_audit = reconcile(
        opening,
        movements_for_reconciliation,
    )

    linked.to_csv(
        OUTPUT_DIR / "integrated_sales_movement_audit.csv",
        index=False,
    )

    calculated.to_csv(
        OUTPUT_DIR / "integrated_inventory_balances.csv",
        index=False,
    )

    inventory_audit.to_csv(
        OUTPUT_DIR / "integrated_inventory_movement_audit.csv",
        index=False,
    )

    print("\nINTEGRATED RECONCILIATION")
    print("Original movement records:", len(movements))
    print("Non-sale movements retained:", len(other_movements))
    print("Sales movements:", len(sales_movements))

    print("\nSALES-MOVEMENT ELIGIBILITY")
    print(linked["integration_decision"].value_counts().to_string())

    print("\nINTEGRATION REASONS")
    print(linked["integration_reason"].value_counts().to_string())

    print("\nINVENTORY MOVEMENT DECISIONS")
    print(inventory_audit["decision"].value_counts().to_string())

    print("\nFiles saved:")
    print(OUTPUT_DIR / "integrated_sales_movement_audit.csv")
    print(OUTPUT_DIR / "integrated_inventory_balances.csv")
    print(OUTPUT_DIR / "integrated_inventory_movement_audit.csv")


if __name__ == "__main__":
    main()