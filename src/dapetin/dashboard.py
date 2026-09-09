from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

from dapetin.database import LeadDatabase
from dapetin.discovery.osm_provider import OpenStreetMapDiscoveryProvider
from dapetin.discovery.providers import DiscoveryQuery
from dapetin.domain.models import Opportunity, PipelineStatus
from dapetin.enrichment.website import WebsiteEnricher
from dapetin.pipeline import enrich_run, run_discovery


def render_dashboard(records: list[tuple[int, Opportunity]], status: PipelineStatus | None = None, message: str | None = None) -> str:
    selected = status.value if status else ""
    rows = []
    for index, (lead_id, opportunity) in enumerate(records, start=1):
        business = opportunity.business
        reasons = "<br>".join(escape(reason) for reason in opportunity.score.reasons) or "-"
        options = "".join(
            f'<option value="{escape(option.value)}" {"selected" if option == opportunity.status else ""}>{escape(option.value)}</option>'
            for option in PipelineStatus
        )
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td><strong>{escape(business.name)}</strong><br><small>{escape(business.category or '-')}</small></td>"
            f"<td>{escape(business.address or business.city or '-')}</td>"
            f"<td>{escape(business.phone or '-')}</td>"
            f"<td>{escape(business.website or '-')}</td>"
            f"<td>{escape(business.email or '-')}</td>"
            f"<td><strong>{opportunity.score.score}/100</strong><br><small>{reasons}</small></td>"
            f'<td><form method="post" action="/status"><input type="hidden" name="id" value="{lead_id}">'
            f'<select name="status">{options}</select><button type="submit">Save</button></form></td></tr>'
        )
    filters = ['<option value="">All statuses</option>'] + [
        f'<option value="{escape(option.value)}" {"selected" if option.value == selected else ""}>{escape(option.value)}</option>'
        for option in PipelineStatus
    ]
    body = "".join(rows) or '<tr><td colspan="8">No leads found.</td></tr>'
    notice = f'<div class="notice">{escape(message)}</div>' if message else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DAPETIN Dashboard</title><style>
body{{font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#20242a}}main{{max-width:1500px;margin:auto;padding:32px 20px}}
.card{{background:white;border:1px solid #ddd;border-radius:10px;padding:16px;margin-top:20px;overflow-x:auto}}
.discovery{{display:grid;grid-template-columns:2fr 2fr 1fr auto;gap:10px;align-items:end}}label{{display:block;font-size:14px;font-weight:600}}
input,select,button{{box-sizing:border-box;padding:9px;margin-top:5px;width:100%}}button{{cursor:pointer}}.checkbox{{display:flex;gap:8px;align-items:center;height:38px}}.checkbox input{{width:auto;margin:0}}
.notice{{margin-top:20px;padding:12px;background:#eef6ff;border:1px solid #c9def5;border-radius:8px}}table{{width:100%;border-collapse:collapse;min-width:1100px}}
th,td{{padding:12px 10px;border-bottom:1px solid #eee;text-align:left;vertical-align:top}}th{{background:#fafafa}}small,footer{{color:#666}}footer{{margin-top:20px;font-size:13px}}@media(max-width:800px){{.discovery{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>DAPETIN</h1><p>Opportunity discovery and qualification dashboard.</p>
<div class="card"><h2>Discover businesses</h2><form class="discovery" method="post" action="/discover">
<div><label for="keyword">Business keyword</label><input id="keyword" name="keyword" placeholder="e.g. kontraktor" required></div>
<div><label for="location">Location</label><input id="location" name="location" placeholder="e.g. Samarinda" required></div>
<div><label for="limit">Limit</label><input id="limit" name="limit" type="number" min="1" max="100" value="20"></div>
<div><label class="checkbox"><input name="enrich" type="checkbox"> Enrich websites</label><button type="submit">Discover</button></div></form>
<small>Discovery uses OpenStreetMap data through Overpass API.</small></div>{notice}
<div class="card"><form method="get" action="/"><label for="status">Filter by status</label><select id="status" name="status">{"".join(filters)}</select><button type="submit">Filter</button></form></div>
<div class="card"><table><thead><tr><th>#</th><th>Business</th><th>Location</th><th>Phone</th><th>Website</th><th>Email</th><th>Score / reasons</th><th>Pipeline</th></tr></thead><tbody>{body}</tbody></table></div>
<footer>Business discovery data may be sourced from OpenStreetMap contributors, available under the Open Database License (ODbL).</footer></main></body></html>"""


def make_handler(database: LeadDatabase):
    class DashboardHandler(BaseHTTPRequestHandler):
        def _send_html(self, content: str, status_code: int = 200) -> None:
            payload = content.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _redirect_home(self, message: str) -> None:
            self.send_response(303)
            self.send_header("Location", "/?" + urlencode({"message": message}))
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/":
                self._send_html("<h1>Not found</h1>", 404)
                return
            params = parse_qs(parsed.query)
            raw_status = params.get("status", [""])[0]
            try:
                status = PipelineStatus(raw_status) if raw_status else None
            except ValueError:
                self._send_html("<h1>Invalid status</h1>", 400)
                return
            self._send_html(render_dashboard(database.list_with_ids(status), status, params.get("message", [""])[0] or None))

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8"))
            if self.path == "/status":
                try:
                    database.update_status(int(form.get("id", [""])[0]), PipelineStatus(form.get("status", [""])[0]))
                except (ValueError, KeyError):
                    self._send_html("<h1>Invalid lead status update</h1>", 400)
                    return
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
                return
            if self.path == "/discover":
                keyword = form.get("keyword", [""])[0].strip()
                location = form.get("location", [""])[0].strip()
                try:
                    limit = int(form.get("limit", ["20"])[0])
                except ValueError:
                    limit = 0
                if not keyword or not location or not 1 <= limit <= 100:
                    self._send_html("<h1>Invalid discovery query</h1>", 400)
                    return
                try:
                    run = run_discovery(OpenStreetMapDiscoveryProvider(), DiscoveryQuery(keyword, location, limit))
                    if "enrich" in form and run.opportunities:
                        enrich_run(run, WebsiteEnricher())
                    for opportunity in run.opportunities:
                        database.save(opportunity)
                    message = f"Discovery completed: {len(run.opportunities)} businesses found for {keyword!r} in {location!r}."
                except Exception as exc:
                    message = f"Discovery failed: {exc}"
                self._redirect_home(message)
                return
            self._send_html("<h1>Not found</h1>", 404)

        def log_message(self, format: str, *args) -> None:
            return
    return DashboardHandler


def serve_dashboard(db_path: str = "dapetin.db", host: str = "127.0.0.1", port: int = 8000) -> None:
    database = LeadDatabase(db_path)
    server = HTTPServer((host, port), make_handler(database))
    print(f"DAPETIN dashboard running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
