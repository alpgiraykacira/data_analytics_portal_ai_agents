import unicodedata
from difflib import get_close_matches
import json
from langchain.tools import tool

@tool
def resolve_province_id(province_name: str, cutoff: float = 0.6) -> int:
    """
    Resolve the province ID based on the provided province name using normalization,
    alias check, and fuzzy matching techniques.

    This function takes a province name and attempts to normalize the input for
    comparison with a predefined list of provinces. It handles special cases, including
    aliases for Istanbul's European and Asian sides, and uses fuzzy string matching
    to find the best possible match. It returns the numeric ID corresponding to
    the resolved province name or raises an error if an ambiguous name or no match
    is found.

    Parameters:
        province_name (str): The name of the province to resolve. This should be a string
            representing a Turkish province, which can include aliases or case-insensitivity.
        cutoff (float, optional): The threshold for fuzzy matching. A value between 0 and 1
            indicating the similarity required to consider a match. Default is 0.6.

    Returns:
        int: The ID of the province corresponding to the resolved name.

    Raises:
        ValueError: Raised if the input is ambiguous for Istanbul's European or Asian sides
            or if no matching province is found based on the provided name.
    """
    def normalize(text: str) -> str:
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').upper().strip()

    with open("data/province_list.json", "r") as f:
        province_list = json.load(f)

    # Define aliases
    istanbul_aliases = {
        "ISTANBUL AVURPA": "İSTANBUL-AVRUPA",
        "EUROPEAN ISTANBUL": "İSTANBUL-AVRUPA",
        "ISTANBUL ASYA": "İSTANBUL-ASYA",
        "ASIAN ISTANBUL": "İSTANBUL-ASYA",
        "ISTANBUL": ["İSTANBUL-AVRUPA", "İSTANBUL-ASYA"]
    }

    query = normalize(province_name)

    # Check aliases
    for alias, target in istanbul_aliases.items():
        if query == normalize(alias):
            if isinstance(target, list):
                raise ValueError("Ambiguous province name: 'Istanbul' — please specify ASYA or AVRUPA.")
            for p in province_list:
                if normalize(p["name"]) == normalize(target):
                    return p["id"]

    # Fuzzy match full names
    name_map = {normalize(p["name"]): p["id"] for p in province_list}
    close_matches = get_close_matches(query, name_map.keys(), n=1, cutoff=cutoff)

    if not close_matches:
        raise ValueError(f"No match found for '{province_name}'.")

    return name_map[close_matches[0]]