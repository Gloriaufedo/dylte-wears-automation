from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "dylte_wears_synthetic_automation_dataset.xlsx"
OUTPUT_DIR = ROOT / "outputs"

APPROVED_STATUS = "Approved in controlled fixture"


def load_data():
    """Load the controlled synthetic inventory reconciliation inputs."""
    opening = pd.read_excel(
        DATA_FILE,
        sheet_name="Opening_Stock_Known",
    )
    movements = pd.read_excel(
        DATA_FILE,
        sheet_name="Synthetic_Movement_Fixture",
    )
    expected = pd.read_excel(
        DATA_FILE,
        sheet_name="Expected_Balances_Known",
    )

    return opening, movements, expected


def parse_movement_date(value):
    """Parse a movement date and return its validation status."""
    if pd.isna(value) or not str(value).strip():
        return pd.NaT, "MISSING_MOVEMENT_DATE"

    text = str(value).strip()

    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", text):
        parsed = pd.to_datetime(
            text,
            format="%d/%m/%Y",
            errors="coerce",
        )
    elif re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2}", text):
        parsed = pd.to_datetime(
            text,
            format="%m/%d/%y",
            errors="coerce",
        )
    else:
        parsed = pd.to_datetime(
            text,
            errors="coerce",
        )

    if pd.isna(parsed):
        return pd.NaT, "INVALID_MOVEMENT_DATE"

    return parsed, "VALID_DATE"


