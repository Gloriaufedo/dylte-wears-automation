# Dylte Wears — Data Quality Rules

## Purpose

Document the data-quality issues identified during profiling, their business risks, and the proposed handling rules before implementing the preparation pipeline.

| Issue | Evidence | Business risk | Proposed handling | Blocks stock movement |
|---|---|---|---|---|
| Missing SKU | 440 of 800 sales rows have no SKU (55%). | Product may be matched to the wrong item or variant. | Attempt matching using validated descriptions, aliases, and available variant details. Send uncertain matches for review. | Conditional: block until the product and variant are validated. |
| SKU not found in product master | 41 sales rows contain an unknown, non-missing SKU. | An invalid or incorrect product reference could cause stock to be deducted from the wrong item. | Flag the SKU, preserve the raw value, and investigate whether a valid product can be established. Never replace it automatically without sufficient evidence. | Yes, until resolved and validated. |
| Missing or ambiguous product variant | Size is missing in 404 rows; all 41 inspected unknown-SKU records have missing sizes. Some descriptions are vague. | A correct product category could still lead to selection of the wrong variant. | Compare against product-master requirements. Request review or hold the record when the exact variant cannot be established. | Yes, when missing variant information prevents safe identification. |
| Missing quantity | 31 of 800 sales rows have missing quantities (3.88%). | Stock could be overstated or understated if quantity is guessed or treated as zero. | Flag the record and obtain a verified quantity before creating a stock movement. | Yes, until quantity is verified. |
| Missing transaction ID | 59 of 800 sales rows have no transaction ID (7.38%). | Transaction-level reconciliation and duplicate investigation may be less reliable. | Preserve the record, flag the missing ID, and investigate alternative evidence. Do not invent a transaction ID. | Conditional: block only if the missing ID prevents a required validation or duplicate check. |
| Uncertain or invalid date/amount information | Raw dates and amounts use mixed formats; ambiguous dates and unusual amount notation need investigation. | Incorrect dates can distort reporting and reconciliation; incorrect amounts can distort sales totals. | Preserve raw values, parse only when the interpretation is unambiguous, and flag invalid or ambiguous values for review. Define whether a verified date or amount is required for the relevant stock-processing decision. | Conditional: block if the field is required for a control that cannot otherwise be satisfied. |

## Implementation note

These are documented handling rules and findings from the synthetic dataset. A proposed rule should not be described as implemented unless the corresponding code and tests verify that behavior.

The findings apply to this synthetic dataset and should not be interpreted as measurements from a live retail operation.