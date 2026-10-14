
from pathlib import Path
import pandas as pd

from candidate_matching import find_alias_candidates, filter_candidates_by_colour

def test_alo_top_returns_all_candidates():
    project_root = Path(__file__).resolve().parent.parent
    workbook_path = (
        project_root
        / "data"
        / "dylte_wears_synthetic_automation_dataset.xlsx"
    )

    aliases = pd.read_excel(
        workbook_path,
        sheet_name="Product_Aliases",
    )
    products = pd.read_excel(
        workbook_path,
        sheet_name="Product_Master",
    )

    candidates = find_alias_candidates(
        "Alo Top",
        aliases,
        products,
    )

    assert candidates["product_id"].nunique() == 14
    assert candidates["sku"].nunique() == 14


def test_unknown_description_returns_no_candidates():
    project_root = Path(__file__).resolve().parent.parent
    workbook_path = (
        project_root
        / "data"
        / "dylte_wears_synthetic_automation_dataset.xlsx"
    )

    aliases = pd.read_excel(
        workbook_path,
        sheet_name="Product_Aliases",
    )
    products = pd.read_excel(
        workbook_path,
        sheet_name="Product_Master",
    )

    candidates = find_alias_candidates(
        "completely unknown product",
        aliases,
        products,
    )

    assert candidates.empty


from candidate_matching import filter_candidates_by_colour


def test_colour_filter_narrows_alo_top_candidates():
    candidates = pd.DataFrame([
        {"product_id": "PRD-0010", "sku": "DW-CAS-0010",
         "product_name": "Alo Top", "colour": "Pink", "size": "M"},
        {"product_id": "PRD-0025", "sku": "DW-CAS-0025",
         "product_name": "Alo Top", "colour": "Black", "size": "S"},
        {"product_id": "PRD-0138", "sku": "DW-CAS-0138",
         "product_name": "Alo Top", "colour": "Pink", "size": "M"},
    ])

    result = filter_candidates_by_colour(candidates, " pink ")

    assert len(result) == 2
    assert set(result["sku"]) == {"DW-CAS-0010", "DW-CAS-0138"}


def test_missing_colour_does_not_remove_candidates():
    candidates = pd.DataFrame([
        {"product_id": "PRD-0010", "sku": "DW-CAS-0010",
         "product_name": "Alo Top", "colour": "Pink", "size": "M"},
        {"product_id": "PRD-0025", "sku": "DW-CAS-0025",
         "product_name": "Alo Top", "colour": "Black", "size": "S"},
    ])

    result = filter_candidates_by_colour(candidates, None)

    assert len(result) == 2


def test_colour_with_no_candidate_match_returns_empty():
    candidates = pd.DataFrame([
        {"product_id": "PRD-0010", "sku": "DW-CAS-0010",
         "product_name": "Alo Top", "colour": "Pink", "size": "M"},
    ])

    result = filter_candidates_by_colour(candidates, "Blue")

    assert result.empty


from candidate_matching import find_description_candidates


def test_long_description_returns_all_product_name_candidates():
    project_root = Path(__file__).resolve().parent.parent
    workbook_path = (
        project_root
        / "data"
        / "dylte_wears_synthetic_automation_dataset.xlsx"
    )

    aliases = pd.read_excel(workbook_path, sheet_name="Product_Aliases")
    products = pd.read_excel(workbook_path, sheet_name="Product_Master")

    candidates = find_description_candidates(
        "Lace Trim Bra Blue 12",
        aliases,
        products,
    )

    assert not candidates.empty
    assert candidates["product_id"].is_unique
    assert candidates["product_name"].eq("Lace Trim Bra").all()


def test_unresolvable_description_returns_no_candidates():
    project_root = Path(__file__).resolve().parent.parent
    workbook_path = (
        project_root
        / "data"
        / "dylte_wears_synthetic_automation_dataset.xlsx"
    )

    aliases = pd.read_excel(workbook_path, sheet_name="Product_Aliases")
    products = pd.read_excel(workbook_path, sheet_name="Product_Master")

    candidates = find_description_candidates(
        "the usual thing",
        aliases,
        products,
    )

    assert candidates.empty