def reconcile(opening, movements):
    """Apply eligible movements in fixture order and produce an audit trail."""
    required_opening = {
        "product_id",
        "sku",
        "opening_qty",
        "unit_of_measure",
    }

    required_movements = {
        "movement_id",
        "movement_date_raw",
        "movement_type",
        "reference_id",
        "product_id",
        "quantity_delta",
        "unit_of_measure",
        "approval_status",
    }

    if not required_opening.issubset(opening.columns):
        missing = required_opening - set(opening.columns)
        raise ValueError(
            f"Opening stock is missing columns: {sorted(missing)}"
        )

    if not required_movements.issubset(movements.columns):
        missing = required_movements - set(movements.columns)
        raise ValueError(
            f"Movement fixture is missing columns: {sorted(missing)}"
        )

    if opening["product_id"].duplicated().any():
        raise ValueError("Opening stock contains duplicate product IDs.")

    if movements["movement_id"].duplicated().any():
        raise ValueError("Movement fixture contains duplicate movement IDs.")

    opening_by_product = opening.set_index("product_id").to_dict("index")

    balances = {}
    applied_counts = {}
    shortage_counts = {}

    for product_id, row in opening_by_product.items():
        quantity = pd.to_numeric(
            row["opening_qty"],
            errors="coerce",
        )

        if pd.isna(quantity) or quantity < 0:
            raise ValueError(
                f"Invalid opening quantity for product {product_id}"
            )

        balances[product_id] = float(quantity)
        applied_counts[product_id] = 0
        shortage_counts[product_id] = 0

    work = movements.copy()

    parsed = work["movement_date_raw"].apply(parse_movement_date)
    work["parsed_date"] = parsed.apply(lambda item: item[0])
    work["date_status"] = parsed.apply(lambda item: item[1])

    # Preserve the original order of the controlled synthetic fixture.
    # Dates are retained for validation and audit purposes, but they do
    # not determine movement sequence in this specific fixture.
    ordered = work

    audit_rows = []

    for row in ordered.to_dict("records"):
        product_id = row["product_id"]
        raw_delta = row["quantity_delta"]

        delta = pd.to_numeric(
            pd.Series([raw_delta]),
            errors="coerce",
        ).iloc[0]

        decision = "REVIEW"
        reason = "UNRESOLVED"

        if product_id not in balances:
            reason = "PRODUCT_NOT_IN_OPENING_STOCK"

        elif row["date_status"] != "VALID_DATE":
            reason = row["date_status"]

        elif pd.isna(delta) or delta == 0:
            reason = "INVALID_OR_ZERO_QUANTITY_DELTA"

        elif row["approval_status"] != APPROVED_STATUS:
            reason = "MOVEMENT_NOT_APPROVED"

        elif str(row["unit_of_measure"]).strip().lower() != str(
            opening_by_product[product_id]["unit_of_measure"]
        ).strip().lower():
            reason = "UNIT_MISMATCH"

        else:
            proposed_balance = balances[product_id] + float(delta)

            if proposed_balance < 0:
                if str(row["movement_type"]).strip().lower() == "sale":
                    reason = "SHORTAGE_SALE_EXCLUDED"
                    shortage_counts[product_id] += 1
                else:
                    reason = "INSUFFICIENT_STOCK_FOR_MOVEMENT"

            else:
                decision = "APPLIED"
                reason = "VALIDATED_MOVEMENT"
                balances[product_id] = proposed_balance
                applied_counts[product_id] += 1

        audit_rows.append({
            "movement_id": row["movement_id"],
            "movement_date_raw": row["movement_date_raw"],
            "parsed_date": row["parsed_date"],
            "date_status": row["date_status"],
            "movement_type": row["movement_type"],
            "reference_id": row["reference_id"],
            "product_id": product_id,
            "quantity_delta": delta,
            "unit_of_measure": row["unit_of_measure"],
            "approval_status": row["approval_status"],
            "decision": decision,
            "decision_reason": reason,
            "balance_after_decision": balances.get(
                product_id,
                float("nan"),
            ),
        })

    result = opening.copy()

    result["calculated_closing_qty"] = result["product_id"].map(balances)

    result["applied_movement_count"] = result["product_id"].map(
        applied_counts
    )

    result["excluded_shortage_movement_count"] = result["product_id"].map(
        shortage_counts
    )

    audit = pd.DataFrame(audit_rows)

    return result, audit


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    opening, movements, expected = load_data()
    calculated, audit = reconcile(opening, movements)

    expected_columns = [
        "product_id",
        "expected_closing_qty",
        "included_movement_count",
        "excluded_shortage_movement_count",
    ]

    expected_comparison = expected[expected_columns].rename(
        columns={
            "excluded_shortage_movement_count":
                "expected_excluded_shortage_movement_count"
        }
    )

    comparison = calculated.merge(
        expected_comparison,
        on="product_id",
        how="left",
        validate="one_to_one",
    )

    comparison["closing_balance_matches"] = (
        comparison["calculated_closing_qty"]
        == comparison["expected_closing_qty"]
    )

    comparison["movement_count_matches"] = (
        comparison["applied_movement_count"]
        == comparison["included_movement_count"]
    )

    calculated_path = OUTPUT_DIR / "inventory_reconciliation_known.csv"
    audit_path = OUTPUT_DIR / "inventory_movement_audit.csv"
    comparison_path = (
        OUTPUT_DIR / "inventory_reconciliation_comparison.csv"
    )

    calculated.to_csv(calculated_path, index=False)
    audit.to_csv(audit_path, index=False)
    comparison.to_csv(comparison_path, index=False)

    print("\nINVENTORY RECONCILIATION")
    print(f"Opening products: {len(opening)}")
    print(f"Movement records: {len(movements)}")

    print("\nMOVEMENT DECISIONS")
    print(audit["decision"].value_counts().to_string())

    print("\nMOVEMENT REVIEW REASONS")
    review_reasons = audit.loc[
        audit["decision"] == "REVIEW",
        "decision_reason",
    ]
    print(review_reasons.value_counts().to_string())

    print("\nEXPECTED BALANCE COMPARISON")
    print(
        comparison["closing_balance_matches"]
        .value_counts()
        .to_string()
    )

    print("\nMOVEMENT COUNT COMPARISON")
    print(
        comparison["movement_count_matches"]
        .value_counts()
        .to_string()
    )

    mismatch_mask = (
        ~comparison["closing_balance_matches"]
        | ~comparison["movement_count_matches"]
    )

    mismatch_columns = [
        "product_id",
        "sku",
        "opening_qty",
        "calculated_closing_qty",
        "expected_closing_qty",
        "applied_movement_count",
        "included_movement_count",
        "excluded_shortage_movement_count",
        "expected_excluded_shortage_movement_count",
    ]

    mismatches = comparison.loc[
        mismatch_mask,
        mismatch_columns,
    ]

    print(
        "\nProducts with one or more comparison mismatches: "
        f"{len(mismatches)}"
    )

    if not mismatches.empty:
        print(mismatches.to_string(index=False))

    print("\nFILES SAVED")
    print(calculated_path)
    print(audit_path)
    print(comparison_path)


if __name__ == "__main__":
    main()
