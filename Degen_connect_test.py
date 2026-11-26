from pathlib import Path
from bs4 import BeautifulSoup
import warnings
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components  # <-- Fixed: Uncommented component import
import ta
import ta.momentum
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px

# 1. Must be the first Streamlit command (removed invalid 'page_link')
st.set_page_config(
    page_title="Degen Alpha | Crypto Quant Dashboard & Liquidity Analytics",
    page_icon="my desired output icon.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject custom CSS for clean spacing & metric aesthetics
def apply_custom_css():
    st.markdown("""
        <style>
            [data-testid="stElementToolbar"] {
                display: none !important;
            }
        </style>
        <style>
        /* Global App Dark Background */
        .stApp {
            background-color: #0E1117;
            color: #E0E0E0;
        }
        /* Custom Styling for Streamlit Metrics */
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 700;
        }
        /* Card-like borders for metric boxes */
        div[data-testid="stMetric"] {
            background-color: #161B22;
            border: 1px solid #30363D;
            padding: 12px 16px;
            border-radius: 8px;
        }
        /* Clean dataframes with rounded borders */
        .stDataFrame {
            border: 1px solid #30363D;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# 3. Inject Open Graph and Twitter card meta tags for SEO preview crawlers
seo_meta_tags = """
<head>
    <title>Degen Connect | Crypto Liquidity & Derivatives Dashboard</title>
    <meta name="description" content="Empowering retail traders with real-time crypto tracking, liquidity risk analysis, sentiment reporting, and macro indicators.">
    <meta property="og:title" content="Degen Connect - Crypto Analytics & Liquidity Risk">
    <meta property="og:description" content="Explore real-time cryptocurrency tracking, liquidity risk analysis, altcoin season index, and automated market reports.">
    <meta property="og:url" content="https://degen-connect.streamlit.app/">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Degen Connect">
    <meta name="twitter:description" content="Real-time crypto tracking, liquidity risk analysis, and macro market reports.">
</head>
"""
components.html(seo_meta_tags, height=0)

# 4. Inject JSON-LD Schema Structured Data for WebApplication
schema_markup = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Degen Connect",
  "url": "https://degen-connect.streamlit.app/",
  "applicationCategory": "FinanceApplication",
  "operatingSystem": "All",
  "description": "Real-time cryptocurrency tracking, liquidity risk analysis, market sentiment reporting, and macro indicators for retail traders."
}
</script>
"""
components.html(schema_markup, height=0)

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import ta
import yfinance as yf

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "BCHAIN-MKPRU_updated10.csv"


# ==========================================
# DATA FETCHING UTILITIES
# ==========================================
@st.cache_data(ttl=3600)
def fetch_yf_data(ticker_symbol: str, interval: str = "1d", period: str = "max") -> pd.DataFrame:
    """Generic helper to fetch clean, localized data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period, interval=interval).reset_index()

        if df.empty:
            st.error(f"No data returned from Yahoo Finance for {ticker_symbol}.")
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        df["Value"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df[["Date", "Value"]].dropna()
        return df[df["Value"] > 0].sort_values(by="Date").reset_index(drop=True)
    except Exception as e:
        st.error(f"Error fetching {ticker_symbol} data from Yahoo Finance: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_combined_btc_data():
    """Combines historical CSV data (2009-present) with live Yahoo Finance data for missing recent dates."""
    if not DATA_PATH.exists():
        st.error(f"Base dataset not found at `{DATA_PATH}`")
        return pd.DataFrame()

    df_old = pd.read_csv(DATA_PATH)[["Date", "Value"]]
    df_old["Date"] = pd.to_datetime(df_old["Date"], errors="coerce")
    df_old["Value"] = pd.to_numeric(df_old["Value"], errors="coerce")
    df_old = df_old.dropna().sort_values("Date").reset_index(drop=True)

    try:
        last_date = df_old["Date"].max()
        start_str = (last_date - pd.Timedelta(days=1)).strftime("%Y-%m-%d")

        ticker = yf.Ticker("BTC-USD")
        df_new = ticker.history(start=start_str, interval="1d").reset_index()

        if not df_new.empty:
            df_new["Date"] = pd.to_datetime(df_new["Date"]).dt.tz_localize(None)
            df_new["Value"] = pd.to_numeric(df_new["Close"], errors="coerce")
            df_new = df_new[["Date", "Value"]].dropna()

            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=["Date"], keep="last")
        else:
            df_combined = df_old
    except Exception:
        df_combined = df_old

    df_combined = df_combined[df_combined["Value"] > 0]
    return df_combined.sort_values(by="Date").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_sol_data():
    return fetch_yf_data("SOL-USD", interval="1d", period="max")


@st.cache_data(ttl=3600)
def load_eth_data():
    return fetch_yf_data("ETH-USD", interval="1d", period="max")


@st.cache_data(ttl=3600)
def load_btc_weekly_data():
    return fetch_yf_data("BTC-USD", interval="1wk", period="max")


@st.cache_data(ttl=3600)
def load_sol_weekly_data():
    return fetch_yf_data("SOL-USD", interval="1wk", period="max")


@st.cache_data(ttl=3600)
def load_eth_weekly_data():
    return fetch_yf_data("ETH-USD", interval="1wk", period="max")


# ==========================================
# REUSABLE PLOTTING HELPER
# ==========================================
def render_rsi_strategy_plot1(df, title, asset_color="purple", overbought_val=80, oversold_val=25, is_weekly=False):
    """Renders standardized price and RSI strategy charts."""
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6), gridspec_kw={"height_ratios": [2, 1]})

    timeframe_label = "Weekly " if is_weekly else ""
    
    # Price Subplot
    ax1.semilogy(df["Date"], df["Value"], linewidth=0.8, color=asset_color)
    ax1.set_ylabel(f"{title} Price (USD, Log Scale)")
    ax1.grid(True, which="both", linestyle="--", alpha=0.3)

    # RSI Subplot
    df["rsi"] = ta.momentum.rsi(close=df["Value"], window=14)
    ax2.plot(df["Date"], df["rsi"], linewidth=0.8, color="purple")
    ax2.axhline(overbought_val, color="red", linewidth=0.8, linestyle="--")
    ax2.axhline(oversold_val, color="green", linewidth=0.8, linestyle="--")
    ax2.set_ylabel(f"{timeframe_label}RSI (14)")
    ax2.grid(True, linestyle="--", alpha=0.3)

    top_label = "Aggressively DCA out" if is_weekly else "Take Profit"
    bottom_label = "Aggressively DCA in" if is_weekly else "Build a position"

    ax2.text(
        df["Date"].iloc[-1], overbought_val + 5, top_label,
        fontsize=8, ha="left", va="center", color="blue", bbox=dict(boxstyle="round", ec="k", fc="w")
    )
    ax2.text(
        df["Date"].iloc[-1], oversold_val - 7, bottom_label,
        fontsize=8, ha="left", va="center", color="blue", bbox=dict(boxstyle="round", ec="k", fc="w")
    )

    st.pyplot(fig)
    plt.close(fig)

    return df["rsi"].iloc[-1]



# ==========================================
# REUSABLE PLOTTING HELPER (FIXED 0-100 RSI)
# ==========================================
def render_rsi_strategy_plot(
    df,
    title,
    asset_color="purple",
    overbought_val=80,
    oversold_val=25,
    is_weekly=False,
):
  """Renders standardized price and RSI strategy charts with a fixed 0-100 RSI scale."""
  fig, (ax1, ax2) = plt.subplots(
      2, 1, sharex=True, figsize=(10, 6), gridspec_kw={"height_ratios": [2, 1]}
  )

  timeframe_label = "Weekly " if is_weekly else ""

  # Price Subplot
  ax1.semilogy(df["Date"], df["Value"], linewidth=0.8, color=asset_color)
  ax1.set_ylabel(f"{title} Price (USD, Log Scale)")
  ax1.grid(True, which="both", linestyle="--", alpha=0.3)

  # RSI Subplot
  df["rsi"] = ta.momentum.rsi(close=df["Value"], window=14)
  ax2.plot(df["Date"], df["rsi"], linewidth=0.8, color="purple")
  ax2.axhline(overbought_val, color="red", linewidth=0.8, linestyle="--")
  ax2.axhline(oversold_val, color="green", linewidth=0.8, linestyle="--")

  # --- FIX: Force full 0 to 100 scale ---
  ax2.set_ylim(0, 100)
  ax2.set_yticks([0, 25, 50, 75, 100])

  ax2.set_ylabel(f"{timeframe_label}RSI (14)")
  ax2.grid(True, linestyle="--", alpha=0.3)

  top_label = "Aggressively DCA out" if is_weekly else "Take Profit"
  bottom_label = "Aggressively DCA in" if is_weekly else "Build a position"

  ax2.text(
      df["Date"].iloc[-1],
      overbought_val + 5,
      top_label,
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.text(
      df["Date"].iloc[-1],
      oversold_val - 7,
      bottom_label,
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )

  st.pyplot(fig)
  plt.close(fig)

  return df["rsi"].iloc[-1]
# ==========================================
# BITCOIN MODULES
# ==========================================
def module_moving_average():
    warnings.filterwarnings("ignore")
    st.header("Bull and Bear Market trigger")

    df = load_combined_btc_data()
    if df.empty:
        return

    df["ma"] = df["Value"].rolling(window=200).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.semilogy(df["Date"], df["Value"], label="BTC Price (USD)", linewidth=0.7)
    ax.plot(df["Date"], df["ma"], color="red", label="200-Day Moving Avg", linewidth=1.2)
    ax.set_ylabel("Price (USD, Log Scale)")
    ax.set_xlabel("Date")
    ax.legend(loc="upper left")
    ax.grid(True, which="both", linestyle="--", alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    latest_price = df["Value"].iloc[-1]
    latest_ma = df["ma"].iloc[-1]

    if latest_price > latest_ma:
        st.success(f"**Bull market triggered: Risk-On Environment** (Price: ${latest_price:,.2f} > 200DMA: ${latest_ma:,.2f})")
    else:
        st.error(f"**Bear market triggered: Risk-Off Environment** (Price: ${latest_price:,.2f} <= 200DMA: ${latest_ma:,.2f})")


def module_rsi_strategy():
    warnings.filterwarnings("ignore")
    st.subheader("Bitcoin Momentum (RSI) Strategy")

    df = load_combined_btc_data()
    if df.empty:
        return

    latest_rsi = render_rsi_strategy_plot(df, "BTC", asset_color="gray", overbought_val=80, oversold_val=25)

    if  80 <= latest_rsi <= 89:
        st.write(f"**SWING TRADER ALERT : RSI is {latest_rsi:.2f} (> 80):** Time to sell / DCA out (short term positions)")
    elif latest_rsi >= 89:
            st.write(f"**SWING TRADER ALERT : RSI is {latest_rsi:.2f} (>= 89):** we are approaching a micro/macro top / DCA out aggressively (we are in the topping out zone)")
    elif 20 < latest_rsi <= 25:
        st.write(f"**SWING TRADER ALERT : RSI is {latest_rsi:.2f} (< 25):** Time to buy / DCA in (short term positions : for a bounce in bear market or start building a long term position in bull market)")
    elif 15 < latest_rsi <= 20:
            st.write(f"**SWING TRADER ALERT : RSI is {latest_rsi:.2f} (< 20):** We are approaching a micro/macro bottom / DCA in aggressively (we are in the bottoming out zone : buy long term positions)")

    elif 10 < latest_rsi <= 15:
            st.write(f"**SWING TRADER ALERT : RSI is {latest_rsi:.2f} (< 15):** SELL EVERYTHING AND BUY BITCOIN / DCA in EXTREMELY AGGRESSIVELY (do not get fooled by the black swan event : it just a shakeout of weak hands)")
    else:
        st.write(f"**SWING TRADER ALERT : RSI is {latest_rsi:.2f}:** Neutral zone (Hold position)")


    

def module_dca_calculator():
    st.subheader("3. Dollar Cost Averaging Calculator")

    df = load_combined_btc_data()
    if df.empty:
        return

    col1, col2 = st.columns(2)
    with col1:
        investment_amount = st.number_input("Enter investment amount ($):", min_value=1, value=100, step=1)
        investment_interval = st.number_input("Enter investment interval (in days):", min_value=1, value=7, step=1)

    with col2:
        start_date = pd.to_datetime(st.date_input("Enter start date:", value=df["Date"].min()))
        end_date = pd.to_datetime(st.date_input("Enter end date:", value=df["Date"].max()))

    df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    if investment_amount < 10:
        st.error("Investment amount must be greater than $10")
    elif df_filtered.empty:
        st.warning("No data within the specified date range.")
    else:
        dca_df = df_filtered.iloc[::investment_interval]
        total_invested = len(dca_df) * investment_amount
        shares_bought = (investment_amount / dca_df["Value"]).sum()
        final_value = shares_bought * df_filtered["Value"].iloc[-1]

        st.success(f"**Total Invested:** ${total_invested:,.2f}")
        st.success(f"**Final Portfolio Value:** ${final_value:,.2f}")



import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


@st.cache_data(ttl=3600)
def fetch_fear_and_greed_data(limit: int = 30) -> pd.DataFrame:
    """Fetches real-time and historical Fear and Greed Index data from Alternative.me API."""
    url = f"https://api.alternative.me/fng/?limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])

        df = pd.DataFrame(data)
        if not df.empty:
            df["value"] = df["value"].astype(int)
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
            df = df.sort_values("timestamp").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error fetching Fear & Greed data: {e}")
        return pd.DataFrame()


def fear_and_greed_indicator():
    """Renders the Crypto Fear and Greed Dashboard in Streamlit."""
    st.subheader("Crypto Fear & Greed Sentiment Indicator")

    # Timeframe selection for historical trend
    col_ctrl, _ = st.columns([1, 2])
    with col_ctrl:
        days = st.selectbox(
            "Historical Period:",
            [7, 30, 90, 180, 365 ,730 ,1460,2920, 5840],
            index=1,
            key="fng_days_select",
        )

    df = fetch_fear_and_greed_data(limit=days)

    if df.empty:
        st.warning("Unable to load Fear & Greed data at this time.")
        return

    # Extract latest readings
    latest_row = df.iloc[-1]
    current_val = latest_row["value"]
    current_class = latest_row["value_classification"]
    prev_val = df.iloc[-2]["value"] if len(df) > 1 else current_val
    delta_val = current_val - prev_val

    # Color Mapping based on score
    def get_sentiment_color(score: int) -> str:
        if score <= 24:
            return "#FF5252"  # Red - Extreme Fear
        elif score <= 46:
            return "#FF9800"  # Orange - Fear
        elif score <= 54:
            return "#FFEB3B"  # Yellow - Neutral
        elif score <= 75:
            return "#00E676"  # Light Green - Greed
        else:
            return "#00B0FF"  # Blue/Cyan - Extreme Greed

    sentiment_color = get_sentiment_color(current_val)

    # Layout Split: Left (Gauge & Metrics), Right (Strategy & History)
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        # Plotly Gauge Chart
        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=current_val,
                delta={
                    "reference": prev_val,
                    "relative": False,
                    "position": "top",
                },
                number={
                    "suffix": " / 100",
                    "font": {"size": 36, "color": sentiment_color},
                },
                title={
                    "text": f"Current Sentiment: <b>{current_class}</b>",
                    "font": {"size": 18, "color": "#FFFFFF"},
                },
                gauge={
                    "axis": {
                        "range": [0, 100],
                        "tickwidth": 1,
                        "tickcolor": "#888888",
                        "tickvals": [0, 25, 47, 55, 76, 100],
                    },
                    "bar": {"color": sentiment_color, "thickness": 0.25},
                    "bgcolor": "rgba(0,0,0,0)",
                    "borderwidth": 1,
                    "bordercolor": "#333333",
                    "steps": [
                        {"range": [0, 24], "color": "rgba(255, 82, 82, 0.2)"},
                        {"range": [25, 46], "color": "rgba(255, 152, 0, 0.2)"},
                        {"range": [47, 54], "color": "rgba(255, 235, 59, 0.2)"},
                        {"range": [55, 75], "color": "rgba(0, 230, 118, 0.2)"},
                        {"range": [76, 100], "color": "rgba(0, 176, 255, 0.2)"},
                    ],
                },
            )
        )

        fig_gauge.update_layout(
            height=290,
            margin=dict(l=30, r=30, t=50, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
        )

        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_right:
        st.subheader("Actionable Strategy Guidance")

        # Dynamic Strategy Output based on sentiment level
        if current_val <= 24:
            st.success(
                "🛒 **Extreme Fear (Accumulation Zone):** Market sentiment is overly pessimistic. "
                "Historically, extreme fear presents high-conviction DCA long entry points for quality spot and futures positions."
            )
        elif 25 <= current_val <= 46:
            st.info(
                "👀 **Fear (Cautious Buying):** Market participants are anxious. "
                "Look for bullish divergence on major crypto assets (BTC, ETH) to build spot positions."
            )
        elif 47 <= current_val <= 54:
            st.info(
                "✊ **Neutral (Balanced Market):** Market lacks strong directional momentum. "
                "Maintain current allocations and await clear trend breakout signals."
            )
        elif 55 <= current_val <= 75:
            st.warning(
                "⚠️ **Greed (Tighten Risk):** Buying interest is high and FOMO is building. "
                "Consider taking partial profits on speculative altcoins into stablecoins, BTC, ETH and SOL."
            )
        else:
            st.error(
                "🚨 **Extreme Greed (Macro/Micro Top Risk):** Market is in a state of euphoria. "
                "Scale out of aggressive positions, hedge downside risk, and avoid leverage longs."
            )

    # Historical Trend Line Chart below gauge
    st.markdown("---")
    st.markdown("### Historical Sentiment Trend")

    fig_line = go.Figure()

    fig_line.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["value"],
            mode="lines+markers",
            name="Fear & Greed Index",
            line=dict(color="#00E676", width=2),
            marker=dict(size=4),
            hovertemplate="Date: %{x|%Y-%m-%d}<br>Score: %{y}<extra></extra>",
        )
    )

    # Reference Threshold Bands
    fig_line.add_hrect(
        y0=0, y1=24, fillcolor="red", opacity=0.1, line_width=0, annotation_text="Extreme Fear"
    )
    fig_line.add_hrect(
        y0=76, y1=100, fillcolor="cyan", opacity=0.1, line_width=0, annotation_text="Extreme Greed"
    )

    fig_line.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,34,45,0.5)",
        font={"color": "white"},
        xaxis=dict(showgrid=False),
        yaxis=dict(range=[0, 100], gridcolor="#333333"),
    )

    st.plotly_chart(fig_line, use_container_width=True)




# Run command : streamlit run crypto_fear_greed_dashboard.py



def module_sentiment_analysis():
    import matplotlib.pyplot as plt
    import pandas as pd
    import streamlit as st
    import warnings
    warnings.filterwarnings("ignore")
    st.header("200 Week Moving Average Heatmap")

    # Load combined data
    df = load_combined_btc_data()
    if df.empty:
        return

    # 1. Parse dates and filter non-zero historical data
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Value"] > 0].sort_values("Date").reset_index(drop=True)

    # 2. 200WMA with min_periods=1 allows calculation starting from 2010
    df["200wma"] = df["Value"].rolling(window=1400, min_periods=1).mean()

    # 3. Monthly sampling (every 30 days) for colored heatmap dots
    monthly = df.iloc[::30].copy()
    monthly["distance"] = monthly["200wma"].pct_change() * 100

    # 4. Matplotlib Dark Theme Plot
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 5))

    # Plot Price Line and 200WMA line across full history
    ax.semilogy(df["Date"], df["Value"], color="grey", zorder=1, label="BTC Price")
    ax.semilogy(df["Date"], df["200wma"], color="purple", zorder=2, label="200WMA")

    # Heatmap Scatter points over full history
    scatter = ax.scatter(
        monthly["Date"],
        monthly["Value"],
        c=monthly["distance"],
        cmap="rainbow",
        vmin=0,
        vmax=16,
        zorder=3,
        s=18
    )

    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("% monthly increase in value of 200wMA")
    cbar.ax.yaxis.set_label_position("left")

    ax.set_ylabel("Price (USD, Log Scale)")
    ax.set_xlabel("Date")
    ax.grid(True, which="both", linestyle="--", alpha=0.2)

    st.pyplot(fig)
    plt.close(fig)





# ==========================================
# SOLANA MODULES
# ==========================================
def sol_momentum_strat():
    warnings.filterwarnings("ignore")
    st.subheader("Solana (SOL) Momentum Strategy")

    df = load_sol_data()
    if df.empty:
        return

    current_rsi = render_rsi_strategy_plot(df, "SOL", asset_color="#14F195", overbought_val=80, oversold_val=25)



    if  80 <= current_rsi <= 85:
        st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (> 80):** Time to sell / DCA out (short term positions)")
    elif current_rsi >= 85:
            st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (>= 85):** we are approaching a micro/macro top / DCA out aggressively (we are in the topping out zone)")
    elif 20 < current_rsi <= 25:
        st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (< 25):** Time to buy / DCA in (short term positions : for a bounce in bear market or start building a long term position in bull market)")
    elif 15 < current_rsi <= 20:
            st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (< 20):** We are approaching a micro/macro bottom / DCA in aggressively (we are in the bottoming out zone: buy long term positions)")

    elif 10 < current_rsi <= 15:
            st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (< 15):** SELL EVERYTHING AND BUY SOLANA / DCA in EXTREMELY AGGRESSIVELY (do not get fooled by the black swan event : it just a shakeout of weak hands)")
    else:
        st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f}:** Neutral zone (Hold positions)")


def sol_weekly_momentum_strat():
    warnings.filterwarnings("ignore")

    df = load_sol_weekly_data()
    if df.empty:
        return

    current_rsi = render_rsi_strategy_plot(df, "SOL Weekly", asset_color="#14F195", overbought_val=87, oversold_val=30, is_weekly=True)

    if current_rsi >= 87:
        st.write(
            f"**INVESTOR ALERT: Solana Weekly RSI is at {current_rsi:.2f} (>87):** Overbought - "
            "SELL THE TOP!: The market will top in the next higher high; watch out for a bearish divergence."
        )
    elif current_rsi <= 30:
        st.write(
            f"**INVESTOR ALERT : Solana Weekly RSI is at {current_rsi:.2f} (<30):** Oversold - "
            "BUY THE BOTTOM!: The market will bottom in the next lower low; watch out for a bullish divergence."
        )
    else:
        st.write(f"**INVESTOR ALERT : Solana Weekly RSI is at {current_rsi:.2f} (Neutral 30-87):** Hold position.")


# ==========================================
# ETHEREUM MODULES
# ==========================================
def eth_momentum_strat():
    warnings.filterwarnings("ignore")
    st.subheader("Ethereum (ETH) Momentum Strategy")

    df = load_eth_data()
    if df.empty:
        return

    current_rsi = render_rsi_strategy_plot(df, "ETH", asset_color="#627EEA", overbought_val=80, oversold_val=25)



    if  75 <= current_rsi <= 80:
        st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (> 80):** Time to sell / DCA out (short term positions)")
    elif current_rsi >= 85:
            st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (>= 85):** we are approaching a micro/macro top / DCA out aggressively (we are in the topping out zone)")


    elif 80 < current_rsi < 85:
            st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (80-85):** we are approaching a micro/macro top / DCA out aggressively (long term positions)")
    
  

    elif 20 < current_rsi <= 26:
        st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (< 25):** Time to buy / DCA in (short term positions : for a bounce in bear market or start building a long term position in bull market)")
    elif 15 < current_rsi <= 20:
            st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (< 20):** We are approaching a micro/macro bottom / DCA in aggressively (we are in the bottoming out zone: buy long term positions)")

    elif 10 < current_rsi <= 15:
            st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f} (< 15):** SELL EVERYTHING AND BUY ETHEREUM / DCA in EXTREMELY AGGRESSIVELY (do not get fooled by the black swan event : it just a shakeout of weak hands)")
    else:
        st.write(f"**SWING TRADER ALERT : RSI is {current_rsi:.2f}:** Neutral zone (Hold positions)")



    


def eth_weekly_momentum_strat():
    warnings.filterwarnings("ignore")

    df = load_eth_weekly_data()
    if df.empty:
        return

    current_rsi = render_rsi_strategy_plot(df, "ETH Weekly", asset_color="#627EEA", overbought_val=83, oversold_val=30, is_weekly=True)

    if current_rsi >= 83:
        st.write(
            f"**INVESTOR ALERT : Ethereum Weekly RSI is at {current_rsi:.2f} (>=83):** Overbought - "
            "SELL THE TOP!: The market will top in the next higher high; watch out for a bearish divergence."
        )
    elif current_rsi <= 30:
        st.write(
            f"**INVESTOR ALERT : Ethereum Weekly RSI is at {current_rsi:.2f} (<=30):** Oversold - "
            "BUY THE BOTTOM!: The market will bottom in the next lower low; watch out for a bullish divergence."
        )
    else:
        st.write(f"**INVESTOR ALERT : Ethereum Weekly RSI is at {current_rsi:.2f} (Neutral 30-83):** Hold position.")


# ==========================================
# BITCOIN WEEKLY MODULE
# ==========================================
def btc_weekly_momentum_strat():
    warnings.filterwarnings("ignore")

    df = load_btc_weekly_data()
    if df.empty:
        return

    current_rsi = render_rsi_strategy_plot(df, "BTC Weekly", asset_color="#F7931A", overbought_val=87, oversold_val=30, is_weekly=True)

    if current_rsi >= 87:
        st.write(
            f"**-INVESTOR ALERT : Bitcoin Weekly RSI is at {current_rsi:.2f} (>=87):** Overbought - "
            "SELL THE TOP!: The market will top in the next higher high; watch out for a bearish divergence."
        )
    elif current_rsi <= 30:
        st.write(
            f"**INVESTOR ALERT : Bitcoin Weekly RSI is at {current_rsi:.2f} (<30):** Oversold - "
            "BUY THE BOTTOM!: The market will bottom in the next lower low; watch out for a bullish divergence."
        )
    else:
        st.write(f"**INVESTOR ALERT : Bitcoin Weekly RSI is at {current_rsi:.2f} (Neutral 30-87):** Hold position.")





import base64
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_plotly_table(df: pd.DataFrame, title: str = ''):
  """Renders a dataframe as a Plotly Table with a PNG camera icon download button."""
  fig = go.Figure(
      data=[
          go.Table(
              header=dict(
                  values=[f'<b>{col}</b>' for col in df.columns],
                  fill_color='#1E222D',
                  font=dict(color='white', size=13),
                  align='left',
                  height=35,
              ),
              cells=dict(
                  values=[df[col] for col in df.columns],
                  fill_color='#131722',
                  font=dict(color='#D1D4DC', size=12),
                  align='left',
                  height=30,
              ),
          )
      ]
  )

  fig.update_layout(
      title=dict(text=title, font=dict(size=16, color='white')),
      margin=dict(l=10, r=10, t=40, b=10),
      paper_bgcolor='rgba(0,0,0,0)',
      plot_bgcolor='rgba(0,0,0,0)',
      height=min(500, 50 + len(df) * 32),
  )

  st.plotly_chart(
      fig,
      use_container_width=True,
      config={
          'displayModeBar': True,
          'toImageButtonOptions': {
              'format': 'png',
              'filename': f'{title.lower().replace(" ", "_")}_dataset',
              'height': 800,
              'width': 1200,
              'scale': 2,
          },
          'modeBarButtonsToRemove': [
              'zoom2d',
              'pan2d',
              'select2d',
              'lasso2d',
              'zoomIn2d',
              'zoomOut2d',
              'autoScale2d',
              'resetScale2d',
          ],
          'displaylogo': False,
      },
  )


def market_report():
  # Load Data
  try:
    df = pd.read_csv('coingecko-crypto-data.csv')
  except FileNotFoundError:
    st.error("Data file 'coingecko-crypto-data.csv' not found.")
    return

  # Categorize Liquidity Risk
  liquidity_risk = []
  for index in df.index:
    vol = df['24h Volume'][index] if '24h Volume' in df.columns else np.nan
    mcap = df['Market Cap'][index] if 'Market Cap' in df.columns else np.nan

    if pd.isna(vol) or pd.isna(mcap) or mcap == 0:
      liquidity_risk.append('unknown')
    elif vol < (mcap * 0.05):
      liquidity_risk.append('illiquid')
    elif vol <= (mcap * 0.1):
      liquidity_risk.append('fairly liquid')
    elif vol <= (mcap * 0.3):
      liquidity_risk.append('highly liquid')
    elif vol <= (mcap * 0.5):
      liquidity_risk.append('limited long term potential')
    else:
      liquidity_risk.append('stay off')

  df['liquidity_risk'] = liquidity_risk

  stablecoins = [
      'Tether',
      'USDC',
      'USDS',
      'Dai',
      'USD1',
      'Ethena USDe',
      'Global Dollar',
      'BlackRock USD Institutional Digital Liquidity Fund',
      'PayPal USD',
      'Ripple USD',
      'USDD',
      'Falcon USD',
      'BFUSD',
      'United Stables',
      'USDGO',
      'GHO',
      'YLDS',
      'Usual USD',
      'Figure Heloc',
      'Circle USYC',
      'Tether Gold',
      'Ondo US Dollar Yield',
      'PAX Gold',
      'Spiko Amundi Overnight Swap Fund (EUR)',
      'Spiko EU T-Bills Money Market Fund',
      'Janus Henderson Anemoy Treasury Fund',
      'Invesco Short Duration US Government Securities Fund',
      'Janus Henderson Anemoy AAA CLO Fund',
  ]
  df.loc[df['Coin'].isin(stablecoins), 'liquidity_risk'] = 'stablecoin'

  def evaluate_bullish_sentiment(top_10_losers_df, period_type):
    stablecoin_count = (
        top_10_losers_df['liquidity_risk'] == 'stablecoin'
    ).sum()

    if period_type == 'hourly':
      if stablecoin_count < 10:
        return 'This day is not so bullish.'
      elif 10 <= stablecoin_count <= 20:
        return 'Bullishness is kicking in today.'
      elif 21 <= stablecoin_count <= 25:
        return 'This day is bullish.'
      else:
        return (
            'This day is extremely bullish: Take partial profits on your long'
            ' day trades and look for potential short day trades.'
        )

    elif period_type == 'daily':
      if stablecoin_count < 10:
        return 'This week is not so bullish.'
      elif 10 <= stablecoin_count <= 20:
        return 'Bullishness is kicking in this week.'
      elif 21 <= stablecoin_count <= 25:
        return 'This week is bullish.'
      else:
        return (
            'This week is extremely bullish: Take partial profits on your long'
            ' swing trades and look for potential short swing trades.'
        )

    elif period_type == 'weekly':
      if stablecoin_count < 10:
        return 'This month is not so bullish: It is not altseason yet.'
      elif 10 <= stablecoin_count <= 20:
        return 'Bullishness is kicking in this month: Altseason is here.'
      elif 21 <= stablecoin_count <= 25:
        return 'This month is bullish: The altseason is bullish.'
      else:
        return (
            'This month is extremely bullish: The altseason is extremely'
            ' bullish. Take partial profits on alts and use them to Buy The Dip'
            ' (BTD) on BTC, SOL, and ETH for the dip coming in less than a month.'
            ' Take some swing short trades.'
        )

  def evaluate_bearish_sentiment(top_10_winners_df, period_type):
    stablecoin_count = (
        top_10_winners_df['liquidity_risk'] == 'stablecoin'
    ).sum()

    if period_type == 'hourly':
      if stablecoin_count < 10:
        return 'This day is not so bearish.'
      elif 10 <= stablecoin_count <= 20:
        return 'Bearishness is kicking in today.'
      elif 21 <= stablecoin_count <= 25:
        return 'This day is bearish.'
      else:
        return (
            'This day is extremely bearish: Take partial profits on your short'
            ' day trades and look for potential long day trades.'
        )

    elif period_type == 'daily':
      if stablecoin_count < 10:
        return 'This week is not so bearish.'
      elif 10 <= stablecoin_count <= 20:
        return 'Bearishness is kicking in this week.'
      elif 21 <= stablecoin_count <= 25:
        return 'This week is bearish.'
      else:
        return (
            'This week is extremely bearish: Take partial profits on your'
            ' short swing trades and look for potential long swing trades.'
        )

    elif period_type == 'weekly':
      if stablecoin_count < 10:
        return 'This month is not so bearish.'
      elif 10 <= stablecoin_count <= 20:
        return 'Bearishness is kicking in this month.'
      elif 21 <= stablecoin_count <= 25:
        return (
            'This month is bearish: Start researching potential Buy The Dip'
            ' (BTD) coins IF we are in a bull market, and start closing your'
            ' swing short trades.'
        )
      else:
        return (
            'This month is extremely bearish: The altseason is extremely'
            ' bearish. Take partial profits on your swing short trades and use'
            ' the profits to buy the BTC, SOL, and ETH dip that is nearing an'
            ' end; you can go long if you want to.'
        )

  st.subheader('Cryptocurrency Market Report')

  tab_hourly, tab_daily, tab_weekly = st.tabs(
      ['⏱️ Hourly Overview', '📅 Daily Overview', '🗓️ Weekly Overview']
  )

  # TAB 1: HOURLY OVERVIEW
  with tab_hourly:
    col_w, col_l = st.columns(2)

    with col_w:
      #st.subheader('Hourly Winners')
      hourly_winners = df.sort_values(by=['1h'], ascending=False).head(30)
      render_plotly_table(hourly_winners, title='Hourly Winners')
      hourly_bear_msg = evaluate_bearish_sentiment(hourly_winners, 'hourly')
      st.warning(f'**Bearish Sentiment Check:** {hourly_bear_msg}')

    with col_l:
      #st.subheader('Hourly Biggest Losers')
      hourly_losers = df.sort_values(by=['1h'], ascending=True).head(30)
      render_plotly_table(hourly_losers, title='Hourly Biggest Losers')
      hourly_bull_msg = evaluate_bullish_sentiment(hourly_losers, 'hourly')
      st.info(f'**Bullish Sentiment Check:** {hourly_bull_msg}')

  # TAB 2: DAILY OVERVIEW
  with tab_daily:
    col_w, col_l = st.columns(2)

    with col_w:
      #st.subheader("Today's Winners")
      daily_winners = df.sort_values(by=['24h'], ascending=False).head(30)
      render_plotly_table(daily_winners, title="Today's Winners")
      daily_bear_msg = evaluate_bearish_sentiment(daily_winners, 'daily')
      st.warning(f'**Bearish Sentiment Check:** {daily_bear_msg}')

    with col_l:
      #st.subheader("Today's Biggest Losers")
      daily_losers = df.sort_values(by=['24h'], ascending=True).head(30)
      render_plotly_table(daily_losers, title="Today's Biggest Losers")
      daily_bull_msg = evaluate_bullish_sentiment(daily_losers, 'daily')
      st.info(f'**Bullish Sentiment Check:** {daily_bull_msg}')

  # TAB 3: WEEKLY OVERVIEW
  with tab_weekly:
    col_w, col_l = st.columns(2)

    with col_w:
      #st.subheader("This Week's Winners")
      weekly_winners = df.sort_values(by=['7d'], ascending=False).head(30)
      render_plotly_table(weekly_winners, title="This Week's Winners")
      weekly_bear_msg = evaluate_bearish_sentiment(weekly_winners, 'weekly')
      st.warning(f'**Bearish Sentiment Check:** {weekly_bear_msg}')

    with col_l:
      #st.subheader("This Week's Biggest Losers")
      weekly_losers = df.sort_values(by=['7d'], ascending=True).head(30)
      render_plotly_table(weekly_losers, title="This Week's Biggest Losers")
      weekly_bull_msg = evaluate_bullish_sentiment(weekly_losers, 'weekly')
      st.info(f'**Bullish Sentiment Check:** {weekly_bull_msg}')


def my_crypto_portfolio_2028():
    import pandas as pd
    import requests
    import streamlit as st



    # ---------------------------------------------------------
    # 1. PORTFOLIO DATASET (Updated with Static Buy Prices)
    # ---------------------------------------------------------
    PORTFOLIO_DATA = [
        # Core Conviction (Aug 21, 2026)
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "category": "Core / L1",
            "allocation_pct": 10.0,
            "buy_date": "2026-08-21",
            "buy_price": None,  # Handled via CG Historical API or manual entry
            "coingecko_id": "bitcoin",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090734263037497711",
        },
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "category": "Core / L1",
            "allocation_pct": 10.0,
            "buy_date": "2026-08-21",
            "buy_price": None,
            "coingecko_id": "ethereum",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090734263037497711",
        },
        {
            "symbol": "SOL",
            "name": "Solana",
            "category": "Core / L1",
            "allocation_pct": 10.0,
            "buy_date": "2026-08-21",
            "buy_price": None,
            "coingecko_id": "solana",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090734263037497711",
        },
        {
            "symbol": "HYPE",
            "name": "Hyperliquid",
            "category": "Perp DEX / L1",
            "allocation_pct": 10.0,
            "buy_date": "2026-08-21",
            "buy_price": 70.0,
            "coingecko_id": "hyperliquid",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090734263037497711",
        },
        {
            "symbol": "SUI",
            "name": "Sui",
            "category": "Core / L1",
            "allocation_pct": 10.0,
            "buy_date": "2026-08-21",
            "buy_price": None,
            "coingecko_id": "sui",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090734263037497711",
        },
        # Infrastructure & Privacy (Aug 21, 2026)
        {
            "symbol": "TAO",
            "name": "Bittensor",
            "category": "AI / Infra",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 235.0,
            "coingecko_id": "bittensor",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090747208517779640",
        },
        {
            "symbol": "NEAR",
            "name": "NEAR Protocol",
            "category": "Infra / L1",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 2.0,
            "coingecko_id": "near",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090747208517779640",
        },
        {
            "symbol": "CANTON",
            "name": "Canton Network",
            "category": "Infra / Privacy",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.11,
            "coingecko_id": "canton-network",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090747208517779640",
        },
        {
            "symbol": "RAIL",
            "name": "Railgun",
            "category": "Privacy",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 2.2,
            "coingecko_id": "railgun",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090747208517779640",
        },
        {
            "symbol": "ONDO",
            "name": "Ondo Finance",
            "category": "RWA",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.4,
            "coingecko_id": "ondo-finance",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090747208517779640",
        },
        # Speculative & Memes (Aug 21, 2026)
        {
            "symbol": "LIGHTER",
            "name": "Lighter",
            "category": "Speculative",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 3.0,
            "coingecko_id": "lighter",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090750060074000780",
        },
        {
            "symbol": "PUMP",
            "name": "Pump.fun",
            "category": "Meme / Infra",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.003,
            "coingecko_id": "pump-fun",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090750060074000780",
        },
        {
            "symbol": "VVV",
            "name": "Venice AI",
            "category": "AI / Speculative",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 14.4,
            "coingecko_id": "venice-ai",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090750060074000780",
        },
        {
            "symbol": "DOGE",
            "name": "Dogecoin",
            "category": "Meme",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": None,
            "coingecko_id": "dogecoin",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090750060074000780",
        },
        {
            "symbol": "PEPE",
            "name": "Pepe",
            "category": "Meme",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.0000032,
            "coingecko_id": "pepe",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090750060074000780",
        },
        # Bitcoin L2 & Scaling (Aug 21, 2026)
        {
            "symbol": "BOB",
            "name": "Build On Bitcoin",
            "category": "BTC L2",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.004,
            "coingecko_id": "bob-token",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090785987882283095",
        },
        {
            "symbol": "MERL",
            "name": "Merlin Chain",
            "category": "BTC L2",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.021,
            "coingecko_id": "merlin-chain",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090785987882283095",
        },
        {
            "symbol": "FB",
            "name": "Fractal Bitcoin",
            "category": "BTC L2",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.36,
            "coingecko_id": "fractal-bitcoin",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090785987882283095",
        },
        {
            "symbol": "CKB",
            "name": "Nervos Network",
            "category": "BTC L2",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.001,
            "coingecko_id": "nervos-network",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090785987882283095",
        },
        {
            "symbol": "RENDER",
            "name": "Render",
            "category": "DePIN / AI",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 1.5,
            "coingecko_id": "render-token",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090785987882283095",
        },
        # Quantum-Proof & Prediction (Aug 21, 2026)
        {
            "symbol": "QRL",
            "name": "Quantum Resistant Ledger",
            "category": "Quantum-Proof",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.94,
            "coingecko_id": "quantum-resistant-ledger",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090787522779517167",
        },
        {
            "symbol": "ABEL",
            "name": "Abel Finance",
            "category": "Quantum-Proof",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.058,
            "coingecko_id": "abel-finance",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090787522779517167",
        },
        {
            "symbol": "CELL",
            "name": "Cellframe",
            "category": "Quantum-Proof",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.04,
            "coingecko_id": "cellframe",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090787522779517167",
        },
        {
            "symbol": "QANX",
            "name": "QANplatform",
            "category": "Quantum-Proof",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.01,
            "coingecko_id": "qanplatform",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090787522779517167",
        },
        {
            "symbol": "RAIN",
            "name": "Rain Coin",
            "category": "Prediction Market",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.013,
            "coingecko_id": "rain-coin",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090787522779517167",
        },
        {
            "symbol": "DESU",
            "name": "Dexsport",
            "category": "Prediction Market",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.014,
            "coingecko_id": "dexsport",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090787522779517167",
        },
        {
            "symbol": "DRIFT",
            "name": "Drift Protocol",
            "category": "Perp / Prediction",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-21",
            "buy_price": 0.0133,
            "coingecko_id": "drift-protocol",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2090787522779517167",
        },
        # High Performance & Pre-Launch (Aug 22, 2026)
        {
            "symbol": "TRUMP",
            "name": "OFFICIAL TRUMP",
            "category": "Meme",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-22",
            "buy_price": 1.6,
            "coingecko_id": "official-trump",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2091052838063423920",
        },
        {
            "symbol": "MON",
            "name": "Monad",
            "category": "L1",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-22",
            "buy_price": 0.026,
            "coingecko_id": "monad",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2091052838063423920",
        },
        {
            "symbol": "EIGEN",
            "name": "EigenLayer",
            "category": "Restaking",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-22",
            "buy_price": 0.2,
            "coingecko_id": "eigenlayer",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2091052838063423920",
        },
        {
            "symbol": "KALSHI",
            "name": "Kalshi (Pre-Launch)",
            "category": "Prediction Market",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-22",
            "buy_price": None,
            "coingecko_id": "kalshi",
            "is_launched": False,
            "tweet_url": "https://x.com/cipher_ope28850/status/2091052838063423920",
        },
        # Added Positions
        {
            "symbol": "BTR",
            "name": "Bitlayer",
            "category": "BTC L2",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-28",
            "buy_price": 0.05,
            "coingecko_id": "bitlayer",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2098843831244337237",
        },
        {
            "symbol": "MEMECORE",
            "name": "MemeCore",
            "category": "Meme",
            "allocation_pct": 1.0,
            "buy_date": "2026-08-30",
            "buy_price": 1.0,
            "coingecko_id": "memecore",
            "is_launched": True,
            "tweet_url": "https://x.com/cipher_ope28850/status/2099508303281725938",
        },
    ]

    # ---------------------------------------------------------
    # 2. API HELPER FUNCTIONS
    # ---------------------------------------------------------
    @st.cache_data(ttl=3600)
    def fetch_historical_price(coingecko_id, date_str, is_launched):
        if not is_launched:
            return None
        formatted_date = pd.to_datetime(date_str).strftime("%d-%m-%Y")
        url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/history?date={formatted_date}"
        try:
            res = requests.get(url, timeout=5).json()
            return res.get("market_data", {}).get("current_price", {}).get("usd", None)
        except Exception:
            return None


    @st.cache_data(ttl=300)
    def fetch_current_prices(ids):
        ids_str = ",".join(ids)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd"
        try:
            res = requests.get(url, timeout=5).json()
            return {k: v.get("usd", None) for k, v in res.items()}
        except Exception:
            return {}


    # ---------------------------------------------------------
    # 3. INTERFACE & CALCULATIONS
    # ---------------------------------------------------------
    #st.title("🚀 2026-2028 High-Performance Crypto Portfolio Tracker")
    st.caption("Verified trade calls mapped to @cipher_ope28850 X tweets with live CoinGecko pricing.")

    st.sidebar.header("Portfolio Parameters")
    portfolio_size = st.sidebar.number_input(
        "Total Initial Capital ($USD)",
        min_value=1000,
        max_value=10000000,
        value=10000,
        step=1000,
    )

    total_allocated_pct = sum([coin["allocation_pct"] for coin in PORTFOLIO_DATA])
    dry_powder_pct = 20.0
    unallocated_pct = max(0.0, 100.0 - (total_allocated_pct + dry_powder_pct))

    st.sidebar.markdown("---")
    st.sidebar.metric("Allocated Assets", f"{total_allocated_pct:.1f}%")
    st.sidebar.metric("Dry Powder (Reserve)", f"{dry_powder_pct:.1f}%")
    st.sidebar.metric("Unallocated Cash", f"{unallocated_pct:.1f}%")

    df = pd.DataFrame(PORTFOLIO_DATA)

    # Fetch Current Market Data
    cg_ids = [row["coingecko_id"] for row in PORTFOLIO_DATA if row["is_launched"]]
    current_prices = fetch_current_prices(cg_ids)

    buy_prices = []
    live_prices = []

    # Pricing logic fallback to static buy_price if API yields None
    for idx, row in df.iterrows():
        if row["is_launched"]:
            # Fallback priority: static buy_price -> API historical lookup
            if pd.notna(row["buy_price"]):
                h_price = row["buy_price"]
            else:
                h_price = fetch_historical_price(row["coingecko_id"], row["buy_date"], True)
            c_price = current_prices.get(row["coingecko_id"], None)
        else:
            h_price = None
            c_price = None

        buy_prices.append(h_price)
        live_prices.append(c_price)

    df["Buy Price Raw"] = buy_prices
    df["Current Price Raw"] = live_prices

    # Financial Valuation Calculations
    df["Capital ($)"] = (df["allocation_pct"] / 100.0) * portfolio_size

    current_vals = []
    pnl_pcts = []
    pnl_usds = []

    for idx, row in df.iterrows():
        if not row["is_launched"] or pd.isna(row["Buy Price Raw"]):
            current_vals.append(row["Capital ($)"])
            pnl_pcts.append(0.0)
            pnl_usds.append(0.0)
        else:
            units = row["Capital ($)"] / row["Buy Price Raw"]
            c_val = units * row["Current Price Raw"] if pd.notna(row["Current Price Raw"]) else row["Capital ($)"]
            pnl_pct = ((row["Current Price Raw"] - row["Buy Price Raw"]) / row["Buy Price Raw"]) * 100 if pd.notna(row["Current Price Raw"]) else 0.0
            pnl_usd = c_val - row["Capital ($)"]

            current_vals.append(c_val)
            pnl_pcts.append(pnl_pct)
            pnl_usds.append(pnl_usd)

    df["Current Value ($)"] = current_vals
    df["PnL (%)"] = pnl_pcts
    df["PnL ($)"] = pnl_usds

    # Summary Dashboard Metrics
    col1, col2, col3, col4 = st.columns(4)

    total_invested = df["Capital ($)"].sum()
    current_portfolio_val = df["Current Value ($)"].sum()
    dry_powder_val = (dry_powder_pct / 100.0) * portfolio_size
    unallocated_val = (unallocated_pct / 100.0) * portfolio_size

    net_pnl_usd = current_portfolio_val - total_invested
    net_pnl_pct = (net_pnl_usd / total_invested) * 100 if total_invested > 0 else 0.0

    col1.metric("Deployed Capital", f"${total_invested:,.2f}")
    col2.metric("Holdings Value", f"${current_portfolio_val:,.2f}")
    col3.metric("Total Net PnL ($)", f"${net_pnl_usd:,.2f}", delta=f"{net_pnl_pct:.2f}%")
    col4.metric("Dry Powder + Cash", f"${dry_powder_val + unallocated_val:,.2f}")

    st.markdown("---")

    st.subheader("📋 Verified Calls & Asset Performance Table")

    # Formatting output strings for display
    df["Buy Price"] = df.apply(
        lambda r: "Pre-Launch" if not r["is_launched"] else (f"${r['Buy Price Raw']:,.6f}".rstrip('0').rstrip('.') if pd.notna(r["Buy Price Raw"]) else "TBA"),
        axis=1,
    )
    df["Current Price"] = df.apply(
        lambda r: "Pre-Launch" if not r["is_launched"] else (f"${r['Current Price Raw']:,.6f}".rstrip('0').rstrip('.') if pd.notna(r["Current Price Raw"]) else "TBA"),
        axis=1,
    )

    display_df = df[[
        "symbol", "name", "category", "allocation_pct", "buy_date", "tweet_url", 
        "Buy Price", "Current Price", "Capital ($)", "Current Value ($)", "PnL (%)", "PnL ($)"
    ]].copy()

    display_df.columns = [
        "Symbol", "Name", "Sector", "Alloc %", "Buy Date", "Verification Tweet", 
        "Buy Price", "Current Price", "Capital ($)", "Current Value ($)", "PnL (%)", "PnL ($)"
    ]

    st.dataframe(
        display_df,
        column_config={
            "Verification Tweet": st.column_config.LinkColumn("Verification Tweet", display_text="View Call on X ↗"),
            "Alloc %": st.column_config.NumberColumn(format="%.1f%%"),
            "Capital ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Current Value ($)": st.column_config.NumberColumn(format="$%.2f"),
            "PnL (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            "PnL ($)": st.column_config.NumberColumn(format="$%+.2f"),
        },
        use_container_width=True,
        height=600,
        hide_index=True,
    )

    # Visualizations
    st.markdown("---")
    st.subheader("📊 Portfolio Allocations & Visualizations")

    tab1, tab2 = st.tabs(["Sector Breakdown", "Capital Deployment ($)"])

    with tab1:
        sector_df = df.groupby("category")["allocation_pct"].sum().reset_index()
        st.bar_chart(data=sector_df, x="category", y="allocation_pct", color="category")

    with tab2:
        capital_df = df[["symbol", "Capital ($)"]].set_index("symbol")
        st.bar_chart(capital_df)






		
#streamlit run report_lidrisk.py

def social_medialinks():
    import streamlit as st

    st.markdown("### 🌐 Connect & Research Hub")
    st.caption("Feel free to reach out directly or explore published quantitative market research.")

    # ---------------------------------------------------------
    # CONTACT & SOCIAL PROFILES
    # ---------------------------------------------------------
    st.markdown("#### 📱 Direct Contact & Profiles")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.link_button("📞 Call Direct", "tel:+254717150549", use_container_width=True)
    with col2:
        st.link_button("💼 LinkedIn", "https://www.linkedin.com/in/obare-mokua-robert-omae-b58b4a293", use_container_width=True)
    with col3:
        st.link_button("💻 GitHub", "https://github.com/mokuaomae254", use_container_width=True)
    with col4:
        st.link_button("🐦 Twitter / X", "https://x.com/cipher_ope28850", use_container_width=True)
    with col5:
        st.link_button("📺 YouTube", "https://www.youtube.com/channel/UCYpLThwlwwUnGmK5q9YCMhA", use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # DASHBOARDS & LIVE APPLICATIONS
    # ---------------------------------------------------------
    st.markdown("#### ⚡ Live Analytics Platforms")
    
    dash_col1, dash_col2 = st.columns(2)
    
    with dash_col1:
        with st.container(border=True):
            st.markdown("##### 📈 Degen Connect Analytics")
            st.caption("Interactive Streamlit quantitative analytical terminal and market metrics.")
            st.link_button("Launch Dashboard 🚀", "https://degen-connect.streamlit.app/", type="primary", use_container_width=True)

    with dash_col2:
        with st.container(border=True):
            st.markdown("##### 🏆 Crypto Track Record")
            st.caption("Verifiable trade setups, macroeconomic calls, and asset performance tracking.")
            st.link_button("View Track Record 📊", "https://my-crypto-track-record.vercel.app/", type="secondary", use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # PUBLICATIONS & RESEARCH ARTICLES
    # ---------------------------------------------------------
    st.markdown("#### 📑 Published Macro & Quantitative Research")

    publications = [
        {
            "title": "Is Crypto in a Bullish Bear Market? Unveiling the Secrets with Elliott Wave Theory",
            "desc": "Elliott Wave macro framework detailing dynamic impulse structures and cycle phase transitions.",
            "url": "https://medium.com/@omaerobert158/is-crypto-in-a-bullish-bear-market-unveiling-the-secrets-with-elliott-wave-theory-3670119beaf2"
        },
        {
            "title": "Decoding the $100K: Reality or Illusion?",
            "desc": "Quantitative liquidity examination of Bitcoin psychological resistance boundaries and orderflow.",
            "url": "https://medium.com/@omaerobert158/decoding-the-100k-reality-or-illusion-7af8094db98e"
        },
        {
            "title": "Is Bitcoin Leading the Market? How We Called Tops on BTC, SOL, DJIA, NASDAQ & SPX",
            "desc": "Cross-asset correlation analysis evaluating Bitcoin leading indicators against equities indices.",
            "url": "https://medium.com/@omaerobert158/is-bitcoin-leading-the-market-how-we-called-the-tops-on-btc-sol-djia-nasdaq-and-spx-89e9e0e22e5a"
        },
        {
            "title": "The Bitcoin Blueprint: From the $126K Liquidity Trap to the 2026 Macro Bottom 🎯",
            "desc": "Comprehensive macro cycle projection identifying systemic distribution zones and target bottoms.",
            "url": "https://medium.com/@omaerobert158/the-bitcoin-blueprint-from-the-126k-liquidity-trap-to-the-2026-macro-bottom-%EF%B8%8F-d0f4d6ff5854"
        },
        {
            "title": "Is the Crypto Bottom In? The Wyckoff Spring, Macro Divergence & Portfolio Positioning",
            "desc": "Applying Wyckoff accumulation schematics and macro momentum metrics to optimize entry sizing.",
            "url": "https://medium.com/@omaerobert158/is-the-crypto-bottom-in-the-wyckoff-spring-macro-divergence-and-my-portfolio-positioning-7786bbf44439"
        }
    ]

    # Render publications into a clean 2-column card layout
    pub_col1, pub_col2 = st.columns(2)
    for idx, item in enumerate(publications):
        target_col = pub_col1 if idx % 2 == 0 else pub_col2
        with target_col:
            with st.container(border=True):
                st.markdown(f"**{item['title']}**")
                st.caption(item["desc"])
                st.link_button("Read Article 📖", item["url"], use_container_width=True)


                




def investor_connect2():
		import streamlit as st
		import matplotlib.pyplot as plt
		from PIL import Image

		st.header("Investor Connect")
		st.text("Share your charts below")
		username = st.text_input("Enter your username")
		caption = st.text_input("What is the chart about")
		uploaded_files = st.file_uploader("Choose one or more files", accept_multiple_files=True)



		if uploaded_files is not None:
			
			for uploaded_file in uploaded_files:
				st.write("Posted by " + username)
				image = Image.open(uploaded_file)
				st.image(image, caption=caption)

		#streamlit run investor_connect2.py



def altcoinseason():
    import pandas as pd
    import streamlit as st
    import plotly.graph_objects as go

    st.subheader("Altcoin Season Indicator")

    try:
        dataframe = pd.read_csv("coingecko-crypto-data.csv")
    except FileNotFoundError:
        st.error("Data file 'coingecko-crypto-data.csv' not found.")
        return

    stablecoins = [
        'Tether',
        'USDC',
        'USDS',
        'Dai',
        'USD1',
        'Ethena USDe',
        'Global Dollar',
        'BlackRock USD Institutional Digital Liquidity Fund',
        'PayPal USD',
        'Ripple USD',
        'USDD',
        'Falcon USD',
        'BFUSD',
        'United Stables',
        'USDGO',
        'GHO',
        'YLDS',
        'Usual USD',
        'Figure Heloc',
        'Circle USYC',
        'Tether Gold',
        'Ondo US Dollar Yield',
        'PAX Gold',
        'Spiko Amundi Overnight Swap Fund (EUR)',
        'Spiko EU T-Bills Money Market Fund',
        'Janus Henderson Anemoy Treasury Fund',
        'Invesco Short Duration US Government Securities Fund',
        'Janus Henderson Anemoy AAA CLO Fund',
    ]
    
    # Filter out stablecoins
    dataframe = dataframe[~dataframe['Coin'].isin(stablecoins)].reset_index(drop=True)

    if dataframe.empty:
        st.error("Dataframe is empty after filtering stablecoins.")
        return

    top_99 = dataframe.head(99).copy()

    # Check for Bitcoin row safely
    bitcoin_row = top_99[top_99["Coin"].str.contains("Bitcoin", case=False, na=False)]
    if bitcoin_row.empty:
        bitcoin_24H_perc = top_99.iloc[0]["1h"]
    else:
        bitcoin_24H_perc = bitcoin_row.iloc[0]["1h"]

    # Controls
    col_sel, col_space = st.columns([1, 2])
    with col_sel:
        timeframe = st.selectbox("Select Timeframe:", ["Hourly", "Daily", "Weekly"])

    timeframe_map = {"Hourly": "1h", "Daily": "24h", "Weekly": "7d"}
    selected_column = timeframe_map[timeframe]

    # Calculate outperforms metric
    top_99["Difference"] = top_99[selected_column] - bitcoin_24H_perc
    top_99["Outperforms"] = top_99["Difference"] > 0
    outperformers = top_99["Outperforms"].sum()
    percent_outperform = (outperformers / len(top_99)) * 100

    # Layout for Gauge and Strategy Output
    col_chart, col_action = st.columns([1.2, 1])

    with col_chart:
        # Plotly Semi-Circle Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=percent_outperform,
            number={"suffix": "%", "font": {"size": 36, "color": "#00E676"}},
            title={"text": f"Altcoin Outperformance ({timeframe})", "font": {"size": 16, "color": "#FFFFFF"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#888888"},
                "bar": {"color": "#00E676"},
                "steps": [
                    {"range": [0, 25], "color": "#1E222D"},
                    {"range": [25, 75], "color": "#2A2E39"},
                    {"range": [75, 100], "color": "#363C4E"}
                ],
            }
        ))
        fig_gauge.update_layout(
            height=280,
            margin=dict(l=30, r=30, t=50, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"}
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_action:
        st.subheader("Market Strategy Insight")
        if 95 < percent_outperform <= 100:
            st.error("🚨 **Extreme Alt Season:** Altcoins are heavily overvalued on this timeframe. Take profits aggressively into Stablecoins, BTC, and ETH.Take some shorts also on altcoins.")
        elif 90 < percent_outperform <= 95:
            st.warning("⚠️ **High Alt Season:** Scale out of altcoins and take partial profits into BTC, ETH, and Stablecoins.")
        elif 80 < percent_outperform <= 90:
            st.info("🔍 **Local Top Warning:** Research coins reaching local tops for potential shorting or hedging opportunities.")
        elif 10 < percent_outperform <= 20:
            st.info("🎯 **Accumulation Zone:** Altcoins reaching local bottoms. Consider building DCA positions gradually.")
        elif 5 < percent_outperform <= 10:
            st.success("🔄 **Rotation Signal:** Consider rotating profits from BTC into high-conviction altcoins.")
        elif 1 < percent_outperform <= 5:
            st.success("💎 **Extreme Undervaluation:** Altcoins are deeply undervalued relative to BTC. Deploy stablecoins into strong altcoin projects. Take some longs on altcoins.")
        else:
            # FIXED: Replaced st.secondary with st.info
            st.info("✊ **Hold Position:** Market is balanced between BTC and Altcoin momentum in this timeframe. Maintain current allocation.")



def crypto_portfolio():
    import streamlit as st
    import plotly.graph_objects as go

    st.subheader("Crypto Portfolio Sizing")

    col_in, col_out = st.columns([1, 1.2])

    with col_in:
        income = st.number_input(
            "Enter your annual income ($):", 
            min_value=0, 
            value=50000, 
            step=1000, 
            format="%d"
        )
        investment = income * 0.10

        if income >= 1000:
            st.success(f"Recommended 10% Crypto Allocation: **${investment:,.2f}** / year")
        elif income > 0:
            st.warning("Minimum recommended trade execution size on most exchanges is $10 USD.")
        else:
            st.caption("Please enter an annual income greater than $0 to calculate sizing.")

    with col_out:
        if income > 2000000:
            st.error("👑 **Accredited Investor Status:** Consult with private wealth managers, hedge funds, or VC firms for custom mandate structuring.")
        elif income >= 1000:
            # Dynamic size logic
            if income <= 1000:
                sizes = [20, 15, 15, 20, 10, 20]
            elif income <= 10000:
                sizes = [25, 10, 15, 20, 10, 20]
            elif income <= 100000:
                sizes = [30, 10, 15, 15, 10, 20]
            elif income <= 1000000:
                sizes = [35, 15, 10, 10, 10, 20]
            else:
                sizes = [40, 10, 10, 10, 10, 20]

            labels = ['Layer 1', 'Quantum resistance & prediction markets', 'BTC L2 & DePIN', 'AI,privacy & RWA', 'Meme', 'Stablecoins']
            colors = ['#00E676', '#FF9800', '#29B6F6', '#AB47BC', '#EC407A', '#FFD700']

            # Clean Plotly Donut Chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels, 
                values=sizes, 
                hole=0.45,
                marker=dict(colors=colors),
                textinfo='label+percent',
                textfont=dict(size=11, color='#FFFFFF')
            )])

            fig_pie.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )

            st.plotly_chart(fig_pie, use_container_width=True)



		


import io
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


def render_plotly_table(df: pd.DataFrame, title: str = ''):
  """Renders a dataframe as a Plotly Table with a PNG camera icon download button."""
  fig = go.Figure(
      data=[
          go.Table(
              header=dict(
                  values=[f'<b>{col}</b>' for col in df.columns],
                  fill_color='#1E222D',
                  font=dict(color='white', size=13),
                  align='left',
                  height=35,
              ),
              cells=dict(
                  values=[df[col] for col in df.columns],
                  fill_color='#131722',
                  font=dict(color='#D1D4DC', size=12),
                  align='left',
                  height=30,
              ),
          )
      ]
  )

  fig.update_layout(
      title=dict(text=title, font=dict(size=18, color='white')),
      margin=dict(l=10, r=10, t=40, b=10),
      paper_bgcolor='rgba(0,0,0,0)',
      plot_bgcolor='rgba(0,0,0,0)',
      height=min(600, 50 + len(df) * 32),
  )

  st.plotly_chart(
      fig,
      use_container_width=True,
      config={
          'displayModeBar': True,
          'toImageButtonOptions': {
              'format': 'png',
              'filename': f'{title.lower().replace(" ", "_")}_dataset',
              'height': 800,
              'width': 1200,
              'scale': 2,
          },
          'modeBarButtonsToRemove': [
              'zoom2d',
              'pan2d',
              'select2d',
              'lasso2d',
              'zoomIn2d',
              'zoomOut2d',
              'autoScale2d',
              'resetScale2d',
          ],
          'displaylogo': False,
      },
  )


def scrapping_coingeckoAPI():
  

  import pandas as pd
  import requests
  from Degen_connect_test import render_plotly_table, topcryptos
  import streamlit as st

  STABLECOINS = {
      'Tether',
      'USDC',
      'USDS',
      'Dai',
      'USD1',
      'Ethena USDe',
      'Global Dollar',
      'BlackRock USD Institutional Digital Liquidity Fund',
      'PayPal USD',
      'Ripple USD',
      'USDD',
      'Falcon USD',
      'BFUSD',
      'United Stables',
      'USDGO',
      'GHO',
      'YLDS',
      'Usual USD',
      'Figure Heloc',
      'Circle USYC',
      'Tether Gold',
      'Ondo US Dollar Yield',
      'PAX Gold',
      'Spiko Amundi Overnight Swap Fund (EUR)',
      'Spiko EU T-Bills Money Market Fund',
      'Janus Henderson Anemoy Treasury Fund',
      'Invesco Short Duration US Government Securities Fund',
      'Janus Henderson Anemoy AAA CLO Fund',
  }


  def classify_liquidity(row):
    if row['Coin'] in STABLECOINS:
      return 'stablecoin'
    vol = row['24h Volume']
    mcap = row['Market Cap']
    if pd.isna(vol) or pd.isna(mcap) or mcap == 0:
      return 'unknown'
    ratio = vol / mcap
    if ratio < 0.05:
      return 'illiquid'
    elif ratio <= 0.10:
      return 'fairly liquid'
    elif ratio <= 0.30:
      return 'highly liquid'
    elif ratio <= 0.50:
      return 'limited long term potential'
    return 'stay off'


  @st.cache_data(ttl=300)
  def fetch_market_data(page=1, per_page=100):
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': per_page,
        'page': page,
        'sparkline': 'false',
        'price_change_percentage': '1h,24h,7d',
    }
    headers = {'Accept': 'application/json', 'User-Agent': 'DegenAlpha/1.0'}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    df = pd.DataFrame([
        {
            '#': item.get('market_cap_rank'),
            'Coin': item.get('name'),
            'Price': item.get('current_price'),
            '1h': round(item.get('price_change_percentage_1h_in_currency') or 0, 2),
            '24h': round(
                item.get('price_change_percentage_24h_in_currency') or 0, 2
            ),
            '7d': round(item.get('price_change_percentage_7d_in_currency') or 0, 2),
            '24h Volume': item.get('total_volume'),
            'Market Cap': item.get('market_cap'),
        }
        for item in data
    ])
    df['liquidity_risk'] = df.apply(classify_liquidity, axis=1)
    return df


  def load_crypto_table():
    try:
      # Change page=1 for ranks 1-100, or page=2 for ranks 101-200
      df = fetch_market_data(page=1, per_page=100)
      df.to_csv('coingecko-crypto-data.csv', index=False)
      render_plotly_table(
          df, title='Top Cryptocurrencies & Liquidity Analysis (Live Data)'
      )
    except Exception as e:
      st.warning(f'⚠️ Live API failed ({e}). Displaying fallback data.')
      topcryptos()


  # Make sure you actually call the function in your app flow!
  load_crypto_table()


  #streamlit run coingecko_scrappingAPI.py



def scrapping():
  try:
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
    }

    url = 'https://www.coingecko.com/en?page=2'
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')

    parsed_data = []

    if table:
      rows = table.find_all('tr')

      for row in rows:
        cols = row.find_all('td')

        if len(cols) < 8:
          continue

        # Filter out 'Buy' / 'Trade' action cells
        filtered_cols = [
            c
            for c in cols
            if c.text.strip().lower() not in ['buy', 'trade', '']
        ]

        if len(filtered_cols) < 7:
          continue

        # 1. Rank & Coin Name
        rank = filtered_cols[0].text.strip()

        coin_raw = filtered_cols[1].text.strip()
        coin_lines = [
            line.strip()
            for line in coin_raw.split('\n')
            if line.strip() and line.strip().lower() not in ['buy', 'trade']
        ]
        coin_name = coin_lines[0] if coin_lines else 'Unknown'

        # 2. Price
        price_raw = filtered_cols[2].text.strip()
        price_clean = re.sub(r'[^\d.]', '', price_raw.replace(',', ''))

        # Percentage parser (1h, 24h, 7d)
        def parse_pct_cell(cell):
          if not cell:
            return 0.0

          text_val = cell.text.strip()
          cell_html = str(cell).lower()

          clean_num = re.sub(r'[^\d.]', '', text_val)
          if not clean_num:
            return 0.0

          try:
            val = float(clean_num)
          except ValueError:
            return 0.0

          has_down_indicator = (
              'caret-down' in cell_html
              or 'down-icon' in cell_html
              or '▼' in text_val
              or '-' in text_val
              or 'fe-chevron-down' in cell_html
          )

          has_up_indicator = (
              'caret-up' in cell_html
              or 'up-icon' in cell_html
              or '▲' in text_val
              or '+' in text_val
              or 'fe-chevron-up' in cell_html
              or 'text-green' in cell_html
              or 'green' in cell_html
          )

          if has_down_indicator and not has_up_indicator:
            return -val
          return val

        p_1h = parse_pct_cell(filtered_cols[3])
        p_24h = parse_pct_cell(filtered_cols[4])
        p_7d = parse_pct_cell(filtered_cols[5])

        # 3. Dynamic Lookup for 24h Volume and Market Cap ($ amounts)
        dollar_values = []
        for c in filtered_cols[6:]:
          txt = c.text.strip()
          if '$' in txt or (
              re.search(r'\d{1,3}(,\d{3})+', txt) and '%' not in txt
          ):
            clean_val = re.sub(r'[^\d.]', '', txt.replace(',', ''))
            try:
              dollar_values.append(float(clean_val))
            except ValueError:
              pass

        vol_clean = dollar_values[0] if len(dollar_values) >= 1 else 0.0
        mcap_clean = dollar_values[1] if len(dollar_values) >= 2 else 0.0

        parsed_data.append({
            '#': rank,
            'Coin': coin_name,
            'Price': float(price_clean) if price_clean else 0.0,
            '1h': p_1h,
            '24h': p_24h,
            '7d': p_7d,
            '24h Volume': vol_clean,
            'Market Cap': mcap_clean,
        })

    df = pd.DataFrame(parsed_data)

    # 4. Compute Volume/Mcap Liquidity Risk
    liquidity_risk = []
    for idx in df.index:
      vol = df.loc[idx, '24h Volume']
      mcap = df.loc[idx, 'Market Cap']

      if pd.isna(vol) or pd.isna(mcap) or mcap == 0:
        liquidity_risk.append('unknown')
      elif vol < (mcap * 0.05):
        liquidity_risk.append('illiquid')
      elif vol <= (mcap * 0.1):
        liquidity_risk.append('fairly liquid')
      elif vol <= (mcap * 0.3):
        liquidity_risk.append('highly liquid')
      elif vol <= (mcap * 0.5):
        liquidity_risk.append('limited long term potential')
      else:
        liquidity_risk.append('stay off')

    df['liquidity_risk'] = liquidity_risk

    # 5. STABLECOIN OVERRIDE
    stablecoins = [
        'Tether',
        'USDC',
        'USDS',
        'Dai',
        'USD1',
        'Ethena USDe',
        'Global Dollar',
        'BlackRock USD Institutional Digital Liquidity Fund',
        'PayPal USD',
        'Ripple USD',
        'USDD',
        'Falcon USD',
        'BFUSD',
        'United Stables',
        'USDGO',
        'GHO',
        'YLDS',
        'Usual USD',
        'Figure Heloc',
        'Circle USYC',
        'Tether Gold',
        'Ondo US Dollar Yield',
        'PAX Gold',
        'Spiko Amundi Overnight Swap Fund (EUR)',
        'Spiko EU T-Bills Money Market Fund',
        'Janus Henderson Anemoy Treasury Fund',
        'Invesco Short Duration US Government Securities Fund',
        'Janus Henderson Anemoy AAA CLO Fund',
    ]

    df.loc[df['Coin'].isin(stablecoins), 'liquidity_risk'] = 'stablecoin'

    # Save clean dataset locally
    df.to_csv('coingecko-crypto-data.csv', index=False)

    # Display dataset as Plotly Table with Camera PNG export
    render_plotly_table(
        df, title='Top Cryptocurrencies & Liquidity Analysis (Live Data)'
    )

  except Exception as e:
    st.warning('⚠️ Live scraping failed or blocked. Displaying fallback data.')
    topcryptos()





def scrapping1():
  try:
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
    }

    url = 'https://www.coingecko.com/en?page=2'
    r = requests.get(url, headers=headers, timeout=8)
    r.raise_for_status()

    df = pd.read_html(io.StringIO(r.text))[0]

    df = df[['#','Coin', 'Price', '1h', '24h', '7d', '24h Volume', 'Market Cap']]

    df['Coin'] = df['Coin'].apply(
        lambda x: str(x).split(' \xa0')[0].split('  ')[0]
    )
    df['Price'] = df['Price'].apply(
        lambda x: str(x).replace(',', '').replace('$', '')
    )
    df['Market Cap'] = df['Market Cap'].apply(
        lambda x: str(x).replace(',', '').replace('$', '')
    )
    df['Market Cap'] = pd.to_numeric(df['Market Cap'], errors='coerce').abs()

    df['24h Volume'] = (
        df['24h Volume'].astype(str).str.replace(',', '').str.replace('$', '')
    )
    df['24h Volume'] = pd.to_numeric(df['24h Volume'], errors='coerce').abs()

    df['1h'] = pd.to_numeric(
        df['1h'].astype(str).str.replace('%', ''), errors='coerce'
    )
    df['24h'] = pd.to_numeric(
        df['24h'].astype(str).str.replace('%', ''), errors='coerce'
    )
    df['7d'] = pd.to_numeric(
        df['7d'].astype(str).str.replace('%', ''), errors='coerce'
    )

    df.to_csv('coingecko-crypto-data.csv', index=False)

    liquidity_risk = []
    for index in df.index:
      vol = df['24h Volume'][index]
      mcap = df['Market Cap'][index]

      if pd.isna(vol) or pd.isna(mcap) or mcap == 0:
        liquidity_risk.append('unknown')
      elif vol < (mcap * 0.05):
        liquidity_risk.append('illiquid')
      elif vol <= (mcap * 0.1):
        liquidity_risk.append('fairly liquid')
      elif vol <= (mcap * 0.3):
        liquidity_risk.append('highly liquid')
      elif vol <= (mcap * 0.5):
        liquidity_risk.append('limited long term potential')
      else:
        liquidity_risk.append('stay off')

    df['liquidity_risk'] = liquidity_risk

    stablecoins = [
        'Tether',
        'USDC',
        'USDS',
        'Dai',
        'USD1',
        'Ethena USDe',
        'Global Dollar',
        'BlackRock USD Institutional Digital Liquidity Fund',
        'PayPal USD',
        'Ripple USD',
        'USDD',
        'Falcon USD',
        'BFUSD',
        'United Stables',
        'USDGO',
        'GHO',
        'YLDS',
        'Usual USD',
        'Figure Heloc',
        'Circle USYC',
        'Tether Gold',
        'Ondo US Dollar Yield',
        'PAX Gold',
        'Spiko Amundi Overnight Swap Fund (EUR)',
        'Spiko EU T-Bills Money Market Fund',
        'Janus Henderson Anemoy Treasury Fund',
        'Invesco Short Duration US Government Securities Fund',
        'Janus Henderson Anemoy AAA CLO Fund',
    ]
    df.loc[df['Coin'].isin(stablecoins), 'liquidity_risk'] = 'stablecoin'

    # Display dataset as Plotly Table with Camera PNG export
    render_plotly_table(
        df, title='Top Cryptocurrencies & Liquidity Analysis (Live Data)'
    )

  except Exception as e:
    st.warning('⚠️ Live scraping failed or blocked. Displaying fallback data.')
    topcryptos()


def topcryptos():
  try:
    df = pd.read_csv('coingecko-crypto-data.csv')
    df = df[['Coin', 'Price', '1h', '24h', '7d', '24h Volume', 'Market Cap']]

    liquidity_risk = []
    for index in df.index:
      vol = df['24h Volume'][index]
      mcap = df['Market Cap'][index]

      if pd.isna(vol) or pd.isna(mcap) or mcap == 0:
        liquidity_risk.append('unknown')
      elif vol < (mcap * 0.05):
        liquidity_risk.append('illiquid')
      elif vol <= (mcap * 0.1):
        liquidity_risk.append('fairly liquid')
      elif vol <= (mcap * 0.3):
        liquidity_risk.append('highly liquid')
      elif vol <= (mcap * 0.5):
        liquidity_risk.append('limited long term potential')
      else:
        liquidity_risk.append('stay off')

    df['liquidity_risk'] = liquidity_risk

    stablecoins = [
        'Tether',
        'USDC',
        'USDS',
        'Dai',
        'USD1',
        'Ethena USDe',
        'Global Dollar',
        'BlackRock USD Institutional Digital Liquidity Fund',
        'PayPal USD',
        'Ripple USD',
        'USDD',
        'Falcon USD',
        'BFUSD',
        'United Stables',
        'USDGO',
        'GHO',
        'YLDS',
        'Usual USD',
        'Figure Heloc',
        'Circle USYC',
        'Tether Gold',
        'Ondo US Dollar Yield',
        'PAX Gold',
        'Spiko Amundi Overnight Swap Fund (EUR)',
        'Spiko EU T-Bills Money Market Fund',
        'Janus Henderson Anemoy Treasury Fund',
        'Invesco Short Duration US Government Securities Fund',
        'Janus Henderson Anemoy AAA CLO Fund',
    ]
    df.loc[df['Coin'].isin(stablecoins), 'liquidity_risk'] = 'stablecoin'

    # Display dataset as Plotly Table with Camera PNG export
    render_plotly_table(
        df, title='Top Cryptocurrencies & Liquidity Analysis (Static Data)'
    )

  except FileNotFoundError:
    st.error(
        '❌ Failed to fetch live data and local dataset'
        ' (coingecko-crypto-data.csv) was not found.'
    )




import json
import re
import sqlite3
import urllib.request
from datetime import datetime, time, timedelta

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

DB_FILE = "consultations.db"
RECIPIENT_WALLET = "0x1560fE2D29b86a0B0040e96545bDe4531E3feBD3".lower()
TRANSFER_EVENT_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)


# ==========================================
# DATABASE INITIALIZATION & QUERIES
# ==========================================
def init_sqlite_db():
    """Initialize SQLite database for storing EVM consultation bookings."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            service_type TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            portfolio_size TEXT,
            trading_experience TEXT,
            consultation_topics TEXT,
            notes TEXT,
            payment_network TEXT,
            payment_currency TEXT,
            amount_usd REAL,
            tx_hash TEXT UNIQUE NOT NULL,
            tx_status TEXT DEFAULT 'Pending Verification',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


def save_booking(data):
    """Save verified client booking into database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO bookings (
                client_name, email, phone, service_type,
                booking_date, booking_time, portfolio_size,
                trading_experience, consultation_topics, notes,
                payment_network, payment_currency, amount_usd, tx_hash, tx_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["name"],
                data["email"],
                data["phone"],
                data["service"],
                data["date"].strftime("%Y-%m-%d"),
                data["time"].strftime("%H:%M"),
                data["portfolio_size"],
                data["trading_experience"],
                ", ".join(data["topics"]),
                data["notes"],
                data["payment_network"],
                data["payment_currency"],
                data["amount_usd"],
                data["tx_hash"],
                data["tx_status"],
            ),
        )
        conn.commit()
        success = True
        msg = "Booking successfully registered!"
    except sqlite3.IntegrityError:
        success = False
        msg = "⚠️ This Transaction Hash has already been submitted for a previous booking."
    finally:
        conn.close()

    return success, msg


def get_existing_bookings(selected_date):
    """Retrieve booked time slots for a given date."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT booking_time FROM bookings WHERE booking_date = ?",
        (selected_date.strftime("%Y-%m-%d"),),
    )
    booked_slots = [row[0] for row in cursor.fetchall()]
    conn.close()
    return booked_slots


def get_all_bookings_df():
    """Fetch all bookings from SQLite into a Pandas DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT * FROM bookings ORDER BY booking_date DESC, booking_time ASC",
        conn,
    )
    conn.close()
    return df


# ==========================================
# ON-CHAIN EVM VERIFICATION LOGIC
# ==========================================
def rpc_post(rpc_url: str, method: str, params: list) -> dict:
    """Send a JSON-RPC request to an EVM RPC node using urllib."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        rpc_url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def verify_evm_payment(
    rpc_url: str,
    tx_hash: str,
    expected_wallet: str,
    expected_amount_usd: float,
    token_decimals: int = 6,
) -> tuple[bool, str]:
    """Verify an EVM ERC-20 token transfer transaction on-chain."""
    if not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
        return False, "Invalid EVM transaction hash format."

    try:
        res = rpc_post(rpc_url, "eth_getTransactionReceipt", [tx_hash])
        receipt = res.get("result")

        if not receipt:
            return (
                False,
                "Transaction receipt not found or still pending in mempool.",
            )

        if receipt.get("status") != "0x1":
            return False, "Transaction was reverted or failed on-chain."

        clean_expected_wallet = expected_wallet.lower().replace("0x", "")
        padded_expected_wallet = f"0x{clean_expected_wallet.zfill(64)}".lower()

        valid_transfer_found = False
        amount_transferred = 0.0

        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if len(topics) >= 3:
                event_sig = topics[0].lower()
                recipient_topic = topics[2].lower()

                if (
                    event_sig == TRANSFER_EVENT_TOPIC
                    and recipient_topic == padded_expected_wallet
                ):
                    data_hex = log.get("data", "0x0")
                    raw_value = (
                        0 if data_hex == "0x" else int(data_hex, 16)
                    )
                    amount_transferred = raw_value / (10**token_decimals)
                    valid_transfer_found = True
                    break

        if not valid_transfer_found:
            return (
                False,
                f"Transaction did not contain an ERC-20 transfer to receiver {expected_wallet}.",
            )

        if amount_transferred < (expected_amount_usd * 0.99):
            return (
                False,
                f"Insufficient transfer amount: received {amount_transferred:.2f}, required {expected_amount_usd:.2f}.",
            )

        return (
            True,
            f"Verified successfully! Transfer of {amount_transferred:.2f} tokens confirmed.",
        )

    except Exception as e:
        return False, f"RPC Verification Error: {str(e)}"


