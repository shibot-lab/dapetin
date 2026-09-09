from dapetin.domain.models import Business, OpportunityScore


def score_business(business: Business) -> OpportunityScore:
    """Score a business using transparent MVP signals.

    The score is intentionally heuristic. Later versions can replace or augment
    these rules with learned/AI-assisted signals while preserving explanations.
    """
    score = 0
    reasons: list[str] = []

    if business.website:
        score += 15
        reasons.append("Has a website")
    else:
        score += 25
        reasons.append("No website detected")

    if business.phone:
        score += 10
        reasons.append("Public phone number available")

    if business.email:
        score += 10
        reasons.append("Public business email available")

    if business.rating is not None:
        if business.rating >= 4.5:
            score += 10
            reasons.append("Strong public rating")
        elif business.rating < 4.0:
            score += 5
            reasons.append("Rating suggests room for improvement")

    if business.review_count is not None:
        if business.review_count >= 100:
            score += 15
            reasons.append("Established review volume")
        elif business.review_count >= 20:
            score += 8
            reasons.append("Some review traction")

    # Missing digital conversion signals are useful opportunities when we can
    # establish them from enrichment data. These are intentionally not inferred
    # from absence in the discovery payload yet.
    if business.metadata.get("whatsapp") == "true":
        score += 5
        reasons.append("WhatsApp contact signal available")

    return OpportunityScore(score=score, reasons=reasons)
