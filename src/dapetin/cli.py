import argparse

from dapetin.database import LeadDatabase
from dapetin.dashboard import serve_dashboard
from dapetin.discovery.file_provider import CsvDiscoveryProvider
from dapetin.discovery.providers import DemoDiscoveryProvider, DiscoveryQuery
from dapetin.domain.models import PipelineStatus
from dapetin.enrichment.website import WebsiteEnricher
from dapetin.pipeline import enrich_run, run_discovery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dapetin",
        description="Discover and qualify business opportunities.",
    )
    parser.add_argument("--version", action="version", version="DAPETIN 0.3.0")
    subparsers = parser.add_subparsers(dest="command")

    discover = subparsers.add_parser("discover", help="Run business discovery")
    discover.add_argument("keyword", help="Business keyword, e.g. kontraktor")
    discover.add_argument("location", help="Target location, e.g. Samarinda")
    discover.add_argument("--limit", type=int, default=20)
    discover.add_argument("--csv", dest="csv_path", help="Use a compliant CSV export as the discovery source")
    discover.add_argument("--enrich", action="store_true", help="Enrich public website signals")
    discover.add_argument("--db", default="dapetin.db", help="SQLite database path")

    leads = subparsers.add_parser("leads", help="Manage saved leads")
    leads.add_argument("--db", default="dapetin.db", help="SQLite database path")
    leads.add_argument("--status", choices=[status.value for status in PipelineStatus])
    leads.add_argument("--set-status", nargs=2, metavar=("ID", "STATUS"), help="Update a lead status")

    dashboard = subparsers.add_parser("dashboard", help="Run the local web dashboard")
    dashboard.add_argument("--db", default="dapetin.db", help="SQLite database path")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8000)

    return parser


def _print_opportunities(opportunities) -> None:
    for index, opportunity in enumerate(opportunities, start=1):
        business = opportunity.business
        print(f"\n{index}. {business.name}")
        print(f"   category: {business.category or '-'}")
        print(f"   location: {business.address or '-'}")
        print(f"   phone: {business.phone or '-'}")
        print(f"   website: {business.website or '-'}")
        print(f"   email: {business.email or '-'}")
        print(f"   score: {opportunity.score.score}/100")
        print(f"   status: {opportunity.status.value}")
        for reason in opportunity.score.reasons:
            print(f"   - {reason}")


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "discover":
        query = DiscoveryQuery(args.keyword, args.location, args.limit)
        provider = CsvDiscoveryProvider(args.csv_path) if args.csv_path else DemoDiscoveryProvider()
        run = run_discovery(provider, query)
        if args.enrich:
            enrich_run(run, WebsiteEnricher())

        database = LeadDatabase(args.db)
        for opportunity in run.opportunities:
            database.save(opportunity)

        print(f"DAPETIN discovery: {args.keyword!r} in {args.location!r}")
        _print_opportunities(run.opportunities)
    elif args.command == "leads":
        database = LeadDatabase(args.db)
        if args.set_status:
            lead_id, raw_status = args.set_status
            database.update_status(int(lead_id), PipelineStatus(raw_status))
            print(f"Lead {lead_id} status updated to {raw_status}")
        else:
            status = PipelineStatus(args.status) if args.status else None
            _print_opportunities(database.list(status))
    elif args.command == "dashboard":
        serve_dashboard(args.db, args.host, args.port)
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
