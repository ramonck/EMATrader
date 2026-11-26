"""EMA Trader entry point. The CLI and desktop share the same monitor."""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import broker
from engine import Monitor, NORMAL_REFRESH, RETRY, account_positions, diagnose, markets, symbol_key
from storage import data_root, read, write

SUBACCOUNTS = """1. Na Lighter, abra o seletor da conta e crie uma subconta para cada estratégia.
2. Anote o índice de cada subconta. Crie a chave de API vinculada à subconta que será usada.
3. Para rodar BTC e SOL ao mesmo tempo, configure BTC no índice da primeira subconta e SOL no índice da segunda.
4. Separe o saldo de cada subconta e confira rede, índice e par em Testnet antes de habilitar ordens reais.

As duas instâncias podem usar a mesma pasta de dados. O catálogo e os candles são compartilhados. O diário de ordens é separado por rede e conta. A trava de uma posição por conta permanece ativa.

Exemplo no terminal: uma instância com --symbol BTC --account INDICE_BTC e outra com --symbol SOL --account INDICE_SOL. Informe a chave da subconta correspondente por variável de ambiente em cada terminal."""


def label(side):
    return "Long" if side > 0 else "Short" if side < 0 else "Zerado"


def credentials(symbol, network, account, key, key_index, margin, leverage):
    symbol_key(symbol)
    if account < 0 or not 0 <= key_index <= 254 or not key or not 1 <= leverage <= 20 or not 0 < margin <= 1_000_000:
        raise ValueError("Confira a conta, chave, margem e alavancagem.")
    return {"symbol": symbol, "network": network, "account": account, "key": key, "key_index": key_index,
            "margin": str(margin), "leverage": leverage}


def cli(args):
    monitor = Monitor()
    if args.account is not None:
        monitor.account = args.network, args.account
    if args.trade:
        if args.account is None or (args.network == "mainnet" and not args.confirm_mainnet):
            raise ValueError("Informe --account; para ordens reais, também --confirm-mainnet.")
        monitor.arm(credentials(args.symbol, args.network, args.account, os.environ.get("LIGHTER_API_KEY"),
                                args.key_index, args.margin, args.leverage), args.adopt_size)
    while True:
        candles, points, orders, errors = monitor.snapshot(args.symbol)
        if points:
            print(args.symbol, points[-1].action or label(points[-1].side), candles[-1].close, flush=True)
        for row in monitor.position_rows:
            print(f'{row["symbol"]} · {label(int(row["sign"]))} · qtd {row["position"]} · entrada {row["avg_entry_price"]} · P&L {row["unrealized_pnl"]}', flush=True)
        for order in orders:
            print(f'{order["action"]}: {order["filled"]}', flush=True)
            if args.beep and Decimal(order["filled"]) > 0:
                print("\a", end="", flush=True)
        if monitor.trade_error:
            print(monitor.trade_error, file=sys.stderr)
        if errors:
            print(" | ".join(errors), file=sys.stderr)
        if args.once:
            break
        time.sleep(RETRY if errors else max(2, NORMAL_REFRESH - time.time() % NORMAL_REFRESH + 2))