# ==========================================
# ADMIN DASHBOARD INTERFACE (mokua254)
# ==========================================
def admin_dashboard():
    """Custom UI/UX for Administrator (mokua254)."""
    st.title("🛡️ Admin Dashboard | Consultation Management")
    st.caption("Welcome back, **mokua254**. Here are your upcoming consultations and verified client details.")

    df = get_all_bookings_df()

    if df.empty:
        st.info("No consultation bookings registered yet.")
        return

    # Overview Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Bookings", len(df))
    m2.metric("Total Revenue (USD)", f"${df['amount_usd'].sum():,.2f}")
    m3.metric("Verified Txns", len(df[df["tx_status"] == "Verified On-Chain"]))
    m4.metric("Unique Clients", df["email"].nunique())

    st.markdown("---")

    # Filter Controls
    col_search, col_filter = st.columns([2, 1])
    search_query = col_search.text_input("🔍 Search Client Name, Email, or Tx Hash")
    selected_status = col_filter.selectbox("Filter Status", ["All"] + list(df["tx_status"].unique()))

    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df["client_name"].str.contains(search_query, case=False, na=False)
            | filtered_df["email"].str.contains(search_query, case=False, na=False)
            | filtered_df["tx_hash"].str.contains(search_query, case=False, na=False)
        ]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["tx_status"] == selected_status]

    # Detailed Client Cards
    st.subheader("📋 Scheduled Client Appointments")
    
    for idx, row in filtered_df.iterrows():
        with st.expander(
            f"🗓️ {row['booking_date']} @ {row['booking_time']} EAT — {row['client_name']} ({row['service_type']})"
        ):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 👤 Client Information")
                st.write(f"**Name:** {row['client_name']}")
                st.write(f"**Email:** {row['email']}")
                st.write(f"**Phone / Telegram:** {row['phone'] if row['phone'] else 'N/A'}")
                st.write(f"**Portfolio Size:** {row['portfolio_size']}")
                st.write(f"**Trading Experience:** {row['trading_experience']}")

            with c2:
                st.markdown("##### 💳 Payment & Session Focus")
                st.write(f"**Amount Paid:** ${row['amount_usd']:.2f} USD ({row['payment_currency']} via {row['payment_network']})")
                st.write(f"**Tx Hash:** `{row['tx_hash']}`")
                st.write(f"**Verification Status:** ✅ `{row['tx_status']}`")
                st.write(f"**Key Topics:** {row['consultation_topics']}")

            st.markdown("**Client Goals / Specific Notes:**")
            st.info(row["notes"] if row["notes"] else "No specific notes provided.")

    # Data Table View & Export
    st.markdown("---")
    st.subheader("📊 Master Ledger Table")
    st.dataframe(filtered_df, use_container_width=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Ledger to CSV",
        data=csv_data,
        file_name=f"consultations_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


# ==========================================
# CLIENT BOOKING INTERFACE (PUBLIC)
# ==========================================
def client_booking_interface():
    """Standard Booking UI/UX for Public Clients."""
    st.title("📅 Schedule Your EVM Strategy Consultation")
    st.caption("Select your consultation service, choose an available time slot, and confirm via on-chain EVM payment.")

    with st.form("booking_form", clear_on_submit=False):
        col1, col2 = st.columns([1, 1], gap="large")

        # Column 1: Service & Schedule
        with col1:
            st.markdown("### 1. Select Consultation & Schedule")

            services = {
                "Crypto Market Analysis & Strategy (45 min)": 150,
                "Trading Psychology & Risk Management (45 min)": 100,
                "Quantitative Trading & Algo Setup (60 min)": 250,
                "Portfolio Risk Audit & DeFi Advisory (60 min)": 200,
            }

            selected_service = st.selectbox(
                "Consultation Type", list(services.keys())
            )
            service_price = services[selected_service]
            st.info(f"**Fee:** ${service_price} USD")

            today = datetime.now().date()
            max_date = today + timedelta(days=30)
            booking_date = st.date_input(
                "Choose Date", min_value=today, max_value=max_date
            )

            all_slots = [
                time(9, 0),
                time(10, 30),
                time(13, 0),
                time(14, 30),
                time(16, 0),
            ]
            booked_times = get_existing_bookings(booking_date)
            available_slots = [
                t for t in all_slots if t.strftime("%H:%M") not in booked_times
            ]

            if available_slots:
                booking_time = st.selectbox(
                    "Available Time Slot (EAT)",
                    available_slots,
                    format_func=lambda x: x.strftime("%I:%M %p"),
                )
            else:
                st.error("No slots available on this date.")
                booking_time = None

            st.markdown("---")
            st.markdown("### 2. Client Details")
            client_name = st.text_input("Full Name *", key="client_name_input")
            email = st.text_input("Email Address *", key="email_input")
            phone = st.text_input("Phone Number / Telegram Handle")

            portfolio_size = st.selectbox(
                "Approximate Portfolio Size",
                ["< $10k", "$10k - $50k", "$50k - $250k", "$250k+"],
            )

            trading_exp = st.select_slider(
                "Trading Experience Level",
                options=[
                    "Beginner",
                    "Intermediate",
                    "Advanced",
                    "Institutional",
                ],
            )

            topics = st.multiselect(
                "Primary Topics to Cover",
                [
                    "Technical Analysis (Elliott Wave / Wyckoff)",
                    "Automated Trading & Execution APIs",
                    "Perpetuals & Derivatives Strategy",
                    "DeFi Liquidity Provisioning",
                    "Risk Management & Hedging",
                    "Trading Psychology & Risk Management",
                ],
            )
            notes = st.text_area("Specific Goals for the Session")

        # Column 2: Payment & Proof
        with col2:
            st.markdown("### 3. Payment & Transaction Proof")

            network_payment_options = {
                "BNB CHAIN": ["BUSD", "USDT", "USDC"],
                "BASE": ["USDBC", "USDC"],
                "POLYGON": ["USDC", "DAI", "USDT"],
                "OPTIMISM": ["USDC", "USDT"],
                "AVALANCHE": ["EUROC", "USDC", "USDT"],
                "ETHEREUM": ["USDC", "USDT", "DAI"],
            }

            network_options = list(network_payment_options.keys())
            selected_network = st.selectbox("Choose Network:", network_options)
            payment_options = network_payment_options.get(selected_network, [])

            if payment_options:
                selected_payment_option = st.selectbox(
                    "Choose Settlement Token:", payment_options
                )
                receiver_address = "0x1560fE2D29b86a0B0040e96545bDe4531E3feBD3"

                st.write(f"**Amount Due:** ${service_price} USD")

                html_code = f"""
                <div style="display: flex; flex-direction: column; align-items: center; background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0;">
                    <script src="https://button.getpip.com/cdn/pipbutton.js"></script>
                    <div class="pip-button"
                        data-amount="{service_price}"
                        data-chainNetwork="{selected_network}"
                        data-currency="{selected_payment_option}"
                        data-label="PAY WITH CRYPTO"
                        data-useLabel="true"
                        data-receiver="{receiver_address}"
                        data-buttonColor="#1149FF"
                        data-buttonTextColor="#FFFFFF"
                        data-memo="{receiver_address}">
                    </div>
                    <p style="margin-top: 10px; font-size: 11px; color: #6c757d; text-align: center;">
                        Deposit EVM Address: <br><code>{receiver_address}</code>
                    </p>
                </div>
                """
                components.html(html_code, height=180)

                st.markdown("#### 4. Confirm Payment")
                tx_hash_input = st.text_input(
                    "Transaction Hash *",
                    placeholder="Paste EVM Tx Hash (starts with 0x...)",
                    help="Copy and paste the transaction hash generated by your wallet after completing the transfer.",
                    key="tx_hash_input",
                )

                submitted = st.form_submit_button("Submit Booking & Verify Proof")

                if submitted:
                    if not client_name.strip() or not email.strip():
                        st.error("Please provide your Name and Email.")
                    elif not booking_time:
                        st.error("Please pick an available time slot.")
                    elif not tx_hash_input.strip():
                        st.error("Please paste your Transaction Hash proof.")
                    else:
                        rpc_endpoints = {
                            "ETHEREUM": "https://eth.llamarpc.com",
                            "BNB CHAIN": "https://binance.llamarpc.com",
                            "POLYGON": "https://polygon.llamarpc.com",
                            "BASE": "https://mainnet.base.org",
                            "OPTIMISM": "https://mainnet.optimism.io",
                            "AVALANCHE": "https://api.avax.network/ext/bc/C/rpc",
                        }
                        rpc_url = rpc_endpoints.get(
                            selected_network.upper(), "https://eth.llamarpc.com"
                        )

                        token_decimals = (
                            6
                            if selected_payment_option
                            in ["USDC", "USDT", "USDBC", "EUROC"]
                            else 18
                        )

                        with st.spinner("Verifying payment on-chain..."):
                            is_valid, verify_msg = verify_evm_payment(
                                rpc_url=rpc_url,
                                tx_hash=tx_hash_input.strip(),
                                expected_wallet=receiver_address,
                                expected_amount_usd=float(service_price),
                                token_decimals=token_decimals,
                            )

                        if not is_valid:
                            st.error(f"❌ Payment Verification Failed: {verify_msg}")
                        else:
                            booking_payload = {
                                "name": client_name.strip(),
                                "email": email.strip(),
                                "phone": phone.strip(),
                                "service": selected_service,
                                "date": booking_date,
                                "time": booking_time,
                                "portfolio_size": portfolio_size,
                                "trading_experience": trading_exp,
                                "topics": topics,
                                "notes": notes,
                                "payment_network": selected_network,
                                "payment_currency": selected_payment_option,
                                "amount_usd": service_price,
                                "tx_hash": tx_hash_input.strip(),
                                "tx_status": "Verified On-Chain",
                            }

                            saved, db_msg = save_booking(booking_payload)
                            if saved:
                                st.success("✅ Payment verified & consultation scheduled!")
                                st.balloons()
                                st.markdown(
                                    f"""
                                **Booking Summary:**
                                * **Tx Hash:** `{tx_hash_input.strip()}`
                                * **Status:** Verified On-Chain
                                * **Service:** {selected_service}
                                * **Date:** {booking_date.strftime('%B %d, %Y')} at {booking_time.strftime('%I:%M %p')} EAT
                                """
                                )
                            else:
                                st.error(db_msg)


# ==========================================
# MAIN ROUTER WITH AUTHENTICATION
# ==========================================
def booking_consultation():
    init_sqlite_db()

    # Session State Authentication Initialization
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    # Sidebar Authentication Box
    st.sidebar.markdown("### 🔐 Admin Authentication")
    
    if st.session_state.is_admin:
        st.sidebar.success("Logged in as **mokua254**")
        if st.sidebar.button("Logout Admin"):
            st.session_state.is_admin = False
            st.rerun()
    else:
        admin_username = st.sidebar.text_input("Username", key="admin_user")
        admin_password = st.sidebar.text_input("Password", type="password", key="admin_pass")
        
        if st.sidebar.button("Login"):
            if admin_username.strip() == "mokua254" and admin_password == "mokua@254":
                st.session_state.is_admin = True
                st.sidebar.success("Welcome back, mokua254!")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials.")

    # View Routing Logic
    if st.session_state.is_admin:
        admin_dashboard()
    else:
        client_booking_interface()









def crypto_quantitative_analysis():
    import streamlit as st
    import pandas as pd
    import numpy as np
    import time
    import plotly.graph_objects as go

    # Define top-level tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "⚠️ DISCLAIMER",
        "📊 Top Cryptocurrencies",
        "📈 Cycle Tops & Bottoms", 
        "🧠 Sentiment Check",
        "💼 Portfolio & Position Sizing", 
        "🚀 AltSeason Index",
        "🎯 Profit Taking & DCA",
        "📑 Market Report"
    ])

    # ---------------------------------------------------------
    # TAB 1: DISCLAIMER
    # ---------------------------------------------------------
    with tab1:
        st.subheader("RISK DISCLAIMER")
        st.warning(
            "Before deciding to participate in the Crypto market, you should carefully consider your investment "
            "objectives, level of experience, and risk appetite. Most importantly, do not invest money you cannot afford to lose.\n\n"
            "Crypto trading is highly volatile and carries significant financial risk. All information, analyses, opinions, and prices "
            "are provided strictly as general market commentary and do not constitute investment advice.\n\n"
            "Under no circumstances will OpenCipher accept liability for any loss or damage arising directly or indirectly "
            "from reliance on information contained in this platform."
        )

    # ---------------------------------------------------------
    # TAB 2: TOP CRYPTOCURRENCIES
    # ---------------------------------------------------------
    with tab2:
        #scrapping()
        scrapping_coingeckoAPI()

    # ---------------------------------------------------------
    # TAB 3: CYCLE TOPS & BOTTOMS
    # ---------------------------------------------------------
    with tab3:
        st.subheader("Long Term Position Building & Profit Taking")

        btc_tab, eth_tab, sol_tab = st.tabs(["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"])

        with btc_tab:
            st.subheader("Bitcoin Analytics (Future Cycle Tops & Bottoms)")
            btc_weekly_momentum_strat()

        with eth_tab:
            st.subheader("Ethereum Analytics (Future Cycle Tops & Bottoms)")
            eth_weekly_momentum_strat()

        with sol_tab:
            st.subheader("Solana Analytics (Future Cycle Tops & Bottoms)")
            sol_weekly_momentum_strat()

    # ---------------------------------------------------------
    # TAB 4: SENTIMENT CHECK
    # ---------------------------------------------------------
    with tab4:
        st.subheader("Sentiment Analysis & Moving Average Check")
        #put this into mini tabs for each of the above modules
        sentiment_tab, ma_tab ,greedandfear_tab = st.tabs(["Sentiment Analysis", "Moving Average"," Crypto Fear & Greed Index"])

        with sentiment_tab:
            module_sentiment_analysis()

        with ma_tab:
            module_moving_average()

        with greedandfear_tab:
            fear_and_greed_indicator()
            

    # ---------------------------------------------------------
    # TAB 5: PORTFOLIO DESIGN & POSITION SIZING (Refactored UI)
    # ---------------------------------------------------------
    with tab5:

        # ---------------------------------------------------------
        # Create Sub-tabs inside Tab 5
        # ---------------------------------------------------------
        subtab1, subtab2 = st.tabs(
            ["📊 Risk, allocation & Design", "🚀 2028 Crypto Portfolio"]
        )

        # ---------------------------------------------------------
        # SUB-TAB 1: Risk & Design Allocation
        # ---------------------------------------------------------
        with subtab1:
            st.subheader("Portfolio Design & Risk Management")

            col_input, col_chart = st.columns([1, 1.2])

            with col_input:
                age = st.number_input(
                    "Enter your age:", min_value=1, max_value=300, value=25, step=1
                )
                if age < 18:
                    st.warning("You are a minor, wait till 18 to start investing.")
                    st.stop()  # Stops execution here so no subsequent code or charts are displayed

                # Determine allocation percentages based on age bracket (sums to 100%)
                if 18 <= age <= 30:
                    sizes = [30, 10, 10, 10, 10, 10, 20]
                elif 30 < age <= 40:
                    sizes = [25, 11, 11, 11, 11, 11, 20]
                elif 40 < age <= 50:
                    sizes = [20, 11.5, 11.5, 11.5, 11.5, 14, 20]
                elif 50 < age <= 60:
                    sizes = [15, 12.5, 12.5, 12.5, 12.5, 15, 20]
                elif 60 < age <= 70:
                    sizes = [10, 13.5, 13.5, 13.5, 13.5, 16, 20]
                else:
                    sizes = [5, 14.5, 14.5, 14.5, 14.5, 17, 20]

                st.info(
                    f"Target Crypto Allocation for age **{age}**: **{sizes[0]}%**"
                )

            with col_chart:
                labels = [
                    "CRYPTO",
                    "S&P 500",
                    "DJIA",
                    "NASDAQ",
                    "Fine Art",
                    "BONDS",
                    "Dollar Reserves",
                ]

                # Hex colors matched to all 7 assets:
                # 1. CRYPTO: #00E676 (Green)
                # 2. S&P 500: #FF9800 (Orange)
                # 3. DJIA: #29B6F6 (Light Blue)
                # 4. NASDAQ: #AB47BC (Purple)
                # 5. Fine Art: #EC407A (Pink)
                # 6. BONDS: #4CAF50 (Forest Green)
                # 7. Dollar Reserves: #FFC107 (Amber Gold)
                colors = [
                    "#00E676",
                    "#FF9800",
                    "#29B6F6",
                    "#AB47BC",
                    "#EC407A",
                    "#4CAF50",
                    "#FFC107",
                ]

                fig_portfolio = go.Figure(
                    data=[
                        go.Pie(
                            labels=labels,
                            values=sizes,
                            hole=0.45,
                            marker=dict(colors=colors),
                            textinfo="label+percent",
                            textfont=dict(size=12, color="#FFFFFF"),
                        )
                    ]
                )

                fig_portfolio.update_layout(
                    height=320,
                    margin=dict(l=20, r=20, t=30, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                )

                st.plotly_chart(fig_portfolio, use_container_width=True)

            st.divider()

            # Optional: General Crypto Framework Function
            if "crypto_portfolio" in globals():
                crypto_portfolio()

        # ---------------------------------------------------------
        # SUB-TAB 2: 2028 Crypto Portfolio Engine
        # ---------------------------------------------------------

        import streamlit as st

        # Check your app's login state (session state or local variable)
        # Replace 'username' with your actual variable name if it differs
        active_user = st.session_state.get("username", None)

        with subtab2:
            if active_user == "mokua254":
                st.subheader("🚀 2026–2028 High-Performance Crypto Portfolio Tracker")

                if "my_crypto_portfolio_2028" in globals():
                    my_crypto_portfolio_2028()
                else:
                    st.warning(
                        "`my_crypto_portfolio_2028()` function is not defined."
                    )
            else:
                st.info("🔒 Restricted Portfolio Access")
                st.write(
                    "Email me at **opencipher254@gmail.com** to access my portfolio."
                )

    
        #with subtab2:

            #if "my_crypto_portfolio_2028" in globals():
               # my_crypto_portfolio_2028()
            #else:
                #st.warning("`my_crypto_portfolio_2028()` function is not defined.")



    # ---------------------------------------------------------
    # TAB 6: ALTSEASON INDEX
    # ---------------------------------------------------------
    with tab6:
        altcoinseason()

    # ---------------------------------------------------------
    # TAB 7: PROFIT TAKING & DCA STRATEGIES
    # ---------------------------------------------------------
    with tab7:
        st.subheader("Profit Taking & DCA Strategies")

        btc_tab, eth_tab, sol_tab = st.tabs(["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"])

        with btc_tab:
            #st.header("Bitcoin Strategies")
            module_rsi_strategy()

        with eth_tab:
            #st.header("Ethereum Strategies")
            eth_momentum_strat()

        with sol_tab:
            #st.header("Solana Strategies")
            sol_momentum_strat()

    # ---------------------------------------------------------
    # TAB 8: MARKET REPORT
    # ---------------------------------------------------------
    with tab8:
        market_report()



import hashlib
import sqlite3
import pandas as pd
import streamlit as st



def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False
# DB Management
import sqlite3 
conn = sqlite3.connect('data.db')
c = conn.cursor()
# DB  Functions
def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')


def add_userdata(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data


def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data

import pandas as pd
import streamlit as st



def main():
    """Simple Login App"""

    # 1. Initialize session state variables if they don't exist
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None

    menu = [
        "Home",
        "Login",
        "SignUp",
        "Logout",
        "Reset Password",
        
    ]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        #scrapping()
        scrapping_coingeckoAPI()

    elif choice == "Login":
        st.sidebar.subheader("Login Section")

        # If user is already logged in, show status
        if st.session_state["logged_in"]:
            st.sidebar.success(
                f"Already logged in as: {st.session_state['username']}"
            )
        else:
            username_input = st.sidebar.text_input("User Name")
            password_input = st.sidebar.text_input("Password", type="password")

            if st.sidebar.button("Login"):
                create_usertable()
                hashed_pswd = make_hashes(password_input)

                # Validate user credentials
                result = login_user(
                    username_input, check_hashes(password_input, hashed_pswd)
                )

                if result:
                    # SAVE STATE TO PERSIST ACROSS RERUNS
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username_input
                    st.sidebar.success(f"Logged In as {username_input}")
                    st.rerun()
                else:
                    st.sidebar.warning("Incorrect Username/Password")

        # If logged in successfully, show main app features

        if st.session_state["logged_in"]:

            # 1. Dynamically build available tasks based on user role
            available_tasks = ["Qualitative Analysis", "Quantitative Analysis"]

            # Show "Profiles" only to admin
            if st.session_state["username"] == "mokua254":
                available_tasks.append("Profiles")

            # Add "Book an Appointment" for everyone
            available_tasks.append("Book an Appointment")

            task = st.selectbox("Task", available_tasks)

            # -------------------------------------------------------------------------
            # Task Handlers
            # -------------------------------------------------------------------------
            if task == "Qualitative Analysis":
                st.subheader("Add Your Post")
                investor_connect2()

                comments = st.text_input("Leave a Comment Below: ")
                st.button("Submit Comment")
                social_medialinks()

            elif task == "Quantitative Analysis":
                st.subheader("Quantitative Analysis")
                crypto_quantitative_analysis()

            elif task == "Profiles":
                if st.session_state["username"] == "mokua254":
                    st.subheader("User Profiles")
                    user_result = view_all_users()
                    clean_db = pd.DataFrame(
                        user_result, columns=["Username", "Password"]
                    )
                    st.dataframe(clean_db)
                else:
                    st.warning("Cannot access profiles.")

            elif task == "Book an Appointment":
                st.subheader("Get an expert's insights")

                # Admin Access Prompt
                if st.session_state["username"] == "mokua254":
                    st.info("ℹ️ You are logged in as Admin (`mokua254`). This feature is designed for clients.")
                    admin_access = st.checkbox("Preview Client Booking Interface")

                    if admin_access:
                        booking_consultation()
                        admin_dashboard()
                    else:
                        st.caption("Check the box above if you want to view or test the booking flow.")
                else:
                    # Render directly for clients
                    booking_consultation()

       
    elif choice == "Logout":
        st.subheader("Logout Section")
        if st.session_state["logged_in"]:
            if st.button("Confirm Logout"):
                st.session_state["logged_in"] = False
                st.session_state["username"] = None
                st.success("You have been logged out.")
                st.rerun()
        else:
            st.info("You are not logged in.")

    elif choice == "Reset Password":
        st.subheader("Reset Password")
        username = st.text_input("Username")
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")

        if st.button("Reset"):
            create_usertable()
            hashed_pswd = make_hashes(old_password)

            result = login_user(
                username, check_hashes(old_password, hashed_pswd)
            )
            if result:
                reset_password(username, new_password)
                st.success("Password successfully reset!")
            else:
                st.warning("Incorrect Username/Password")

    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type="password")

        if st.button("Signup"):
            create_usertable()
            add_userdata(new_user, make_hashes(new_password))
            st.success("You have successfully created a valid Account")
            st.info("Go to Login Menu to login")

    

    
if __name__ == "__main__":
    main()








#streamlit run old_login.py





#streamlit run streamlit_login.py
#streamlit run Degen_connect_test.py

# Megatron1080
#python.exe -m pip install --upgrade pip --user


#run command: streamlit run after_uiux_design.py





#streamlit run streamlit_login.py
#streamlit run Degen_connect_test.py

# Megatron1080
#python.exe -m pip install --upgrade pip --user


