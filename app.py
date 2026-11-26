"""EMA Trader entry point. The CLI and desktop share the same monitor."""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import broker
from engine import Monitor, NORMAL_REFRESH, RETRY, markets, symbol_key
from i18n import LANGUAGES, tr, translate_error
from knowledge import knowledge_rule
from local_mcp import LocalMCP
from storage import data_root, read, write

def label(side, language):
    return "Long" if side > 0 else "Short" if side < 0 else tr(language, "Zerado")


def credentials(symbol, network, account, key, key_index, margin, leverage, drawdown=Decimal("25")):
    symbol_key(symbol)
    if account < 0 or not 0 <= key_index <= 254 or not key or not 1 <= leverage <= 20 or not 0 < margin <= 1_000_000:
        raise ValueError("Confira a conta, chave, margem e alavancagem.")
    if not drawdown.is_finite() or not 0 < drawdown < 100:
        raise ValueError("Limite de perda da conta inválido.")
    return {"symbol": symbol, "network": network, "account": account, "key": key, "key_index": key_index,
            "margin": str(margin), "leverage": leverage, "compound": True, "drawdown": str(drawdown)}


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


def run_cli(args, monitor, mcp):
    language = args.lang or "pt"
    if args.account is not None:
        monitor.account = args.network, args.account
    if args.trade:
        if args.account is None or (args.network == "mainnet" and not args.confirm_mainnet):
            raise ValueError("Informe --account; para ordens reais, também --confirm-mainnet.")
        monitor.arm(credentials(args.symbol, args.network, args.account, os.environ.get("LIGHTER_API_KEY"),
                                args.key_index, args.margin, args.leverage, args.drawdown))
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
        if errors:
            print(" | ".join(translate_error(language, error) for error in errors), file=sys.stderr)
        if args.once:
            break
        time.sleep(RETRY if errors else max(2, NORMAL_REFRESH - time.time() % NORMAL_REFRESH + 2))


