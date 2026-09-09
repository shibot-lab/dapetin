from dapetin.discovery.providers import DemoDiscoveryProvider, DiscoveryQuery
from dapetin.pipeline import run_discovery


def test_discovery_pipeline_returns_sorted_opportunities() -> None:
    run = run_discovery(
        DemoDiscoveryProvider(),
        DiscoveryQuery("kontraktor rumah", "Samarinda", limit=5),
    )

    assert len(run.opportunities) == 1
    opportunity = run.opportunities[0]
    assert opportunity.business.category == "kontraktor rumah"
    assert 0 <= opportunity.score.score <= 100
