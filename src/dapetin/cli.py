import argparse
import os

from dapetin.analysis import OpenAIOpportunityAnalysisProvider
from dapetin.database import LeadDatabase
from dapetin.dashboard import serve_dashboard
from dapetin.discovery.file_provider import CsvDiscoveryProvider
from dapetin.discovery.providers import DemoDiscoveryProvider, DiscoveryQuery
from dapetin.domain.models import PipelineStatus
from dapetin.enrichment.website import WebsiteEnricher
from dapetin.outreach import SmtpOutreachProvider, send_targeted_outreach
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

    analyze = subparsers.add_parser("analyze", help="Analyze a saved opportunity with AI")
    analyze.add_argument("lead_id", type=int)
    analyze.add_argument("--db", default="dapetin.db", help="SQLite database path")
    analyze.add_argument("--model", help="AI model name")

    dashboard = subparsers.add_parser("dashboard", help="Run the local web dashboard")
    dashboard.add_argument("--db", default="dapetin.db", help="SQLite database path")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8000)

    outreach = subparsers.add_parser("outreach", help="Send one targeted outreach email")
    outreach.add_argument("lead_id", type=int)
    outreach.add_argument("subject")
    outreach.add_argument("body")
    outreach.add_argument("--db", default="dapetin.db", help="SQLite database path")
    outreach.add_argument("--cooldown-hours", type=int, default=24)

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
    elif args.command == "analyze":
        database = LeadDatabase(args.db)
        records = {lead_id: opportunity for lead_id, opportunity in database.list_with_ids()}
        opportunity = records.get(args.lead_id)
        if opportunity is None:
            raise SystemExit(f"Lead {args.lead_id} not found")
        analysis = OpenAIOpportunityAnalysisProvider(model=args.model).analyze(opportunity)
        print(f"Summary: {analysis.summary}")
        print("Strengths:")
        for item in analysis.strengths:
            print(f"- {item}")
        print("Risks:")
        for item in analysis.risks:
            print(f"- {item}")
        print(f"Next step: {analysis.next_step}")
    elif args.command == "dashboard":
        serve_dashboard(args.db, args.host, args.port)
    elif args.command == "outreach":
        database = LeadDatabase(args.db)
        records = {lead_id: opportunity for lead_id, opportunity in database.list_with_ids()}
        opportunity = records.get(args.lead_id)
        if opportunity is None:
            raise SystemExit(f"Lead {args.lead_id} not found")
        required = ("DAPETIN_SMTP_HOST", "DAPETIN_SMTP_PORT", "DAPETIN_SMTP_USERNAME", "DAPETIN_SMTP_PASSWORD", "DAPETIN_SMTP_SENDER")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise SystemExit(f"Missing SMTP configuration: {', '.join(missing)}")
        provider = SmtpOutreachProvider(
            os.environ["DAPETIN_SMTP_HOST"],
            int(os.environ["DAPETIN_SMTP_PORT"]),
            os.environ["DAPETIN_SMTP_USERNAME"],
            os.environ["DAPETIN_SMTP_PASSWORD"],
            os.environ["DAPETIN_SMTP_SENDER"],
        )
        send_targeted_outreach(
            opportunity,
            provider,
            args.subject,
            args.body,
            cooldown_hours=args.cooldown_hours,
        )
        database.update_status(args.lead_id, PipelineStatus.CONTACTED)
        print(f"Targeted outreach sent to {opportunity.business.email}")
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
