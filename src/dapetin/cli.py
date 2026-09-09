import argparse


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
        print(
            f"Discovery adapter not configured yet: {args.keyword!r} in {args.location!r} "
            f"(limit={args.limit})"
        )
        print("Next step: connect a compliant discovery provider adapter.")
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