def gui(profile="DEFAULT"):
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
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
    worker = ThreadPoolExecutor(max_workers=1)
    ai_worker = ThreadPoolExecutor(max_workers=1)
    prefs = read(preferences_path, {})
    if "account" in prefs:
        monitor.account = prefs["network"], prefs["account"]
    selected = tk.StringVar(value=prefs.get("symbol", "BTC"))
    beep = tk.BooleanVar(value=prefs.get("beep", True))
    banner = tk.StringVar(value="Aguardando candles fechados de 15 min")
    status = tk.StringVar()
    position = tk.StringVar(value="Conta não configurada")
    pnl = tk.StringVar(value="—")
    detail = tk.StringVar()
    refresh_timer = None
    busy = False
    browse_until = 0
    last_chart = None

    toolbar = ttk.Frame(root, padding=(18, 12))
    toolbar.pack(fill="x")
    ttk.Label(toolbar, text="EMA Trader", font=("TkDefaultFont", 18, "bold")).pack(side="left", padx=(0, 18))
    choice = ttk.Combobox(toolbar, textvariable=selected, state="readonly", width=12, values=("BTC",))
    choice.pack(side="left", padx=4)
    refresh_button = ttk.Button(toolbar, text="Atualizar", command=lambda: refresh())
    refresh_button.pack(side="left", padx=4)
    settings_button = ttk.Button(toolbar, text="Configurações", command=lambda: settings())
    settings_button.pack(side="left", padx=4)
    ai_button = ttk.Button(toolbar, text="Revisar com IA", command=lambda: review_ai())
    ai_button.pack(side="left", padx=4)
    ttk.Button(toolbar, text="Subcontas", command=lambda: show_subaccounts()).pack(side="right")
    body = ttk.Frame(root, padding=(18, 0, 18, 12))
    body.pack(fill="both", expand=True)
    card = ttk.LabelFrame(body, text="Conta na Lighter", padding=14)
    card.pack(side="right", fill="y", padx=(12, 0))
    ttk.Label(card, textvariable=position, width=29).pack(anchor="w")
    ttk.Label(card, textvariable=pnl, font=("TkDefaultFont", 21, "bold")).pack(anchor="w", pady=9)
    ttk.Label(card, textvariable=detail, wraplength=240, justify="left").pack(anchor="w")
    main = ttk.Frame(body)
    main.pack(side="left", fill="both", expand=True)
    ttk.Label(main, textvariable=banner, font=("TkDefaultFont", 15, "bold")).pack(anchor="w", pady=(3, 8))
    canvas = tk.Canvas(main, bg="#101723", borderwidth=0, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    ttk.Label(main, text="Verde: long · Vermelho: short · Cinza: mantém", padding=(0, 7)).pack(anchor="w")
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
        for control in (choice, refresh_button, settings_button, ai_button):
            control.configure(state="disabled")
        future = worker.submit(task)

        def await_result():
            nonlocal busy
            if not future.done():
                root.after(70, await_result)
                return
            busy = False
            choice.configure(state="readonly")
            for control in (refresh_button, settings_button, ai_button):
                control.configure(state="normal")
            try:
                on_finish(future.result())
            except Exception as error:
                status.set(str(error))
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
            return monitor.snapshot(symbol), sorted(set(markets()) | {"BTC", symbol})

        def show(result):
            nonlocal last_chart
            (candles, points, orders, errors), catalog = result
            choice.configure(values=catalog)
            if points:
                last_chart = candles, points
                value = points[-1]
                banner.set(f"{symbol} · {value.action or 'Manter ' + label(value.side).lower()} · {candles[-1].close:,.2f}")
                draw()
            if monitor.position_rows:
                focus = monitor.managed["symbol"] if monitor.managed else symbol
                row = next((r for r in monitor.position_rows if r["symbol"] == focus), monitor.position_rows[0])
                position.set(row["symbol"] + " · " + label(int(row["sign"])))
                pnl.set(f'US$ {float(row["unrealized_pnl"]):+,.2f}')
                anothers = [f'{r["symbol"]} · {label(int(r["sign"]))} · US$ {float(r["unrealized_pnl"]):+,.2f}'
                            for r in monitor.position_rows if r is not row]
                detail.set(f'Quantidade {row["position"]} · entrada {row["avg_entry_price"]}\n' +
                           ("Dados desatualizados\n" if errors else "") + "\n".join(anothers))
            else:
                position.set("Sem posição aberta" if monitor.account and monitor.closed_at else
                             "Aguardando conta" if monitor.account else "Conta não configurada")
                pnl.set("—")
                detail.set("")
            mode = "Ordens automáticas ativas para " + monitor.managed["symbol"] if monitor.managed else "Ordens automáticas desativadas"
            status.set(" · ".join([mode] + ([monitor.trade_error] if monitor.trade_error else []) + errors))
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

    def schedule(seconds):
        nonlocal refresh_timer
        refresh_timer = root.after(round(seconds * 1000), refresh)

    def change(_):
        nonlocal browse_until, last_chart
        browse_until = time.time() + 300
        last_chart = None
        draw()
        refresh()

    def show_subaccounts():
        if messagebox.askyesno("Subcontas Lighter", SUBACCOUNTS + "\n\nAbrir documentação oficial?"):
            webbrowser.open("https://docs.lighter.xyz/trading/trading-fees")

    def review_ai():
        token = os.environ.get("OPENROUTER_API_KEY") or simpledialog.askstring("Revisar com IA", "Chave OpenRouter", show="*")
        if token:
            symbol = selected.get()
            ai_button.configure(state="disabled")
            task = ai_worker.submit(diagnose, symbol, os.environ.get("OPENROUTER_MODEL", "google/gemini-3.1-flash-lite"), token)

            def report():
                if not task.done():
                    root.after(150, report)
                    return
                ai_button.configure(state="normal")
                try:
                    messagebox.showinfo("Parecer · " + symbol, task.result())
                except (OSError, ValueError, KeyError) as error:
                    messagebox.showerror("IA · " + symbol, str(error))
            root.after(150, report)

    def settings():
        win = tk.Toplevel(root)
        win.title("Configurações")
        win.transient(root)
        win.grab_set()
        form = ttk.Frame(win, padding=18)
        form.pack(fill="both", expand=True)
        values = {}
        for i, (name, default) in enumerate((("Rede", prefs.get("network", "testnet")), ("Índice da conta", str(prefs.get("account", ""))),
                ("Índice da chave", "3"), ("Chave privada", ""), ("Margem USD", "100"), ("Alavancagem", "5"))):
            ttk.Label(form, text=name).grid(row=i, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=default)
            values[name] = var
            field = ttk.Combobox(form, textvariable=var, values=("testnet", "mainnet"), state="readonly") if i == 0 else ttk.Entry(form, textvariable=var, show="*" if i == 3 else "")
            field.grid(row=i, column=1, padx=8, pady=4, sticky="ew")
        ttk.Checkbutton(form, text="Um beep por ação confirmada", variable=beep).grid(row=6, columnspan=2, sticky="w", pady=8)

        def apply(trade):
            if busy:
                messagebox.showinfo("Configurações", "Aguarde a consulta atual terminar.", parent=win)
                return
            network = values["Rede"].get()
            symbol = monitor.managed["symbol"] if monitor.managed else selected.get()
            try:
                idx = int(values["Índice da conta"].get())
                if idx < 0:
                    raise ValueError("Índice inválido.")
                config = credentials(symbol, network, idx, values["Chave privada"].get(), int(values["Índice da chave"].get()),
                                     Decimal(values["Margem USD"].get()), int(values["Alavancagem"].get())) if trade else None
            except (ValueError, ArithmeticError) as error:
                messagebox.showerror("Configurações", str(error), parent=win)
                return
            if trade and network == "mainnet" and not messagebox.askyesno("Lighter Mainnet",
                    f"Ativar ordens automáticas reais para {symbol}?", parent=win):
                return
            expected = None
            if trade:
                expected = simpledialog.askstring("Assumir posição", "Se já houver posição, digite a quantidade exata com sinal (− para short). Deixe em branco para não assumir.", parent=win)
                if expected is None:
                    return
                expected = expected.replace("−", "-").strip() or None
            win.destroy()

            def configure():
                if trade:
                    monitor.arm(config, expected)
                else:
                    monitor.managed = None
                    monitor.account = network, idx
                return True

            def saved(_):
                prefs.update(symbol=selected.get(), network=network, account=idx, beep=beep.get())
                write(preferences_path, prefs)
                refresh()

            submit(configure, saved, lambda: schedule(RETRY))

        ttk.Button(form, text="Só acompanhar conta", command=lambda: apply(False)).grid(row=7, column=0, pady=5)
        ttk.Button(form, text="Ativar ordens automáticas", command=lambda: apply(True)).grid(row=7, column=1, pady=5)
        ttk.Button(form, text="Pasta de históricos", command=lambda: webbrowser.open(data_root().as_uri())).grid(row=8, column=0, pady=5)
        ttk.Button(form, text="Subcontas", command=show_subaccounts).grid(row=8, column=1)

    canvas.bind("<Configure>", lambda _: draw())
    choice.bind("<<ComboboxSelected>>", change)
    def close_window():
        if busy:
            messagebox.showinfo("EMA Trader", "Aguarde a consulta ou a execução em andamento terminar.")
        else:
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", close_window)
    root.after(100, refresh)
    root.mainloop()
    worker.shutdown(wait=False)
    ai_worker.shutdown(wait=False)


def main():
    parser = argparse.ArgumentParser(description="EMA Trader · faixa EMA de 15 minutos")
    parser.add_argument("--gui", action="store_true", help="abrir a interface gráfica")
    parser.add_argument("--symbol", default="BTC")
    parser.add_argument("--profile", default="DEFAULT", help="preferências separadas da janela")
    parser.add_argument("--network", choices=("testnet", "mainnet"), default="testnet")
    parser.add_argument("--account", type=int)
    parser.add_argument("--key-index", type=int, default=3)
    parser.add_argument("--margin", type=Decimal, default=Decimal("100"))
    parser.add_argument("--leverage", type=int, default=5)
    parser.add_argument("--adopt-size", help="quantidade real com sinal para assumir posição")
    parser.add_argument("--trade", action="store_true")
    parser.add_argument("--confirm-mainnet", action="store_true")
    parser.add_argument("--beep", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--subaccounts", action="store_true", help="mostrar guia de subcontas")
    args = parser.parse_args()
    if args.subaccounts:
        print(SUBACCOUNTS)
        return
    try:
        if args.gui or sys.stdout is None:
            gui(args.profile)
        else:
            cli(args)
    except KeyboardInterrupt:
        pass
    except (ValueError, broker.BridgeError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
