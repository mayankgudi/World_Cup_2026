from third_place_lookup import THIRD_PLACE_LOOKUP


def team_from_slot(slot, group_results):
    """
    Converts a slot like '1A', '2F', or '3E' into the actual team name.
    """
    place = slot[0]
    group = slot[1]

    if place == "1":
        return group_results[group]["first"]
    if place == "2":
        return group_results[group]["second"]
    if place == "3":
        return group_results[group]["third"]

    raise ValueError(f"Invalid slot: {slot}")


def get_third_place_key(third_place_ranking):
    """
    Takes the user's ranked third-place groups and returns the lookup key.

    Example:
    ['A', 'D', 'F', 'J', 'B', 'H', 'K', 'E', 'C', 'G', 'I', 'L']

    Top 8:
    ['A', 'D', 'F', 'J', 'B', 'H', 'K', 'E']

    Sorted key:
    'A,B,D,E,F,H,J,K'
    """
    top_8 = third_place_ranking[:8]
    return ",".join(sorted(top_8))


def generate_round_of_32(group_results, third_place_ranking):
    third_key = get_third_place_key(third_place_ranking)

    if third_key not in THIRD_PLACE_LOOKUP:
        raise ValueError(
            f"No third-place matchup table found for combination: {third_key}. "
            "Add this combination to THIRD_PLACE_LOOKUP."
        )

    third_assignments = THIRD_PLACE_LOOKUP[third_key]

    bracket_slots = [
        ("Match 1", "1E", third_assignments["1E"]),
        ("Match 2", "1I", third_assignments["1I"]),
        ("Match 3", "2A", "2B"),
        ("Match 4", "1F", "2C"),

        ("Match 5", "2K", "2L"),
        ("Match 6", "1H", "2J"),
        ("Match 7", "1D", third_assignments["1D"]),
        ("Match 8", "1G", third_assignments["1G"]),

        ("Match 9", "1C", "2F"),
        ("Match 10", "2E", "2I"),
        ("Match 11", "1A", third_assignments["1A"]),
        ("Match 12", "1L", third_assignments["1L"]),

        ("Match 13", "1J", "2H"),
        ("Match 14", "2D", "2G"),
        ("Match 15", "1B", third_assignments["1B"]),
        ("Match 16", "1K", third_assignments["1K"]),
    ]

    bracket = []

    for match_name, slot_1, slot_2 in bracket_slots:
        bracket.append({
            "match": match_name,
            "team_1": team_from_slot(slot_1, group_results),
            "team_2": team_from_slot(slot_2, group_results),
            "slot_1": slot_1,
            "slot_2": slot_2,
        })

    return bracket