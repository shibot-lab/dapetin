from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from dapetin.database import LeadDatabase
from dapetin.domain.models import Opportunity, PipelineStatus


def render_dashboard(opportunities: list[Opportunity], status: PipelineStatus | None = None) -> str:
    selected = status.value if status else ""
    rows = []
    for index, opportunity in enumerate(opportunities, start=1):
        business = opportunity.business
        reasons = "<br>".join(escape(reason) for reason in opportunity.score.reasons) or "-"
        status_options = "".join(
            f'<option value="{escape(option.value)}" {"selected" if option == opportunity.status else ""}>'
            f"{escape(option.value)}</option>"
            for option in PipelineStatus
        )
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td><strong>{escape(business.name)}</strong><br><small>{escape(business.category or '-')}</small></td>"
            f"<td>{escape(business.address or business.city or '-')}</td>"
            f"<td>{escape(business.website or '-')}</td>"
            f"<td>{escape(business.email or '-')}</td>"
            f"<td><strong>{opportunity.score.score}/100</strong><br><small>{reasons}</small></td>"
            f'<td><form method="post" action="/status">'
            f'<input type="hidden" name="id" value="{escape(str(index))}">'
            f'<select name="status">{status_options}</select>'
            f'<button type="submit">Save</button></form></td>'
            "</tr>"
        )

    filters = [
        '<option value="">All statuses</option>',
        *[
            f'<option value="{escape(option.value)}" {"selected" if option.value == selected else ""}>'
            f"{escape(option.value)}</option>"
            for option in PipelineStatus
        ],
    ]
    body = "".join(rows) or '<tr><td colspan="7">No leads found.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DAPETIN Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 0; background: #f6f7f9; color: #20242a; }}
main {{ max-width: 1400px; margin: 0 auto; padding: 32px 20px; }}
h1 {{ margin-bottom: 6px; }}
.card {{ background: white; border: 1px solid #ddd; border-radius: 10px; padding: 16px; margin-top: 20px; overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; min-width: 900px; }}
th, td {{ padding: 12px 10px; border-bottom: 1px solid #eee; text-align: left; vertical-align: top; }}
th {{ background: #fafafa; }}
select, button {{ padding: 7px; margin-top: 4px; }}
small {{ color: #666; }}
</style>
</head>
<body>
<main>
<h1>DAPETIN</h1>
<p>Opportunity discovery and qualification dashboard.</p>
<div class="card">
<form method="get" action="/">
<label for="status">Filter by status</label>
<select id="status" name="status">{"".join(filters)}</select>
<button type="submit">Filter</button>
</form>
</div>
<div class="card">
<table>
<thead><tr><th>#</th><th>Business</th><th>Location</th><th>Website</th><th>Email</th><th>Score / reasons</th><th>Pipeline</th></tr></thead>
<tbody>{body}</tbody>
</table>
</div>
</main>
</body>
</html>"""


def make_handler(database: LeadDatabase):
    class DashboardHandler(BaseHTTPRequestHandler):
        def _send_html(self, content: str, status_code: int = 200) -> None:
            payload = content.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/":
                self._send_html("<h1>Not found</h1>", 404)
                return
            raw_status = parse_qs(parsed.query).get("status", [""])[0]
            status = PipelineStatus(raw_status) if raw_status else None
            self._send_html(render_dashboard(database.list(status), status))

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/status":
                self._send_html("<h1>Not found</h1>", 404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8"))
            try:
                lead_id = int(form.get("id", [""])[0])
                status = PipelineStatus(form.get("status", [""])[0])
                database.update_status(lead_id, status)
            except (ValueError, KeyError):
                self._send_html("<h1>Invalid lead status update</h1>", 400)
                return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

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
