"""Opt-in, read-only MCP endpoint sharing the monitor's in-memory data."""
import json
import secrets
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from i18n import LANGUAGES
from knowledge import TOPICS, knowledge_rule

VERSIONS = ("2025-03-26", "2025-06-18", "2025-11-25")
LANGUAGE = {"type": "string", "enum": list(LANGUAGES)}
LIMIT = {"type": "integer", "minimum": 1, "maximum": 24}


def tool(name, description, required=(), **properties):
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": properties, "required": list(required),
                            "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True}}


TOOLS = [
    tool("status", "Get the last EMA Trader snapshot, positions and timestamps in UTC milliseconds."),
    tool("candles", "Get up to 24 cached 15-minute candles for the viewed or managed market.",
         symbol={"type": "string"}, limit=LIMIT),
    tool("knowledge_index", "Find relevant rule IDs. Request one language only.", language=LANGUAGE),
    tool("knowledge_rule", "Read one versioned EMA Trader topic.", ("id",), language=LANGUAGE,
         id={"type": "string", "enum": list(TOPICS)}),
]


class LocalMCP:
    def __init__(self):
        self.server = None
        self.thread = None
        self.token = None
        self.snapshot = ({}, {})

    @property
    def port(self):
        return self.server.server_port if self.server else None

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/mcp" if self.port else None

    def start(self, port, token=None):
        if self.server:
            return self.url
        if token is not None and (len(token) < 24 or not token.isascii() or not token.isalnum()):
            raise ValueError("O token MCP precisa ter pelo menos 24 letras ASCII ou dígitos.")
        self.server = HTTPServer(("127.0.0.1", port), MCPHandler)
        self.token = token or secrets.token_hex(24)
        self.server.service = self
        self.thread = Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.15}, daemon=True)
        self.thread.start()
        return self.url

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.server = self.thread = self.token = None

    def publish(self, monitor, selected):
        candles = {}
        markets = {}
        current_market = monitor.market_state if monitor.market_state_network == monitor.market_network else {}
        for symbol, (rows, point) in current_market.items():
            candles[symbol] = [asdict(row) for row in rows]
            last = rows[-1]
            preceding = rows[:-1]
            volume = sum(row.volume for row in preceding) / max(len(preceding), 1)
            markets[symbol] = {
                "closed_ms": point.time, "close": last.close, "band": point.band,
                "direction": point.side, "signal": point.action,
                "ema": [float(f"{price:.8g}") for price in (point.lower, point.upper)],
                "ema_change_22": [float(f"{change:.5g}") for change in (point.lower_change, point.upper_change)],
                "range": [min(row.low for row in rows), max(row.high for row in rows)],
                "move_pct": round((last.close / rows[0].close - 1) * 100, 3),
                "volume_ratio": round(last.volume / volume, 2) if volume else None,
            }
        snapshot = {"viewed_asset": selected, "managed_asset": (monitor.managed or {}).get("symbol"),
                    "network": monitor.account[0] if monitor.account else None,
                    "market_data_network": monitor.market_network,
                    "account_checked_ms": monitor.closed_at or None,
                    "positions": [row.copy() for row in monitor.position_rows[:12]],
                    "position_count": len(monitor.position_rows),
                    "entry_retry_pending": bool(monitor.managed and monitor.entry_retry),
                    "execution_needs_review": bool(monitor.trade_error), "markets": markets}
        self.snapshot = (snapshot, candles)

    def invoke(self, name, args):
        snapshot, candles = self.snapshot
        if name == "status":
            return snapshot or {"ready": False}
        if name == "candles":
            symbol = args.get("symbol", snapshot.get("viewed_asset"))
            return candles.get(symbol, [])[-args.get("limit", 6):]
        language = args.get("language", "en")
        return knowledge_rule(language, "index" if name == "knowledge_index" else args["id"])

    def rpc(self, message):
        method = message.get("method")
        params = message.get("params", {})
        if not isinstance(method, str) or not isinstance(params, dict):
            return {"error": {"code": -32600, "message": "Invalid request"}}
        if method == "initialize":
            version = params.get("protocolVersion")
            return {"result": {"protocolVersion": version if version in VERSIONS else VERSIONS[-1],
                               "capabilities": {"tools": {}}, "serverInfo": {"name": "EMA Trader", "version": "1"},
                               "instructions": "Read-only. Check snapshot timestamps. Use the index and one topic at a time."}}
        if method == "ping":
            return {"result": {}}
        if method == "tools/list":
            return {"result": {"tools": TOOLS}}
        if method == "tools/call":
            args = params.get("arguments", {})
            definition = next((item for item in TOOLS if item["name"] == params.get("name")), None)
            if definition and valid_args(definition["inputSchema"], args):
                value = self.invoke(definition["name"], args)
                return {"result": {"content": [{"type": "text", "text": value if isinstance(value, str)
                                               else json.dumps(value, ensure_ascii=False, separators=(",", ":"))}]}}
            return {"error": {"code": -32602, "message": "Unknown tool or invalid arguments"}}
        return {"error": {"code": -32601, "message": "Method not found"}}


def valid_args(schema, args):
    if not isinstance(args, dict) or not set(schema["required"]) <= args.keys() <= schema["properties"].keys():
        return False
    for key, value in args.items():
        constraint = schema["properties"][key]
        if constraint["type"] == "integer":
            if type(value) is not int or not constraint["minimum"] <= value <= constraint["maximum"]:
                return False
        elif not isinstance(value, str) or len(value) > 32 or ("enum" in constraint and value not in constraint["enum"]):
            return False
    return True


class MCPHandler(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(2)
        super().setup()

    def log_message(self, *_):
        pass

    def respond(self, status, message=None):
        body = json.dumps(message, ensure_ascii=False).encode() if message is not None else b""
        self.send_response(status)
        if status == 401:
            self.send_header("WWW-Authenticate", "Bearer")
        if body:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def validate(self):
        if self.path != "/mcp":
            self.respond(404)
            return False
        host = self.headers.get("Host", "")
        port = self.server.server_port
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if host not in allowed or any(origin not in {f"http://{name}" for name in allowed}
                                      for origin in self.headers.get_all("Origin", [])):
            self.respond(403)
            return False
        authorization = self.headers.get("Authorization", "").encode("utf-8")
        if not secrets.compare_digest(authorization, f"Bearer {self.server.service.token}".encode()):
            self.respond(401)
            return False
        version = self.headers.get("MCP-Protocol-Version")
        if version and version not in VERSIONS:
            self.respond(400)
            return False
        return True

    def do_GET(self):
        if self.validate():
            self.respond(405)

    do_DELETE = do_GET

    def do_POST(self):
        if not self.validate():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 32768 or self.headers.get_content_type() != "application/json":
                raise ValueError
            message = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError, TimeoutError):
            self.respond(400)
            return
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            self.respond(400)
            return
        if "id" not in message:
            self.respond(202)
            return
        result = self.server.service.rpc(message)
        self.respond(200, {"jsonrpc": "2.0", "id": message["id"], **result})
