"""EMA Trader entry point. The CLI and desktop share the same monitor."""

import argparse
import getpass
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import broker
import dashboard
from engine import Monitor, NORMAL_REFRESH, RETRY, markets, symbol_key
from i18n import LANGUAGES, tr, translate_error
from knowledge import knowledge_rule
from local_mcp import LocalMCP
from storage import data_root, read, write
from vault import METADATA, Vault, VaultError

SIGNAL_ACTIONS = {"AL": "Abrir long", "FL": "Fechar long", "AS": "Abrir short", "FS": "Fechar short"}


def price_text(value):
    return f"{value:,.2f}" if value >= 1 else f"{value:.5g}"


def compact_usd(value):
    for scale, unit in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if value >= scale:
            return f"US$ {value / scale:.1f}{unit}"
    return f"US$ {value:,.0f}"


def label(side, language):
    return "Long" if side > 0 else "Short" if side < 0 else tr(language, "Zerado")


def credentials(symbol, network, account, key, key_index, margin, leverage, drawdown=Decimal("25")):
    symbol_key(symbol)
    if account < 0 or not 0 <= key_index <= 254 or not key or not 1 <= leverage <= 20 or not 0 < margin <= 1_000_000:
        raise ValueError("Confira a conta, chave, margem e alavancagem.")
    if not drawdown.is_finite() or not 0 <= drawdown < 100:
        raise ValueError("Limite de perda da conta inválido.")
    return {"symbol": symbol, "network": network, "account": account, "key": key, "key_index": key_index,
            "margin": str(margin), "leverage": leverage, "compound": True, "drawdown": str(drawdown) if drawdown else None}


def cli(args):
    monitor = Monitor()
    mcp = LocalMCP()
    if args.mcp_port is not None:
        token = os.environ.get("EMA_TRADER_MCP_TOKEN")
        if not token:
            raise ValueError("Defina EMA_TRADER_MCP_TOKEN para habilitar o MCP no terminal.")
        if not 1 <= args.mcp_port <= 65535:
            raise ValueError("Porta inválida.")
        print(mcp.start(args.mcp_port, token), file=sys.stderr)
    try:
        run_cli(args, monitor, mcp)
    finally:
        mcp.stop()


def terminal_vault(language):
    root = data_root()
    passphrase = os.environ.get("EMA_TRADER_VAULT_PASSPHRASE")
    if passphrase is None:
        if not sys.stdin.isatty():
            raise VaultError("Abra um terminal interativo ou defina EMA_TRADER_VAULT_PASSPHRASE.")
        passphrase = getpass.getpass(tr(language, "Frase secreta do cofre") + " ")
        if not (root / METADATA).exists():
            confirm = getpass.getpass(tr(language, "Repita a frase secreta") + " ")
            if passphrase != confirm:
                raise VaultError("As frases secretas não coincidem.")
    return Vault.open(root, passphrase)


def run_cli(args, monitor, mcp):
    language = args.lang or "pt"
    if args.account is not None:
        monitor.account = args.network, args.account
    if args.trade:
        if args.account is None or (args.network == "mainnet" and not args.confirm_mainnet):
            raise ValueError("Informe --account; para ordens reais, também --confirm-mainnet.")
        vault = terminal_vault(language)
        path = vault.root / "profiles" / (symbol_key(args.profile.upper()) + ".json")
        saved = vault.read(path, {})
        identity = {"network": args.network, "account": args.account, "key_index": args.key_index}
        key = os.environ.get("LIGHTER_API_KEY")
        if not key and all(saved.get(field) == value for field, value in identity.items()):
            key = saved.get("key")
        if not key and args.save_key and sys.stdin.isatty():
            key = getpass.getpass(tr(language, "Chave privada") + " ")
        config = credentials(args.symbol, args.network, args.account, key, args.key_index,
                             args.margin, args.leverage, args.drawdown)
        def save():
            vault.write(path, dict(saved, **identity, key=key))
        config["vault"] = vault
        if broker.saved_close(config):
            monitor.recovery = config
        else:
            monitor.arm(config, on_ready=save if args.save_key else None)
    while True:
        candles, points, orders, errors = monitor.snapshot(args.symbol)
        if mcp.port:
            mcp.publish(monitor, args.symbol)
        if points:
            print(args.symbol, points[-1].action or label(points[-1].side, language), candles[-1].close, flush=True)
        for row in monitor.position_rows:
            detail = tr(language, "Quantidade {quantity} · entrada {price}",
                        quantity=row["position"], price=row["avg_entry_price"])
            print(f'{row["symbol"]} · {label(int(row["sign"]), language)} · {detail} · P&L {row["unrealized_pnl"]}', flush=True)
        for order in orders:
            print(f'{tr(language, order["action"])}: {order["filled"]}', flush=True)
            if args.beep and Decimal(order["filled"]) > 0:
                print("\a", end="", flush=True)
        if monitor.trade_error:
            print(translate_error(language, monitor.trade_error), file=sys.stderr)
        elif monitor.managed and monitor.entry_retry:
            print(tr(language, "Abertura cancelada por desvio de preço. Aguardando nova tentativa."), file=sys.stderr)
        if errors:
            print(" | ".join(translate_error(language, error) for error in errors), file=sys.stderr)
        if args.once:
            break
        time.sleep(RETRY if errors or monitor.recovery_pending else max(2, NORMAL_REFRESH - time.time() % NORMAL_REFRESH + 2))