def gui(profile="DEFAULT", language=None):
    import tkinter as tk
    from tkinter import messagebox, ttk
    import webbrowser

    profile = symbol_key(profile.upper())
    preferences_path = data_root() / "profiles" / (profile + ".json")
    root = tk.Tk()
    root.title("EMA Trader")
    root.geometry("1024x700")
    root.minsize(740, 520)
    icon = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets" / "icon.png"
    if icon.is_file():
        root.iconphoto(True, tk.PhotoImage(file=icon))
    monitor = Monitor()
    mcp = LocalMCP()
    worker = ThreadPoolExecutor(max_workers=1)
    prefs = read(preferences_path, {})
    language = language or prefs.get("language", "pt")

    def t(message, **values):
        return tr(language, message, **values)

    localized = []

    def localize(widget, message):
        localized.append((widget, message))
        widget.configure(text=t(message))
        return widget
    if "account" in prefs:
        monitor.account = prefs["network"], prefs["account"]
    selected = tk.StringVar(value=prefs.get("symbol", "BTC"))
    beep = tk.BooleanVar(value=prefs.get("beep", True))
    banner = tk.StringVar(value=t("Aguardando candles fechados de 15 min"))
    status = tk.StringVar()
    position = tk.StringVar(value=t("Conta não configurada"))
    pnl = tk.StringVar(value="—")
    detail = tk.StringVar()
    refresh_timer = None
    busy = False
    browse_until = 0
    last_chart = None
    last_view = None
    assets = ("BTC",)

    toolbar = ttk.Frame(root, padding=(18, 12))
    toolbar.pack(fill="x")
    ttk.Label(toolbar, text="EMA Trader", font=("TkDefaultFont", 18, "bold")).pack(side="left", padx=(0, 18))
    localize(ttk.Label(toolbar), "Buscar ativo").pack(side="left")
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
    body = ttk.Frame(root, padding=(18, 0, 18, 12))
    body.pack(fill="both", expand=True)
    card = localize(ttk.LabelFrame(body, padding=14), "Conta na Lighter")
    card.pack(side="right", fill="y", padx=(12, 0))
    ttk.Label(card, textvariable=position, width=29).pack(anchor="w")
    ttk.Label(card, textvariable=pnl, font=("TkDefaultFont", 21, "bold")).pack(anchor="w", pady=9)
    ttk.Label(card, textvariable=detail, wraplength=240, justify="left").pack(anchor="w")
    main = ttk.Frame(body)
    main.pack(side="left", fill="both", expand=True)
    ttk.Label(main, textvariable=banner, font=("TkDefaultFont", 15, "bold")).pack(anchor="w", pady=(3, 8))
    canvas = tk.Canvas(main, bg="#101723", borderwidth=0, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    localize(ttk.Label(main, padding=(0, 7)), "Verde: long · Vermelho: short · Cinza: mantém").pack(anchor="w")
    localize(ttk.Label(main, padding=(0, 0, 0, 6)), "AL abre long · FL fecha long · AS abre short · FS fecha short").pack(anchor="w")
    ttk.Label(root, textvariable=status, wraplength=900, padding=(18, 3, 18, 10)).pack(fill="x")

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
        stride = max(1, (width - 32) / len(candles))

        def y(value):
            return 18 + (hi - value) / max(hi - lo, 1e-12) * max(1, height - 36)

        last = None
        for i, c in enumerate(candles):
            x = 16 + i * stride
            point = values.get(c.time)
            if point and last:
                tone = {1: "#174637", -1: "#592f3a", 0: "#333e51"}[point.band]
                canvas.create_polygon(x-stride, y(last.upper), x, y(point.upper),
                                      x, y(point.lower), x-stride, y(last.lower), fill=tone)
            last = point
            shade = "#52e3b2" if c.close >= c.open else "#ff7489"
            canvas.create_line(x, y(c.high), x, y(c.low), fill=shade)
            top = min(y(c.open), y(c.close))
            canvas.create_rectangle(x-stride*.24, top, x+stride*.24, max(top+2, y(min(c.open,c.close))),
                                    fill=shade, outline="")
            if point and point.action:
                canvas.create_text(x, y(c.low)+11 if point.side > 0 else y(c.high)-11,
                                   text=point.action, fill="#c8f4e7" if point.side > 0 else "#ffb0ba")

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

        def update():
            result = monitor.snapshot(symbol)
            if mcp.port:
                mcp.publish(monitor, symbol)
            return result, sorted(set(markets()) | {"BTC", symbol})

        def show(result):
            nonlocal last_view, assets
            (candles, points, orders, errors), catalog = result
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
                schedule(RETRY if errors else max(2, NORMAL_REFRESH - time.time() % NORMAL_REFRESH + 2))

        submit(update, show, lambda: schedule(RETRY))

    def render():
        nonlocal last_chart
        symbol, candles, points, errors = last_view or (selected.get(), [], [], [])
        if points:
            last_chart = candles, points
            value = points[-1]
            action = value.action or t("Manter {side}", side=label(value.side, language).lower())
            banner.set(f"{symbol} · {action} · {candles[-1].close:,.2f}")
            draw()
        else:
            banner.set(t("Aguardando candles fechados de 15 min"))
        if monitor.position_rows:
            focus = monitor.managed["symbol"] if monitor.managed else symbol
            row = next((r for r in monitor.position_rows if r["symbol"] == focus), monitor.position_rows[0])
            position.set(row["symbol"] + " · " + label(int(row["sign"]), language))
            pnl.set(f'US$ {float(row["unrealized_pnl"]):+,.2f}')
            others = [f'{r["symbol"]} · {label(int(r["sign"]), language)} · US$ {float(r["unrealized_pnl"]):+,.2f}'
                      for r in monitor.position_rows if r is not row]
            size = t("Quantidade {quantity} · entrada {price}", quantity=row["position"], price=row["avg_entry_price"])
            detail.set("\n".join([size] + ([t("Dados desatualizados")] if errors else []) + others))
        else:
            position.set(t("Sem posição aberta" if monitor.account and monitor.closed_at else
                           "Aguardando conta" if monitor.account else "Conta não configurada"))
            pnl.set("—")
            detail.set("")
        mode = t("Ordens automáticas ativas para {symbol}", symbol=monitor.managed["symbol"]) if monitor.managed else t("Ordens automáticas desativadas")
        if monitor.managed and monitor.managed["symbol"] != selected.get():
            mode += " · " + t("Novas ordens neste gráfico estão bloqueadas.")
        messages = [message for message in [monitor.trade_error, *errors] if message]
        status.set(" · ".join([mode] + [translate_error(language, message) for message in messages]))

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
        values = {}
        for i, (name, default) in enumerate((("Rede", prefs.get("network", "testnet")), ("Índice da conta", str(prefs.get("account", ""))),
                ("Índice da chave", "3"), ("Chave privada", ""), ("Margem base USD", prefs.get("margin", "100")),
                ("Alavancagem", str(prefs.get("leverage", 5))),
                ("Limite de perda da conta (%)", prefs.get("drawdown", "25")))):
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
                config = credentials(symbol, network, idx, values["Chave privada"].get(), int(values["Índice da chave"].get()),
                                     Decimal(values["Margem base USD"].get()), int(values["Alavancagem"].get()),
                                     Decimal(values["Limite de perda da conta (%)"].get())) if trade else None
            except (ValueError, ArithmeticError) as error:
                messagebox.showerror(t("Configurações"), translate_error(language, error), parent=win)
                return
            if trade and network == "mainnet" and not messagebox.askyesno("Lighter Mainnet",
                    t("Ativar ordens automáticas reais para {symbol}?", symbol=symbol), parent=win):
                return
            win.destroy()

            def configure():
                if trade:
                    monitor.arm(config)
                else:
                    if monitor.account != (network, idx):
                        monitor.position_rows = []
                        monitor.closed_at = 0
                    monitor.managed = None
                    monitor.account = network, idx
                    monitor.trade_error = ""
                if mcp.port:
                    mcp.publish(monitor, symbol)
                return True

            def saved(_):
                prefs.update(symbol=selected.get(), network=network, account=idx, beep=beep.get(), language=language)
                if config:
                    prefs.update(margin=config["margin"], leverage=config["leverage"], drawdown=config["drawdown"])
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
    root.after(100, refresh)
    root.mainloop()
    mcp.stop()
    worker.shutdown(wait=False)


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
    parser.add_argument("--drawdown", type=Decimal, default=Decimal("25"))
    parser.add_argument("--mcp-port", type=int, help=tr(language, "usar consulta local via MCP na porta indicada"))
    parser.add_argument("--trade", action="store_true")
    parser.add_argument("--confirm-mainnet", action="store_true")
    parser.add_argument("--beep", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--subaccounts", action="store_true", help=tr(language, "mostrar guia de subcontas"))
    args = parser.parse_args()
    if args.subaccounts:
        print(knowledge_rule(language, "SUBACCOUNTS"))
        return
    try:
        if args.gui or sys.stdout is None:
            gui(args.profile, args.lang)
        else:
            cli(args)
    except KeyboardInterrupt:
        pass
    except (OSError, ValueError, broker.BridgeError) as error:
        parser.exit(2, translate_error(language, error) + "\n")


if __name__ == "__main__":
    main()
