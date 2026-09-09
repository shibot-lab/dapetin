import argparse

from dapetin.discovery.providers import DemoDiscoveryProvider, DiscoveryQuery
from dapetin.pipeline import run_discovery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dapetin",
        description="Discover and qualify business opportunities.",
    )
    parser.add_argument("--version", action="version", version="DAPETIN 0.1.0")
    subparsers = parser.add_subparsers(dest="command")

    discover = subparsers.add_parser("discover", help="Run business discovery")
    discover.add_argument("keyword", help="Business keyword, e.g. kontraktor")
    discover.add_argument("location", help="Target location, e.g. Samarinda")
    discover.add_argument("--limit", type=int, default=20)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "discover":
        query = DiscoveryQuery(args.keyword, args.location, args.limit)
        run = run_discovery(DemoDiscoveryProvider(), query)
        print(f"DAPETIN discovery: {args.keyword!r} in {args.location!r}")
        for index, opportunity in enumerate(run.opportunities, start=1):
            business = opportunity.business
            print(f"\n{index}. {business.name}")
            print(f"   category: {business.category or '-'}")
            print(f"   location: {business.address or '-'}")
            print(f"   phone: {business.phone or '-'}")
            print(f"   website: {business.website or '-'}")
            print(f"   score: {opportunity.score.score}/100")
            for reason in opportunity.score.reasons:
                print(f"   - {reason}")
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