def gui(profile="DEFAULT", language=None):
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
    import webbrowser

    profile = symbol_key(profile.upper())
    root_path = data_root()
    preferences_path = root_path / "ui-profiles" / (profile + ".json")
    private_path = root_path / "profiles" / (profile + ".json")
    root = tk.Tk()
    root.title("EMA Trader")
    root.geometry("1152x648")
    root.minsize(740, 520)
    background, panel, chart = "#0b111c", "#151e2e", "#101723"
    foreground, muted = "#f1f5fc", "#a8b7cc"
    long_color, short_color = "#56e3b4", "#ff899b"
    root.configure(background=background)
    icon = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets" / "icon.png"
    if icon.is_file():
        root.iconphoto(True, tk.PhotoImage(file=icon))
    monitor = Monitor()
    mcp = LocalMCP()
    worker = ThreadPoolExecutor(max_workers=1)
    public_worker = ThreadPoolExecutor(max_workers=2)
    prefs = read(preferences_path, {})
    requested_language = language
    language = requested_language or prefs.get("language", "pt")
    vault = None
    private = {}

    def t(message, **values):
        return tr(language, message, **values)

    def unlock(parent, interactive=True):
        nonlocal vault, private
        if vault is not None:
            return True
        try:
            secret = os.environ.get("EMA_TRADER_VAULT_PASSPHRASE")
            if secret is None:
                if not interactive:
                    return False
                secret = simpledialog.askstring(t("Cofre local"), t("Frase secreta do cofre"), show="*", parent=parent)
                if secret is None:
                    return False
                if not (root_path / METADATA).exists():
                    confirm = simpledialog.askstring(t("Cofre local"), t("Repita a frase secreta"), show="*", parent=parent)
                    if confirm is None:
                        return False
                    if confirm != secret:
                        raise VaultError("As frases secretas não coincidem.")
            candidate = Vault.open(root_path, secret)
            private = candidate.read(private_path, {})
            if private.get("recover_close") and private.get("key"):
                config = credentials(private["symbol"], private["network"], private["account"],
                                     private["key"], private["key_index"], Decimal(private["margin"]),
                                     private["leverage"], Decimal(private.get("drawdown") or "0"))
                config["vault"] = candidate
                if broker.saved_close(config):
                    monitor.recovery = config
            vault = candidate
            return True
        except (OSError, ValueError) as error:
            messagebox.showerror(t("Cofre local"), translate_error(language, error), parent=parent)
            return False

    unlock(root, interactive=(root_path / METADATA).exists() or private_path.exists())
    for field in ("symbol", "beep", "language", "mcp_port"):
        if field in private:
            prefs.setdefault(field, private[field])
    language = requested_language or prefs.get("language", "pt")
    localized = []

    def localize(widget, message):
        localized.append((widget, message))
        widget.configure(text=t(message))
        return widget
    if "account" in private:
        monitor.account = private["network"], private["account"]
    selected = tk.StringVar(value=prefs.get("symbol", "BTC"))
    beep = tk.BooleanVar(value=prefs.get("beep", True))
    banner = tk.StringVar()
    signal_title = tk.StringVar()
    signal_detail = tk.StringVar()
    status = tk.StringVar()
    position = tk.StringVar(value=t("Conta não configurada"))
    detail = tk.StringVar()
    refresh_timer = None
    busy = False
    browse_until = 0
    last_chart = None
    last_view = None
    last_network = None
    assets = ("BTC",)
    market_view = None
    stories = []
    context_future = news_future = None

    def dashboard_label(parent, *, bg=background, fg=foreground, **options):
        return tk.Label(parent, bg=bg, fg=fg, **options)

    toolbar = tk.Frame(root, bg=background, padx=18, pady=12)
    toolbar.pack(fill="x")
    dashboard_label(toolbar, text="EMA Trader", fg=long_color, font=("TkDefaultFont", 18, "bold")).pack(side="left", padx=(0, 18))
    localize(dashboard_label(toolbar, fg=muted), "Buscar ativo").pack(side="left")
    search = tk.StringVar()
    search_field = ttk.Entry(toolbar, textvariable=search, width=9)
    search_field.pack(side="left", padx=(4, 0))
    choice = ttk.Combobox(toolbar, textvariable=selected, state="readonly", width=12, values=("BTC",))
    choice.pack(side="left", padx=4)

    def filter_assets(*_):
        query = search.get().strip().upper()
        matches = sorted((symbol for symbol in assets if query in symbol),
                         key=lambda symbol: (symbol != query, not symbol.startswith(query), symbol))
        choice.configure(values=matches)
        return matches

    def select_match(_):
        if not busy and (matches := filter_assets()):
            selected.set(matches[0])
            change(None)

    search.trace_add("write", filter_assets)
    search_field.bind("<Return>", select_match)
    refresh_button = localize(ttk.Button(toolbar, command=lambda: refresh()), "Atualizar")
    refresh_button.pack(side="left", padx=4)
    settings_button = localize(ttk.Button(toolbar, command=lambda: settings()), "Configurações")
    settings_button.pack(side="left", padx=4)
    localize(ttk.Button(toolbar, command=lambda: show_subaccounts()), "Subcontas").pack(side="right")
    body = tk.Frame(root, bg=background, padx=18)
    body.pack(fill="both", expand=True)
    market_strip = tk.Frame(body, bg=panel, padx=12, pady=6)
    market_strip.pack(fill="x", pady=(0, 8))
    localize(dashboard_label(market_strip, bg=panel, fg=muted, text="", font=("TkDefaultFont", 9, "bold")),
             "Mercado · 24h").pack(side="left", padx=(0, 10))
    tickers = [dashboard_label(market_strip, bg=panel, anchor="w") for _ in range(4)]
    for ticker in tickers:
        ticker.pack(side="left", fill="x", expand=True)
    signal_panel = tk.Frame(body, bg=panel, padx=16, pady=9)
    signal_panel.pack(fill="x", pady=(0, 12))
    localize(dashboard_label(signal_panel, bg=panel, fg=muted, font=("TkDefaultFont", 10, "bold")),
             "Sinal da EMA · 15 min").pack(anchor="w")
    action_label = dashboard_label(signal_panel, bg=panel, textvariable=signal_title,
                                   font=("TkDefaultFont", 22, "bold"), anchor="w", justify="left")
    action_label.pack(anchor="w", fill="x", pady=(2, 1))
    action_label.bind("<Configure>", lambda event: action_label.configure(wraplength=max(1, event.width)))
    dashboard_label(signal_panel, bg=panel, fg=muted, textvariable=signal_detail).pack(anchor="w")
    card = tk.Frame(body, bg=panel, padx=15, pady=12)
    card.pack(side="right", fill="y", padx=(12, 0))
    localize(dashboard_label(card, bg=panel, fg=muted, font=("TkDefaultFont", 10, "bold")),
             "Posição real · Lighter").pack(anchor="w")
    dashboard_label(card, bg=panel, textvariable=position, width=23, wraplength=240, anchor="w",
                    justify="left", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(8, 0))
    dashboard_label(card, bg=panel, fg=muted, textvariable=detail, wraplength=240,
                    justify="left").pack(anchor="w", pady=(0, 4))
    ttk.Separator(card).pack(fill="x", pady=8)
    localize(dashboard_label(card, bg=panel, fg=muted, font=("TkDefaultFont", 10, "bold")),
             "Livro de ofertas e volume").pack(anchor="w")
    book_label = dashboard_label(card, bg=panel, width=32, anchor="w", justify="left", wraplength=240)
    book_label.pack(anchor="w", pady=(4, 0))
    depth_bar = tk.Canvas(card, width=230, height=5, bg=chart, borderwidth=0, highlightthickness=0)
    depth_bar.pack(anchor="w", pady=6)
    ttk.Separator(card).pack(fill="x", pady=(3, 7))
    localize(dashboard_label(card, bg=panel, fg=muted, font=("TkDefaultFont", 10, "bold")),
             "Notícias de mercado").pack(anchor="w")
    news_rows = [dashboard_label(card, bg=panel, wraplength=230, justify="left", anchor="w") for _ in range(2)]
    for row in news_rows:
        row.pack(anchor="w", pady=(5, 0))
    main = tk.Frame(body, bg=background)
    main.pack(side="left", fill="both", expand=True)
    dashboard_label(main, textvariable=banner, font=("TkDefaultFont", 15, "bold")).pack(anchor="w", pady=(3, 8))
    canvas = tk.Canvas(main, bg=chart, borderwidth=0, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    localize(dashboard_label(main, fg=muted), "AL abre long · FL fecha long · AS abre short · FS fecha short").pack(anchor="w", pady=(7, 0))
    status_label = dashboard_label(root, fg=muted, textvariable=status, anchor="w", justify="left", padx=18, pady=8)
    status_label.pack(fill="x")
    status_label.bind("<Configure>", lambda event: status_label.configure(wraplength=max(1, event.width - 36)))

    def draw():
        canvas.delete("all")
        if not last_chart:
            return
        candles, points = last_chart
        values = {point.time: point for point in points}
        candles = candles[-46:]
        lo = min(min(c.low, values[c.time].lower) if c.time in values else c.low for c in candles)
        hi = max(max(c.high, values[c.time].upper) if c.time in values else c.high for c in candles)
        width, height = max(1, canvas.winfo_width()), max(1, canvas.winfo_height())
        if width <= 106 or height <= 70:
            return
        plot_right = width - 83
        stride = (plot_right - 18) / len(candles)

        def y(value):
            return 27 + (hi - value) / max(hi - lo, 1e-12) * (height - 66)

        for step in range(5):
            level = hi - (hi - lo) * step / 4
            line_y = y(level)
            canvas.create_line(10, line_y, plot_right, line_y, fill="#202b3d")
            canvas.create_text(plot_right + 7, line_y, text=price_text(level), anchor="w", fill=muted)
        canvas.create_line(10, y(candles[-1].close), plot_right, y(candles[-1].close), fill="#8199b4", dash=(3, 4))
        for i, anchor in ((0, "w"), (len(candles) // 2, "center"), (len(candles) - 1, "e")):
            stamp = time.strftime("%H:%M", time.localtime(candles[i].time / 1000))
            canvas.create_text(18 + (i + .5) * stride, height - 9, text=stamp, anchor=anchor, fill=muted)

        last = None
        for i, c in enumerate(candles):
            x = 18 + (i + .5) * stride
            point = values.get(c.time)
            if point and last:
                tone = {1: "#174637", -1: "#592f3a", 0: "#333e51"}[point.band]
                canvas.create_polygon(x-stride, y(last.upper), x, y(point.upper),
                                      x, y(point.lower), x-stride, y(last.lower), fill=tone)
            last = point
        for i, c in enumerate(candles):
            x = 18 + (i + .5) * stride
            point = values.get(c.time)
            shade = long_color if c.close >= c.open else short_color
            canvas.create_line(x, y(c.high), x, y(c.low), fill=shade)
            top = min(y(c.open), y(c.close))
            canvas.create_rectangle(x-stride*.24, top, x+stride*.24, max(top+2, y(min(c.open,c.close))),
                                    fill=shade, outline="")
            if point and point.action:
                tip = y(c.low) + 3 if point.side > 0 else y(c.high) - 3
                base = tip + 7 * point.side
                color = long_color if point.side > 0 else short_color
                canvas.create_polygon(x, tip, x - 4, base, x + 4, base, fill=color)
                marker = canvas.create_text(max(30, x), base + 9 * point.side, text=point.action, fill=color,
                                            font=("TkDefaultFont", 8, "bold"))
                x1, y1, x2, y2 = canvas.bbox(marker)
                pill = canvas.create_rectangle(x1 - 3, y1 - 1, x2 + 3, y2 + 1, fill=chart, outline="")
                canvas.tag_lower(pill, marker)

    def submit(task, on_finish, on_error=None):
        nonlocal busy
        if busy:
            return
        busy = True
        for control in (choice, refresh_button, settings_button):
            control.configure(state="disabled")
        future = worker.submit(task)

        def await_result():
            nonlocal busy
            if not future.done():
                root.after(70, await_result)
                return
            busy = False
            choice.configure(state="readonly")
            for control in (refresh_button, settings_button):
                control.configure(state="normal")
            try:
                on_finish(future.result())
            except Exception as error:
                status.set(translate_error(language, error))
                if on_error:
                    on_error()

        root.after(70, await_result)

    def refresh():
        nonlocal refresh_timer
        if refresh_timer:
            root.after_cancel(refresh_timer)
            refresh_timer = None
        if busy:
            schedule(2)
            return
        symbol = selected.get()
        refresh_context(symbol, monitor.market_network)

        def update():
            network = monitor.market_network
            result = monitor.snapshot(symbol)
            if mcp.port:
                mcp.publish(monitor, symbol)
            return result, sorted(set(markets(network)) | {symbol}), network

        def show(result):
            nonlocal last_view, last_chart, last_network, assets
            (candles, points, orders, errors), catalog, network = result
            if network != last_network:
                last_chart = None
                last_network = network
                draw()
            assets = catalog
            filter_assets()
            last_view = symbol, candles, points, errors
            render()
            if beep.get():
                actions = {r["action"] for r in orders if Decimal(r["filled"]) > 0 and not r.get("partial")}
                for i in range(len(actions)):
                    root.after(i * 400, root.bell)
            if monitor.managed and symbol != monitor.managed["symbol"] and time.time() >= browse_until and any(
                    r["symbol"] == monitor.managed["symbol"] for r in monitor.position_rows):
                selected.set(monitor.managed["symbol"])
                schedule(1)
            else:
                schedule(RETRY if errors or monitor.recovery_pending else max(2, NORMAL_REFRESH - time.time() % NORMAL_REFRESH + 2))

        submit(update, show, lambda: schedule(RETRY))

    def refresh_context(symbol, network):
        nonlocal context_future, news_future

        def finish_market():
            nonlocal market_view, context_future
            if not context_future.done():
                root.after(150, finish_market)
                return
            try:
                quotes, book = context_future.result()
                if selected.get() == symbol and monitor.market_network == network:
                    market_view = network, symbol, quotes, book
            except (OSError, ValueError, KeyError):
                if selected.get() == symbol and monitor.market_network == network:
                    market_view = network, symbol, {}, None
            finally:
                context_future = None
            render_context()
            if selected.get() != symbol or monitor.market_network != network:
                refresh_context(selected.get(), monitor.market_network)

        def finish_news():
            nonlocal stories, news_future
            if not news_future.done():
                root.after(150, finish_news)
                return
            try:
                stories = news_future.result()
            finally:
                news_future = None
            render_context()

        if context_future is None:
            context_future = public_worker.submit(dashboard.market_context, network, symbol)
            root.after(150, finish_market)
        if news_future is None:
            news_future = public_worker.submit(dashboard.headlines)
            root.after(150, finish_news)

    def render_context():
        symbol = selected.get()
        quotes, book = {}, None
        if market_view and market_view[0] == monitor.market_network:
            _, market_symbol, quotes, book = market_view
            if market_symbol != symbol:
                book = None
        gold = next((name for name in ("XAU", "GOLD", "XAUT", "PAXG") if name in quotes), "XAU")
        for ticker, name in zip(tickers, ("BTC", "ETH", "SOL", gold)):
            if name in quotes:
                value, change, _ = quotes[name]
                ticker.configure(text=f"{name}   {price_text(value)}   {change:+.2f}%",
                                 fg=long_color if change >= 0 else short_color)
            else:
                ticker.configure(text=f"{name}   —", fg=muted)
        volume = compact_usd(quotes[symbol][2]) if symbol in quotes else "—"
        lines = [t("{symbol} · Volume 24h {volume}", symbol=symbol, volume=volume)]
        depth_bar.delete("all")
        if book and time.time() - book[3] <= 2 * NORMAL_REFRESH:
            spread, bids, asks, observed = book
            lines.append(t("Spread {spread} pb · {time}", spread=f"{spread:.2f}", time=time.strftime("%H:%M", time.localtime(observed))))
            lines.append(t("Compras {bids} · Vendas {asks}", bids=compact_usd(bids), asks=compact_usd(asks)))
            lines.append(t("Ofertas até 0,25% do preço médio"))
            if bids + asks:
                split = 230 * bids / (bids + asks)
                depth_bar.create_rectangle(0, 0, split, 5, fill=long_color, width=0)
                depth_bar.create_rectangle(split, 0, 230, 5, fill=short_color, width=0)
        else:
            lines.append(t("Livro indisponível"))
        book_label.configure(text="\n".join(lines))
        for i, row in enumerate(news_rows):
            row.unbind("<Button-1>")
            if i < len(stories):
                published, title, source, link = stories[i]
                stamp = time.strftime("%Y-%m-%d", time.localtime(published))
                row.configure(text=f"{source} · {stamp}\n{title}", cursor="hand2", fg=foreground)
                row.bind("<Button-1>", lambda _, url=link: webbrowser.open(url))
            else:
                row.configure(text=t("Sem manchetes disponíveis") if i == 0 else "", cursor="", fg=muted)

    def render():
        nonlocal last_chart
        symbol, candles, points, errors = last_view or (selected.get(), [], [], [])
        if points:
            last_chart = candles, points
            value = points[-1]
            latest = next((point for point in reversed(points) if point.action), None)
            current = t("Manter {side}", side=label(value.side, language).lower()) if value.side else t("Aguardando sinal")
            if latest:
                signal_title.set("  →  ".join(t(SIGNAL_ACTIONS[code]) for code in latest.action.split(" / ")))
                stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(latest.time / 1000))
                signal_detail.set(t("Último sinal {time}", time=stamp) + (f"  ·  {current}" if latest != value else ""))
            else:
                signal_title.set(current)
                signal_detail.set("")
            action_label.configure(fg={1: long_color, -1: short_color, 0: foreground}[value.side])
            banner.set(f"{symbol} · {price_text(candles[-1].close)}")
            draw()
        else:
            banner.set(symbol)
            signal_title.set(t("Aguardando sinal"))
            signal_detail.set(t("Dados desatualizados" if errors else "Aguardando candles fechados de 15 min"))
            action_label.configure(fg=foreground)
        account_stale = any(error.startswith("Conta:") for error in errors)
        if monitor.position_rows and not account_stale:
            rows = monitor.position_rows
            position.set("\n".join(f'{row["symbol"]} · {label(int(row["sign"]), language)}' for row in rows[:3]))
            detail.set(t("Mais {count} posições", count=len(rows) - 3) if len(rows) > 3 else "")
        else:
            position.set(t("Dados desatualizados" if account_stale else
                           "Sem posição aberta" if monitor.account and monitor.closed_at else
                           "Aguardando conta" if monitor.account else "Conta não configurada"))
            detail.set("")
        mode = t("Ordens automáticas ativas para {symbol}", symbol=monitor.managed["symbol"]) if monitor.managed else t("Ordens automáticas desativadas")
        if monitor.managed and monitor.managed["symbol"] != selected.get():
            mode += " · " + t("Novas ordens neste gráfico estão bloqueadas.")
        messages = []
        if monitor.trade_error:
            messages.append(broker.CLOSE_UNCONFIRMED if monitor.recovery_pending else
                            "Execução pausada. Confira posição e diário.")
        if errors:
            messages.append("Dados desatualizados")
        if monitor.managed and monitor.entry_retry:
            messages.insert(0, "Abertura cancelada por desvio de preço. Aguardando nova tentativa.")
        status.set(" · ".join([mode] + [translate_error(language, message) for message in messages]))
        render_context()

    def schedule(seconds):
        nonlocal refresh_timer
        refresh_timer = root.after(round(seconds * 1000), refresh)

    def change(_):
        nonlocal browse_until, last_chart, last_view
        browse_until = time.time() + 300
        search.set("")
        last_chart = None
        last_view = None
        render()
        draw()
        refresh()

    def show_subaccounts():
        if messagebox.askyesno(t("Subcontas Lighter"), knowledge_rule(language, "SUBACCOUNTS") + "\n\n" + t("Abrir documentação oficial?")):
            webbrowser.open("https://docs.lighter.xyz/trading/trading-fees")

    def settings():
        nonlocal language
        win = tk.Toplevel(root)
        win.title(t("Configurações"))
        win.transient(root)
        win.grab_set()
        tabs = ttk.Notebook(win)
        tabs.pack(fill="both", expand=True, padx=12, pady=12)
        form = ttk.Frame(tabs, padding=14)
        general = ttk.Frame(tabs, padding=14)
        tabs.add(general, text=t("Idioma e MCP"))
        tabs.add(form, text=t("Ordens"))
        form.columnconfigure(1, weight=1)
        general.columnconfigure(1, weight=1)
        names = {name: code for code, name in LANGUAGES.items()}
        lang_pick = tk.StringVar(value=LANGUAGES.get(language, LANGUAGES["pt"]))
        ttk.Label(general, text=t("Idioma")).grid(row=0, column=0, sticky="w", pady=6)
        lang_field = ttk.Combobox(general, textvariable=lang_pick, values=list(names), state="readonly")
        lang_field.grid(row=0, column=1, sticky="ew", padx=8)

        def change_language(_):
            nonlocal language
            language = names[lang_pick.get()]
            prefs.update(language=language, beep=beep.get())
            write(preferences_path, prefs)
            for widget, message in localized:
                widget.configure(text=t(message))
            render()
            win.destroy()
            settings()

        lang_field.bind("<<ComboboxSelected>>", change_language)
        ttk.Label(general, text=t("Porta MCP")).grid(row=1, column=0, sticky="w", pady=6)
        port = tk.StringVar(value=str(mcp.port or prefs.get("mcp_port", 8765)))
        ttk.Entry(general, textvariable=port, width=12).grid(row=1, column=1, sticky="w", padx=8)
        mcp_url = tk.StringVar(value=mcp.url or "")
        ttk.Label(general, textvariable=mcp_url).grid(row=3, columnspan=2, sticky="w", pady=6)

        def start_mcp():
            try:
                selected_port = int(port.get())
                if not 1 <= selected_port <= 65535:
                    raise ValueError(t("Porta inválida."))
                mcp_url.set(mcp.start(selected_port))
                mcp.publish(monitor, selected.get())
                prefs["mcp_port"] = selected_port
                write(preferences_path, prefs)
            except (OSError, ValueError) as error:
                messagebox.showerror(t("MCP local"), str(error), parent=win)

        def copy_token():
            if mcp.token:
                root.clipboard_clear()
                root.clipboard_append(mcp.token)

        def stop_mcp():
            mcp.stop()
            mcp_url.set("")

        mcp_buttons = ttk.Frame(general)
        mcp_buttons.grid(row=2, columnspan=2, sticky="w", pady=6)
        for message, command in (("Ativar MCP local", start_mcp), ("Copiar token", copy_token), ("Desativar MCP", stop_mcp)):
            ttk.Button(mcp_buttons, text=t(message), command=command).pack(side="left", padx=3)

        def save_beep():
            prefs["beep"] = beep.get()
            write(preferences_path, prefs)

        ttk.Checkbutton(general, text=t("Um beep por ação confirmada"), variable=beep,
                        command=save_beep).grid(row=4, columnspan=2, sticky="w", pady=6)
        ttk.Button(general, text=t("Pasta de históricos"), command=lambda: webbrowser.open(data_root().as_uri())).grid(row=5, column=0, pady=6)
        ttk.Button(general, text=t("Subcontas"), command=show_subaccounts).grid(row=5, column=1, pady=6)

        def unlock_settings():
            if unlock(win):
                if "account" in private:
                    monitor.account = private["network"], private["account"]
                if "symbol" not in prefs and private.get("symbol"):
                    selected.set(private["symbol"])
                win.destroy()
                settings()
                refresh()

        if vault is None:
            ttk.Button(form, text=t("Desbloquear cofre"), command=unlock_settings).grid(row=8, columnspan=2, pady=6)
        values = {}
        for i, (name, default) in enumerate((("Rede", private.get("network", "testnet")), ("Índice da conta", str(private.get("account", ""))),
                ("Índice da chave", str(private.get("key_index", 3))), ("Chave privada", private.get("key", "")),
                ("Margem base USD", private.get("margin", "100")), ("Alavancagem", str(private.get("leverage", 5))),
                ("Limite de perda (% · opcional)", private.get("drawdown", "25") or ""))):
            ttk.Label(form, text=t(name)).grid(row=i, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=default)
            values[name] = var
            field = ttk.Combobox(form, textvariable=var, values=("testnet", "mainnet"), state="readonly") if i == 0 else ttk.Entry(form, textvariable=var, show="*" if i == 3 else "")
            field.grid(row=i, column=1, padx=8, pady=4, sticky="ew")
        def apply(trade):
            if busy:
                messagebox.showinfo(t("Configurações"), t("Aguarde a consulta atual terminar."), parent=win)
                return
            network = values["Rede"].get()
            symbol = monitor.managed["symbol"] if monitor.managed else selected.get()
            try:
                idx = int(values["Índice da conta"].get())
                if idx < 0:
                    raise ValueError("Índice inválido.")
                if not unlock(win):
                    return
                config = None
                if trade:
                    drawdown = values["Limite de perda (% · opcional)"].get().strip().replace(",", ".")
                    config = credentials(symbol, network, idx, values["Chave privada"].get(),
                                         int(values["Índice da chave"].get()), Decimal(values["Margem base USD"].get()),
                                         int(values["Alavancagem"].get()), Decimal(drawdown or "0"))
            except (ValueError, ArithmeticError) as error:
                messagebox.showerror(t("Configurações"), translate_error(language, error), parent=win)
                return
            if trade and network == "mainnet" and not messagebox.askyesno("Lighter Mainnet",
                    t("Ativar ordens automáticas reais para {symbol}?", symbol=symbol), parent=win):
                return
            win.destroy()

            def configure():
                old_identity = private.get("network"), private.get("account")
                updated = dict(private, network=network, account=idx, symbol=symbol, recover_close=trade)
                if config:
                    updated.update({field: config[field] for field in ("margin", "leverage", "drawdown", "key_index", "key")})
                elif old_identity != (network, idx):
                    updated.pop("key", None)
                    updated.pop("key_index", None)
                def save():
                    vault.write(private_path, updated)
                    private.clear()
                    private.update(updated)
                if trade:
                    monitor.arm(dict(config, vault=vault), on_ready=save)
                else:
                    save()
                    if monitor.account != (network, idx):
                        monitor.position_rows = []
                        monitor.closed_at = 0
                    monitor.managed = None
                    monitor.recovery = None
                    monitor.recovery_pending = False
                    monitor.entry_retry = None
                    monitor.account = network, idx
                    monitor.trade_error = ""
                if mcp.port:
                    mcp.publish(monitor, symbol)
                return True

            def saved(_):
                prefs.update(symbol=selected.get(), beep=beep.get(), language=language)
                write(preferences_path, prefs)
                render()
                refresh()

            submit(configure, saved, lambda: schedule(RETRY))

        ttk.Button(form, text=t("Só acompanhar conta"), command=lambda: apply(False)).grid(row=7, column=0, pady=5)
        ttk.Button(form, text=t("Ativar ordens automáticas"), command=lambda: apply(True)).grid(row=7, column=1, pady=5)

    canvas.bind("<Configure>", lambda _: draw())
    choice.bind("<<ComboboxSelected>>", change)
    def close_window():
        if busy:
            messagebox.showinfo("EMA Trader", t("Aguarde a consulta ou a execução em andamento terminar."))
        else:
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", close_window)
    render()
    root.after(100, refresh)
    root.mainloop()
    mcp.stop()
    worker.shutdown(wait=False)
    public_worker.shutdown(wait=False, cancel_futures=True)


def main():
    languages = argparse.ArgumentParser(add_help=False)
    languages.add_argument("--lang", choices=LANGUAGES)
    language = languages.parse_known_args()[0].lang or "pt"
    parser = argparse.ArgumentParser(parents=[languages], description=tr(language, "EMA Trader · faixa EMA de 15 minutos"))
    parser.add_argument("--gui", action="store_true", help=tr(language, "abrir a interface gráfica"))
    parser.add_argument("--symbol", default="BTC")
    parser.add_argument("--profile", default="DEFAULT", help=tr(language, "preferências separadas da janela"))
    parser.add_argument("--network", choices=("testnet", "mainnet"), default="testnet")
    parser.add_argument("--account", type=int)
    parser.add_argument("--key-index", type=int, default=3)
    parser.add_argument("--margin", type=Decimal, default=Decimal("100"))
    parser.add_argument("--leverage", type=int, default=5)
    parser.add_argument("--drawdown", type=Decimal, default=Decimal("25"), metavar="PERCENT",
                        help="account drawdown limit (default: 25; 0 disables)")
    parser.add_argument("--mcp-port", type=int, help=tr(language, "usar consulta local via MCP na porta indicada"))
    parser.add_argument("--trade", action="store_true")
    parser.add_argument("--save-key", action="store_true", help=tr(language, "Salvar chave no cofre"))
    parser.add_argument("--show-orders", action="store_true", help=tr(language, "Ler histórico privado de ordens"))
    parser.add_argument("--confirm-mainnet", action="store_true")
    parser.add_argument("--beep", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--subaccounts", action="store_true", help=tr(language, "mostrar guia de subcontas"))
    args = parser.parse_args()
    if args.subaccounts:
        print(knowledge_rule(language, "SUBACCOUNTS"))
        return
    try:
        if args.show_orders:
            for order in terminal_vault(language).orders():
                print(json.dumps(order, ensure_ascii=False))
        elif args.gui or sys.stdout is None:
            gui(args.profile, args.lang)
        else:
            cli(args)
    except KeyboardInterrupt:
        pass
    except (OSError, ValueError, broker.BridgeError) as error:
        parser.exit(2, translate_error(language, error) + "\n")


if __name__ == "__main__":
    main()
