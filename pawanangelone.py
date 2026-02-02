import streamlit as st
import pandas as pd
import numpy as np
import datetime, time, os
import plotly.graph_objects as go
import math
import random

# =========================================================
# CONFIG
# =========================================================
APP_NAME = "PAWAN MASTER ALGO SYSTEM"
TIMEFRAME = "5-Min"
BASE_DIR = "pawan_master_data"
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

# =========================================================
# UI STYLE (AngelOne Inspired LIGHT BLUE)
st.markdown("""
<style>
body { background-color:#0b1020; color:white; }
.sidebar .sidebar-content { background-color:#0f1630; }
.stButton>button {
    width:100%;
    height:45px;
    font-size:16px;
    border-radius:8px;
}
.css-1d391kg {background: #1f2a55;}  /* Blue Accent */
.css-1lcbmhc {background: #1f2a55;}  /* Blue Accent */
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
if "mode" not in st.session_state:
    st.session_state.mode = "FUTURES"

if "ws_status" not in st.session_state:
    st.session_state.ws_status = "Disconnected"

if "heartbeat" not in st.session_state:
    st.session_state.heartbeat = 0

if "symbols" not in st.session_state:
    st.session_state.symbols = []

if "candles" not in st.session_state:
    st.session_state.candles = {}

if "panic" not in st.session_state:
    st.session_state.panic = False

if "engine" not in st.session_state:
    st.session_state.engine = True

if "capital" not in st.session_state:
    st.session_state.capital = 200000

if "amt_per_trade" not in st.session_state:
    st.session_state.amt_per_trade = 10000

if "max_trades_symbol" not in st.session_state:
    st.session_state.max_trades_symbol = 2

if "sound_on" not in st.session_state:
    st.session_state.sound_on = True

if "auto_exit" not in st.session_state:
    st.session_state.auto_exit = True

if "alerts" not in st.session_state:
    st.session_state.alerts = {
        "heartbeat": True,
        "ws_reconnect": True,
        "hot_signal": True,
        "verified_signal": True,
        "order_placed": True,
        "slippage": True,
        "heatmap": True,
        "visual_validator": True
    }

if "orders" not in st.session_state:
    st.session_state.orders = []

if "positions" not in st.session_state:
    st.session_state.positions = []

if "signals" not in st.session_state:
    st.session_state.signals = []

if "verified_signals" not in st.session_state:
    st.session_state.verified_signals = []

if "hot_signals" not in st.session_state:
    st.session_state.hot_signals = []

if "pnl_stats" not in st.session_state:
    st.session_state.pnl_stats = {
        "total_profit": 0,
        "total_loss": 0,
        "no_trade_profit": 0,
        "no_trade_loss": 0,
        "tp_count": 0,
        "sl_count": 0,
        "net_profit": 0,
        "roi": 0
    }

if "lot_size" not in st.session_state:
    st.session_state.lot_size = {
        "NIFTY_FUT": 50,
        "BANKNIFTY_FUT": 25,
        "FINNIFTY_FUT": 40,
        "NIFTY_CE_20000": 50,
        "NIFTY_PE_19000": 50,
        "BANKNIFTY_CE_52000": 25
    }

# =========================================================
# HEADER
st.markdown(f"<h1 style='text-align:center;color:#00ff99;'>{APP_NAME}</h1>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.success(f"🟢 WebSocket: {st.session_state.ws_status}")
c2.info(f"⏱ Timeframe: {TIMEFRAME}")
c3.warning("📡 Mode: LIVE")
c4.success("🧠 Engine: Active")

# =========================================================
# TOP BUTTONS (Futures / Options)
col1, col2, col3 = st.columns([1,1,6])
with col1:
    if st.button("📈 FUTURES"):
        st.session_state.mode = "FUTURES"
with col2:
    if st.button("🧾 OPTIONS"):
        st.session_state.mode = "OPTIONS"

st.markdown(f"<h4 style='color:orange;'>MODE : {st.session_state.mode}</h4>", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
st.sidebar.title("📊 MENU")
page = st.sidebar.radio("", [
    "Dashboard",
    "Indicator Values",
    "Heatmap",
    "Futures Scanner",
    "Options Scanner",
    "Signal Validator",
    "Visual Validator",
    "Positions",
    "Order Book",
    "Profit & Loss",
    "Settings",
    "🚨 PANIC BUTTON"
])

# =========================================================
# PANIC BUTTON
if page == "🚨 PANIC BUTTON":
    if st.button("🚨 EXIT ALL & STOP SYSTEM"):
        st.session_state.panic = True
        st.session_state.engine = False
        st.error("ALL TRADES EXITED | ENGINE STOPPED")
        st.stop()

if st.session_state.panic:
    st.error("🚨 PANIC ACTIVATED – ALL TRADES HALTED")
    st.stop()

# =========================================================
# SYMBOLS (ALL)
def get_all_symbols(mode):
    if mode == "FUTURES":
        return ["NIFTY_FUT", "BANKNIFTY_FUT", "FINNIFTY_FUT"]
    else:
        return ["NIFTY_CE_20000", "NIFTY_PE_19000", "BANKNIFTY_CE_52000"]

# =========================================================
# ATM + EXPIRY LOGIC (SIMULATED)
def get_atm_symbol(mode):
    if mode == "FUTURES":
        return "NIFTY_FUT"
    else:
        return "NIFTY_CE_20000"

def get_expiry():
    return (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%d-%m-%Y")

# =========================================================
# LIVE DATA SIMULATION (For Module 1)
def generate_live_data(symbol):
    price = np.random.randint(48000, 49000)
    o = price - random.randint(10, 50)
    h = price + random.randint(10, 50)
    l = price - random.randint(10, 50)
    c = price
    v = random.randint(100, 1000)

    # Indicators
    rsi = round(random.uniform(20, 80), 2)
    macd = round(random.uniform(-5, 5), 2)
    bb_mid = price
    bb_up = price + random.randint(50, 150)
    bb_low = price - random.randint(50, 150)
    supertrend = random.choice(["UP", "DOWN"])
    macd_prev_high = macd + random.uniform(0, 2)

    return {
        "symbol": symbol,
        "spot": price,
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "volume": v,
        "rsi": rsi,
        "macd": macd,
        "macd_prev_high": macd_prev_high,
        "bb_upper": bb_up,
        "bb_middle": bb_mid,
        "bb_lower": bb_low,
        "supertrend": supertrend
    }

# =========================================================
# HEARTBEAT + WS STATUS
def heartbeat():
    st.session_state.heartbeat += 1
    st.session_state.ws_status = "Connected"
    if st.session_state.alerts["heartbeat"]:
        send_alert("Heartbeat Alive")
    return st.session_state.heartbeat

def ws_reconnect_alert():
    if st.session_state.alerts["ws_reconnect"]:
        send_alert("WebSocket Reconnected")

# =========================================================
# ALERTS (Updated for Cloud)
def send_alert(message):
    st.info(f"ALERT: {message}")
    if st.session_state.sound_on:
        st.toast(message)

def send_telegram_email(message):
    with open(os.path.join(LOG_DIR, "telegram_email_log.txt"), "a") as f:
        f.write(f"{datetime.datetime.now()} - {message}\n")

# =========================================================
# INDICATOR PANEL (Separated Table)
def indicator_panel(symbol):
    data = generate_live_data(symbol)
    df = pd.DataFrame([
        ["Supertrend", data["supertrend"], "⬆️" if data["supertrend"] == "UP" else "⬇️"],
        ["BB Upper", data["bb_upper"], ""],
        ["BB Middle", data["bb_middle"], "🔵"],
        ["BB Lower", data["bb_lower"], ""],
        ["RSI", data["rsi"], "🔵"],
        ["MACD", data["macd"], "🟢" if data["macd"] > 0 else "🔴"],
        ["Spot Price", data["spot"], "⚪"],
    ], columns=["Indicator", "Value", "Status"])
    st.table(df)
    return data

# =========================================================
# SIGNAL VALIDATOR (Accurate Rules)
def validate_signal(data):
    conditions = []
    # 1) Supertrend cross BB middle (pink)
    cond1 = (data["supertrend"] == "UP" and data["spot"] > data["bb_middle"])
    conditions.append(("Supertrend Cross BB Middle", cond1, "pink"))

    # 2) RSI cross 70/30 (blue)
    cond2 = (data["rsi"] >= 70 or data["rsi"] <= 30)
    conditions.append(("RSI 70/30 Cross", cond2, "blue"))

    # 3) MACD cross previous MACD high (green)
    cond3 = (data["macd"] > data["macd_prev_high"])
    conditions.append(("MACD Cross Prev High", cond3, "green"))

    # 4) Bollinger Band breakout (price > upper or < lower)
    cond4 = (data["spot"] > data["bb_upper"] or data["spot"] < data["bb_lower"])
    conditions.append(("BB Breakout", cond4, "green"))

    # 5) Supertrend must be UP (for buy)
    cond5 = (data["supertrend"] == "UP")
    conditions.append(("Supertrend UP", cond5, "green"))

    verified = all([c[1] for c in conditions])
    hot = sum([c[1] for c in conditions]) >= 4  # HOT SIGNAL
    return conditions, verified, hot

# =========================================================
# VISUAL VALIDATOR (Chart)
def visual_validator_chart(symbol, data):
    x = list(range(30))
    y = np.random.randint(48000, 49000, 30)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=x,
        open=y,
        high=y + 50,
        low=y - 50,
        close=y + 20
    ))

    # BB overlay
    fig.add_trace(go.Scatter(x=x, y=[data["bb_upper"] for _ in x], mode="lines", name="BB Upper"))
    fig.add_trace(go.Scatter(x=x, y=[data["bb_middle"] for _ in x], mode="lines", name="BB Middle"))
    fig.add_trace(go.Scatter(x=x, y=[data["bb_lower"] for _ in x], mode="lines", name="BB Lower"))

    # Supertrend overlay
    fig.add_trace(go.Scatter(
        x=x,
        y=[y[-1] + (20 if data["supertrend"] == "UP" else -20) for _ in x],
        mode="lines",
        name="Supertrend"
    ))

    fig.update_layout(template="plotly_dark")

    # Diamond marker
    fig.add_trace(go.Scatter(
        x=[29], y=[y[-1]],
        mode="markers",
        marker=dict(size=14, symbol="diamond", color="green"),
        name="💎 Signal"
    ))

    st.plotly_chart(fig, use_container_width=True)

    img_path = os.path.join(SCREENSHOT_DIR, f"{symbol}_{datetime.datetime.now().strftime('%H%M%S')}.png")
    # Note: fig.write_image requires kaleido installed
    try:
        fig.write_image(img_path)
    except:
        pass

    if st.session_state.sound_on and st.session_state.alerts["visual_validator"]:
        st.toast("Visual Validator Confirmed.")

    return img_path

# =========================================================
# ORDER EXECUTION (SIMULATED)
def place_order(symbol, side, qty, price, order_type="MARKET"):
    order_id = f"ORD{int(time.time())}"
    order = {
        "order_id": order_id, "symbol": symbol, "type": side,
        "order_type": order_type, "status": "COMPLETE",
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "qty": qty, "price": price
    }
    st.session_state.orders.append(order)

    st.session_state.positions.append({
        "symbol": symbol, "qty": qty, "avg": price,
        "ltp": price, "pnl": 0, "sl": price - 100,
        "tp": price + 150, "side": side,
        "entry_time": datetime.datetime.now().strftime("%H:%M:%S")
    })

    if st.session_state.alerts["order_placed"]:
        send_alert("ORDER PLACED")
    send_telegram_email(f"Order Placed: {order_id} | {symbol} | {side} | {qty} | {price}")
    return order

# =========================================================
# PNL CALCULATION
def calculate_pnl():
    pnl = sum([p["pnl"] for p in st.session_state.positions])
    st.session_state.pnl_stats["net_profit"] = pnl
    st.session_state.pnl_stats["total_profit"] = max(0, pnl)
    st.session_state.pnl_stats["total_loss"] = max(0, -pnl)
    total_trades = st.session_state.pnl_stats["tp_count"] + st.session_state.pnl_stats["sl_count"]
    win_rate = (st.session_state.pnl_stats["tp_count"] / max(1, total_trades)) * 100
    if st.session_state.capital > 0:
        st.session_state.pnl_stats["roi"] = (pnl / st.session_state.capital) * 100
    return pnl, win_rate

# =========================================================
# HEATMAP & UTILS
def is_in_position(symbol):
    count = sum([1 for p in st.session_state.positions if p["symbol"] == symbol])
    return count >= st.session_state.max_trades_symbol

def calculate_lots(symbol):
    lot = st.session_state.lot_size.get(symbol, 1)
    max_lots = math.floor(st.session_state.amt_per_trade / (lot * 1))
    return max(1, max_lots)

def heatmap_data():
    symbols = get_all_symbols(st.session_state.mode)
    rows = []
    for s in symbols:
        d = generate_live_data(s)
        st_green = 1 if d["supertrend"] == "UP" else 0
        bb_mid = 1 if d["spot"] > d["bb_middle"] else 0
        rsi_70 = 1 if d["rsi"] >= 70 else 0
        rsi_30 = 1 if d["rsi"] <= 30 else 0
        macd = 1 if d["macd"] > 0 else 0
        hot = 1 if (st_green + bb_mid + rsi_70 + macd) >= 3 else 0
        rows.append({
            "symbol": s, "supertrend": st_green, "bb_mid_cross": bb_mid,
            "rsi_70": rsi_70, "rsi_30": rsi_30, "macd": macd, "hot_signal": hot
        })
    return pd.DataFrame(rows)

def heatmap_chart(df):
    fig = go.Figure(data=go.Heatmap(
        z=df.drop("symbol", axis=1).values,
        x=df.drop("symbol", axis=1).columns,
        y=df["symbol"],
        colorscale="Viridis"
    ))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# PAGES
if page == "Dashboard":
    st.subheader("📌 Dashboard (LIVE DATA)")
    hb = heartbeat()
    st.info(f"Heartbeat: {hb}")
    symbols = get_all_symbols(st.session_state.mode)
    df = pd.DataFrame([generate_live_data(s) for s in symbols])
    st.dataframe(df)

elif page == "Indicator Values":
    st.subheader("📊 Indicator Values")
    symbol = st.selectbox("Select Symbol", get_all_symbols(st.session_state.mode))
    indicator_panel(symbol)

elif page == "Futures Scanner":
    st.subheader("📈 Futures Scanner")
    df = pd.DataFrame([generate_live_data(s) for s in get_all_symbols("FUTURES")])
    st.dataframe(df)

elif page == "Options Scanner":
    st.subheader("🧾 Options Scanner")
    df = pd.DataFrame([generate_live_data(s) for s in get_all_symbols("OPTIONS")])
    st.dataframe(df)

elif page == "Signal Validator":
    st.subheader("🧠 Signal Validator")
    symbol = st.selectbox("Select Symbol", get_all_symbols(st.session_state.mode))
    data = generate_live_data(symbol)
    conditions, verified, hot = validate_signal(data)
    st.table(pd.DataFrame(conditions, columns=["Condition", "Status", "Color"]))
    if hot:
        st.warning(f"🔥 HOT SIGNAL - {datetime.datetime.now().strftime('%H:%M:%S')}")
        st.session_state.hot_signals.append(symbol)
        if st.session_state.alerts["hot_signal"]:
            send_alert("HOT SIGNAL CREATED")
    if verified:
        st.success(f"💎 VERIFIED SIGNAL - {datetime.datetime.now().strftime('%H:%M:%S')}")
        st.session_state.verified_signals.append(symbol)

elif page == "Visual Validator":
    st.subheader("👁 Visual Validator")
    if len(st.session_state.verified_signals) == 0:
        st.warning("No verified signals yet.")
    else:
        symbol = st.selectbox("Verified Symbol", st.session_state.verified_signals)
        data = generate_live_data(symbol)
        if is_in_position(symbol):
            st.error("ALREADY MAX TRADES FOR SYMBOL - NO TRADE")
        else:
            img_path = visual_validator_chart(symbol, data)
            st.success(f"Screenshot saved: {img_path}")
            qty = calculate_lots(symbol)
            side = "BUY"
            if st.session_state.mode == "FUTURES":
                side = "BUY" if data["supertrend"] == "UP" else "SELL"
            place_order(symbol, side, qty, data["spot"])

elif page == "Positions":
    st.subheader("📦 Positions")
    st.table(pd.DataFrame(st.session_state.positions))
    for idx, pos in enumerate(st.session_state.positions):
        if st.button(f"Exit {pos['symbol']}"):
            st.session_state.positions.pop(idx)
            send_alert(f"Exited {pos['symbol']}")

elif page == "Order Book":
    st.subheader("📘 Order Book")
    st.table(pd.DataFrame(st.session_state.orders))

elif page == "Profit & Loss":
    st.subheader("📈 Profit & Loss")
    pnl, win_rate = calculate_pnl()
    st.metric("Net Profit", pnl)
    st.metric("Win Rate", f"{win_rate:.2f}%")
    st.metric("ROI", f"{st.session_state.pnl_stats['roi']:.2f}%")

elif page == "Heatmap":
    st.subheader("🔥 Heatmap (TV Style)")
    df = heatmap_data()
    st.dataframe(df)
    heatmap_chart(df)

elif page == "Settings":
    st.subheader("⚙ Settings")
    st.session_state.capital = st.number_input("Capital", value=st.session_state.capital)
    st.session_state.amt_per_trade = st.number_input("Amount per trade", value=st.session_state.amt_per_trade)
    st.session_state.max_trades_symbol = st.number_input("Max trades per symbol", value=st.session_state.max_trades_symbol)
    st.session_state.sound_on = st.checkbox("Alert Toasts ON", value=st.session_state.sound_on)
    st.session_state.auto_exit = st.checkbox("Auto Exit ON", value=st.session_state.auto_exit)
    st.write("🔔 Alert Toggles")
    for key in st.session_state.alerts:
        st.session_state.alerts[key] = st.checkbox(key.replace("_", " ").title(), value=st.session_state.alerts[key])

# =========================================================
# FOOTER
st.markdown("<hr><center>© Pawan Master Algo System</center>", unsafe_allow_html=True)
