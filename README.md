# Dylte Wears: Sales Validation and Inventory Reconciliation Automation

## Overview

Dylte Wears Sales Validation and Inventory Reconciliation Automation is a Python-based portfolio project exploring how retail sales records can be validated, uncertain product matches routed for review, and approved sales movements reconciled against inventory.

The project uses a synthetic retail dataset inspired by clothing retail operations. It combines rule-based product matching, data-quality checks, decision queues, movement validation, and inventory reconciliation.

The central design principle is that **uncertain records should be reviewed rather than silently accepted or used to change inventory**.

## Problem Statement

Retail sales and stock records may contain missing product codes, inconsistent descriptions, incomplete attributes, quantity issues, and movements that cannot safely be linked to validated sales.

Automatically accepting these records can lead to incorrect product attribution and unreliable inventory balances.

This project explores a controlled workflow that separates validated records from records requiring human review or being placed on hold.

## Objectives

- Validate sales records against product and data-quality rules.
- Match known SKUs and generate candidates for records with missing SKUs.
- Preserve ambiguous matches for human review.
- Route incomplete, inconsistent, or invalid records to appropriate queues.
- Link validated sales to corresponding inventory movements.
- Apply only eligible movements through the inventory reconciliation rules.
- Evaluate matching behavior and verify decision logic with automated tests.

## Technology Stack

- Python
- pandas
- Excel and CSV data files
- pytest
- Git and GitHub for version control and project sharing

## Workflow

1. **Load synthetic data:** Read the product catalogue, aliases, sales records, opening stock, and stock movements.
2. **Match products:** Match known SKUs and generate candidate products for missing-SKU records.
3. **Validate sales:** Apply rules covering quantities, product identity, colour consistency, and uncertain size formats.
4. **Route decisions:** Separate accepted sales, records requiring review, and records placed on hold.
5. **Check movement eligibility:** Link sales movements to validation results and verify product, quantity, and approval consistency.
6. **Reconcile inventory:** Pass eligible sales movements and retained non-sale movements through the inventory reconciliation rules.
7. **Evaluate and test:** Generate audit outputs and run automated tests covering matching, validation, and integration decisions.

## Synthetic Dataset

The workbook contains:

- 300 catalogue products
- 636 product aliases
- 800 sales lines
- 150 stock receipts
- 30 stock adjustments
- 800 evaluation labels for synthetic matching analysis
- 46 pilot test cases
- 8 adversarial cases

The dataset is synthetic. Results should not be interpreted as evidence of performance on real retail transactions.

## Current Results

On the current synthetic dataset, the sales validation pipeline produced:

| Processing outcome | Records |
|---|---:|
| Accepted | 111 |
| Requires review | 677 |
| On hold | 12 |
| **Total sales lines** | **800** |

The integrated workflow processed 473 original inventory movement records:

| Integration measure | Records |
|---|---:|
| Sales movements | 338 |
| Eligible sales movements | 56 |
| Sales movements requiring review | 282 |

The integrated inventory movement audit reported 184 applied movements and 7 movements requiring review.

These figures describe the current synthetic dataset and configured rules. They do not demonstrate real-world accuracy, time savings, or production performance.

## Safety and Control Design

- Ambiguous product matches are not automatically accepted.
- Numeric size values are not silently converted to catalogue size labels when their meaning is uncertain.
- Sales must pass validation and match their corresponding movement in product and quantity.
- Sales movements must meet the configured approval condition before becoming eligible.
- The inventory reconciliation module retains its own movement validation rules.
- Audit outputs preserve decisions and reasons for inspection.

## Project Structure

```text
dylte-wears-automation/
├── data/
│   └── dylte_wears_synthetic_automation_dataset.xlsx
├── outputs/
│   ├── accepted_sales.csv
│   ├── review_queue.csv
│   ├── hold_queue.csv
│   ├── validation_results.csv
│   ├── integrated_sales_movement_audit.csv
│   ├── integrated_inventory_balances.csv
│   └── integrated_inventory_movement_audit.csv
├── src/
│   ├── candidate_matching.py
│   ├── matching.py
│   ├── run_sku_matching.py
│   ├── run_validation.py
│   ├── integration_rules.py
│   ├── integrated_reconciliation.py
│   ├── reconcile_inventory.py
│   └── test_*.py
├── data_quality_rules.md
├── requirements.txt
└── README.md
```

Additional exploratory and evaluation scripts are retained in `src/`.

## Setup

Python 3.9 or a compatible version is required.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the Workflow

Run sales validation:

```bash
python src/run_validation.py
```

Then run integrated inventory reconciliation:

```bash
python src/integrated_reconciliation.py
```

Run the automated tests:

```bash
python -m pytest src -v
```

The integration script expects the validation output to exist before it runs.

## Limitations

- The data is synthetic and does not represent a live retail operation.
- The workflow has not been validated against real-world business data.
- Candidate matching is constrained by the catalogue, aliases, and configured rules.
- Records requiring review still need an appropriate human decision process.
- The project is a controlled prototype, not a production inventory system.
- The reported outputs do not establish measured business savings or operational impact.

## Future Improvements

- Add a repeatable end-to-end test that runs the pipeline from fresh inputs.
- Improve configuration and reproducibility by pinning tested dependency versions.
- Add explicit tests for malformed inputs and additional inventory edge cases.
- Create a concise workflow diagram and a documented evaluation methodology.
- Assess the workflow against appropriately anonymized real data if authorized access becomes available.

## Author

Built as a data analytics and automation portfolio project focused on data quality, cautious automation, auditability, and inventory control.
