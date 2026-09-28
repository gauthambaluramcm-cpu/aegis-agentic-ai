def assess_access_risk(access_count: int) -> str:
    """
    Assess a user's access risk based on the number of records accessed.
    """

    if access_count <= 100:
        return "LOW"

    elif access_count <= 500:
        return "MEDIUM"

    else:
        return "HIGH"