from dapetin.domain.models import Business
from dapetin.qualification.scoring import score_business


def test_business_without_website_is_an_opportunity() -> None:
    result = score_business(
        Business(name="Contoh Kontraktor", phone="08123456789", rating=4.6, review_count=120)
    )

    assert result.score > 0
    assert "No website detected" in result.reasons
    assert "Strong public rating" in result.reasons
    assert "Established review volume" in result.reasons


def test_score_is_bounded() -> None:
    result = score_business(
        Business(
            name="Full Signal",
            website="https://example.com",
            phone="0812",
            email="hello@example.com",
            rating=5.0,
            review_count=1000,
            metadata={"whatsapp": "true"},
        )
    )

    assert 0 <= result.score <= 100
