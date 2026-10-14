
import pandas as pd


def normalize_text(value):
    """Normalize text for case-insensitive exact comparison."""
    if pd.isna(value):
        return ""

    return " ".join(str(value).strip().casefold().split())

def filter_candidates_by_colour(candidates, colour):
    """
    Narrow candidates using a recorded colour.

    If colour is missing, retain all candidates.
    If no candidate has that colour, return no candidates.
    """
    normalized_colour = normalize_text(colour)

    if not normalized_colour:
        return candidates.copy()

    candidate_colours = candidates["colour"].map(normalize_text)

    return candidates.loc[
        candidate_colours == normalized_colour
    ].copy().reset_index(drop=True)

def find_alias_candidates(description, aliases, products):
    """
    Return every distinct product linked to an exact alias.

    This generates candidates; it does not approve a match.
    """
    normalized_description = normalize_text(description)

    if not normalized_description:
        return products.iloc[0:0].copy()

    normalized_aliases = aliases["alias_text"].map(normalize_text)

    matching_product_ids = aliases.loc[
        normalized_aliases == normalized_description,
        "product_id",
    ].drop_duplicates()

    candidates = products[
        products["product_id"].isin(matching_product_ids)
    ].copy()

    return candidates.reset_index(drop=True)


def find_description_candidates(description, aliases, products):
    """
    Find products whose alias appears as a phrase inside a description.

    Returns all distinct product candidates. Does not approve a match.
    """
    normalized_description = normalize_text(description)

    if not normalized_description:
        return products.iloc[0:0].copy()

    normalized_aliases = aliases["alias_text"].map(normalize_text)

    matching_product_ids = aliases.loc[
        normalized_aliases.apply(
            lambda alias: bool(alias) and alias in normalized_description
        ),
        "product_id",
    ].drop_duplicates()

    candidates = products[
        products["product_id"].isin(matching_product_ids)
    ].copy()

    return candidates.reset_index(drop=True)
