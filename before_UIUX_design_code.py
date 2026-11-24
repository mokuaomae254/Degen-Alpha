from pathlib import Path
import warnings
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import ta
import ta.momentum
import yfinance as yf

st.set_page_config(layout="wide")

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "BCHAIN-MKPRU_updated10.csv"


# ==========================================
# BITCOIN DATA FETCHING UTILITY
# ==========================================
@st.cache_data(ttl=3600)  # Cache combined dataset for 1 hour
def load_combined_btc_data():
  """Combines historical CSV data (2009-present) with live Yahoo Finance data for missing recent dates."""
  if not DATA_PATH.exists():
    st.error(f"Base dataset not found at `{DATA_PATH}`")
    return pd.DataFrame()

  # 1. Load baseline historical dataset
  df_old = pd.read_csv(DATA_PATH)[["Date", "Value"]]
  df_old["Date"] = pd.to_datetime(df_old["Date"], errors="coerce")
  df_old["Value"] = pd.to_numeric(df_old["Value"], errors="coerce")
  df_old = df_old.dropna().sort_values("Date").reset_index(drop=True)

  # 2. Fetch missing recent dates from Yahoo Finance
  try:
    last_date = df_old["Date"].max()
    # Fetch data starting 1 day before the max CSV date to handle overlaps cleanly
    start_str = (last_date - pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    ticker = yf.Ticker("BTC-USD")
    df_new = ticker.history(start=start_str, interval="1d").reset_index()

    if not df_new.empty:
      df_new["Date"] = pd.to_datetime(df_new["Date"]).dt.tz_localize(None)
      df_new["Value"] = pd.to_numeric(df_new["Close"], errors="coerce")
      df_new = df_new[["Date", "Value"]].dropna()

      # 3. Merge historical CSV + live yfinance data
      df_combined = pd.concat([df_old, df_new], ignore_index=True)
      df_combined = df_combined.drop_duplicates(
          subset=["Date"], keep="last"
      )
    else:
      df_combined = df_old

  except Exception as e:
    # Fail gracefully to historical dataset if API fetch encounters network issues
    df_combined = df_old

  # Final cleaning & sorting (Ascending order for technical indicators)
  df_combined = df_combined[df_combined["Value"] > 0]
  df_combined = df_combined.sort_values(by="Date").reset_index(drop=True)
  return df_combined


# ==========================================
# SOLANA DATA FETCHING UTILITY
# ==========================================
@st.cache_data(ttl=3600)
def load_sol_data():
  """Fetches historical daily Solana (SOL-USD) data directly from Yahoo Finance."""
  try:
    ticker = yf.Ticker("SOL-USD")
    df = ticker.history(period="max", interval="1d")

    if df.empty:
      st.error("No data returned from Yahoo Finance for SOL-USD.")
      return pd.DataFrame()

    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df["Value"] = pd.to_numeric(df["Close"], errors="coerce")

    df = df[["Date", "Value"]].dropna()
    df = df[df["Value"] > 0].sort_values(by="Date").reset_index(drop=True)
    return df
  except Exception as e:
    st.error(f"Error fetching Solana data from Yahoo Finance: {e}")
    return pd.DataFrame()


# ==========================================
# ETHEREUM DATA FETCHING UTILITY
# ==========================================
@st.cache_data(ttl=3600)
def load_eth_data():
  """Fetches historical daily Ethereum (ETH-USD) data directly from Yahoo Finance."""
  try:
    ticker = yf.Ticker("ETH-USD")
    df = ticker.history(period="max", interval="1d")

    if df.empty:
      st.error("No data returned from Yahoo Finance for ETH-USD.")
      return pd.DataFrame()

    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df["Value"] = pd.to_numeric(df["Close"], errors="coerce")

    df = df[["Date", "Value"]].dropna()
    df = df[df["Value"] > 0].sort_values(by="Date").reset_index(drop=True)
    return df
  except Exception as e:
    st.error(f"Error fetching Ethereum data from Yahoo Finance: {e}")
    return pd.DataFrame()


# ==========================================
# BITCOIN MODULES
# ==========================================
def module_moving_average():
  warnings.filterwarnings("ignore")
  st.header("1. 200-Day Moving Average Strategy")

  df = load_combined_btc_data()
  if df.empty:
    return

  df["ma"] = df["Value"].rolling(window=200).mean()

  fig, ax = plt.subplots(figsize=(10, 4))
  ax.semilogy(df["Date"], df["Value"], label="BTC Price (USD)", linewidth=0.7)
  ax.plot(
      df["Date"],
      df["ma"],
      color="red",
      label="200-Day Moving Avg",
      linewidth=1.2,
  )
  ax.set_ylabel("Price (USD, Log Scale)")
  ax.set_xlabel("Date")
  ax.legend(loc="upper left")
  ax.grid(True, which="both", linestyle="--", alpha=0.3)

  st.pyplot(fig)
  plt.close(fig)

  latest_price = df["Value"].iloc[-1]
  latest_ma = df["ma"].iloc[-1]

  if latest_price > latest_ma:
    st.success(
        f"**Risk-On Environment** (Price: ${latest_price:,.2f} > 200DMA:"
        f" ${latest_ma:,.2f})"
    )
  else:
    st.error(
        f"**Risk-Off Environment** (Price: ${latest_price:,.2f} <= 200DMA:"
        f" ${latest_ma:,.2f})"
    )


def module_rsi_strategy():
  warnings.filterwarnings("ignore")
  st.header("2. Relative Strength Index (RSI)")

  df = load_combined_btc_data()
  if df.empty:
    return

  df["rsi"] = ta.momentum.rsi(close=df["Value"], window=14)

  fig, (ax1, ax2) = plt.subplots(
      2, 1, sharex=True, figsize=(10, 6), gridspec_kw={"height_ratios": [2, 1]}
  )

  ax1.semilogy(df["Date"], df["Value"], linewidth=0.7, color="gray")
  ax1.set_ylabel("Price (USD)")

  ax2.plot(df["Date"], df["rsi"], linewidth=0.7, color="purple")
  ax2.axhline(80, color="red", linewidth=0.8, linestyle="--")
  ax2.axhline(25, color="green", linewidth=0.8, linestyle="--")
  ax2.set_ylabel("RSI")
  ax2.grid(True, linestyle="--", alpha=0.3)
  ax2.text(
      df.Date.iloc[-1],
      92,
      "Take Profit",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.text(
      df.Date.iloc[-1],
      13,
      "Build a position",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )

  latest_rsi = df["rsi"].iloc[-1]

  if latest_rsi > 80:
    st.write(
        f"**RSI is {latest_rsi:.2f} (> 80):** Time to sell / DCA out"
        " (Overbought)"
    )
  elif latest_rsi < 25:
    st.write(
        f"**RSI is {latest_rsi:.2f} (< 25):** Time to buy / DCA in (Oversold)"
    )
  else:
    st.write(f"**RSI is {latest_rsi:.2f}:** Neutral zone (Hold position)")

  st.pyplot(fig)
  plt.close(fig)


def module_dca_calculator():
  st.header("3. Dollar Cost Averaging Calculator")

  df = load_combined_btc_data()
  if df.empty:
    return

  col1, col2 = st.columns(2)
  with col1:
    investment_amount = st.number_input(
        "Enter investment amount ($):", min_value=1, value=100, step=1
    )
    investment_interval = st.number_input(
        "Enter investment interval (in days):", min_value=1, value=7, step=1
    )

  with col2:
    start_date = pd.to_datetime(
        st.date_input("Enter start date:", value=df["Date"].min())
    )
    end_date = pd.to_datetime(
        st.date_input("Enter end date:", value=df["Date"].max())
    )

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


def module_sentiment_analysis():
  warnings.filterwarnings("ignore")
  st.header("4. 200-Week Moving Average Sentiment Analysis")

  df = load_combined_btc_data()
  if df.empty:
    return

  df_weekly = (
      df.set_index("Date")["Value"].resample("W").last().reset_index()
  )
  df_weekly["200wma"] = df_weekly["Value"].rolling(window=200).mean()

  dataframe = pd.merge_asof(
      df.sort_values("Date"),
      df_weekly[["Date", "200wma"]].dropna().sort_values("Date"),
      on="Date",
  )

  monthly = dataframe.iloc[::30].copy()
  monthly["distance"] = monthly["200wma"].pct_change() * 100

  fig, ax = plt.subplots(figsize=(10, 5))
  plt.style.use("dark_background")

  ax.semilogy(
      dataframe["Date"],
      dataframe["Value"],
      color="grey",
      zorder=1,
      label="BTC Price",
  )
  ax.semilogy(
      dataframe["Date"],
      dataframe["200wma"],
      color="purple",
      zorder=2,
      label="200WMA",
  )

  scatter = ax.scatter(
      monthly["Date"],
      monthly["Value"],
      c=monthly["distance"],
      cmap="rainbow",
      vmin=0,
      vmax=16,
      zorder=4,
  )

  cbar = fig.colorbar(scatter, ax=ax)
  cbar.set_label("% monthly increase in 200wma")

  ax.set_ylabel("Price (USD, Log Scale)")
  ax.grid(True, which="both", linestyle="--", alpha=0.2)

  st.pyplot(fig)
  plt.close(fig)


# ==========================================
# SOLANA MODULE
# ==========================================
def sol_momentum_strat():
  warnings.filterwarnings("ignore")
  st.header("Solana (SOL) Momentum Strategy")

  df = load_sol_data()
  if df.empty:
    return

  fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(10, 6))

  ax1.semilogy(df.Date, df.Value, linewidth=0.8, color="#14F195")
  ax1.set_ylabel("SOL Price (USD, Log Scale)")
  ax1.grid(True, which="both", ls="--", alpha=0.3)

  df["rsi"] = ta.momentum.rsi(close=df.Value, window=14)
  ax2.axhline(80, color="red", linewidth=0.8)
  ax2.axhline(25, color="green", linewidth=0.8)

  ax2.text(
      df.Date.iloc[-1],
      83,
      "Take Profit",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.text(
      df.Date.iloc[-1],
      18,
      "Build a position",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.plot(df.Date, df.rsi, linewidth=0.8, color="purple")
  ax2.set_ylabel("RSI (14)")
  ax2.grid(True, ls="--", alpha=0.3)

  current_rsi = df["rsi"].iloc[-1]
  if current_rsi > 80:
    st.write(
        f"**Solana RSI is at {current_rsi:.2f} (>80):** Time to sell/DCA out!"
    )
  elif current_rsi < 25:
    st.write(
        f"**Solana RSI is at {current_rsi:.2f} (<25):** Time to buy/DCA in!"
    )
  else:
    st.write(
        f"**Solana RSI is at {current_rsi:.2f} (Neutral 25-80):** Hold"
        " position."
    )

  st.pyplot(fig)
  plt.close(fig)


# ==========================================
# ETHEREUM MODULE
# ==========================================
def eth_momentum_strat():
  warnings.filterwarnings("ignore")
  st.header("Ethereum (ETH) Momentum Strategy")

  df = load_eth_data()
  if df.empty:
    return

  fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(10, 6))

  ax1.semilogy(df.Date, df.Value, linewidth=0.8, color="#627EEA")
  ax1.set_ylabel("ETH Price (USD, Log Scale)")
  ax1.grid(True, which="both", ls="--", alpha=0.3)

  df["rsi"] = ta.momentum.rsi(close=df.Value, window=14)
  ax2.axhline(80, color="red", linewidth=0.8)
  ax2.axhline(25, color="green", linewidth=0.8)

  ax2.text(
      df.Date.iloc[-1],
      83,
      "Take Profit",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.text(
      df.Date.iloc[-1],
      18,
      "Build a position",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.plot(df.Date, df.rsi, linewidth=0.8, color="purple")
  ax2.set_ylabel("RSI (14)")
  ax2.grid(True, ls="--", alpha=0.3)

  current_rsi = df["rsi"].iloc[-1]
  if current_rsi > 80:
    st.write(
        f"**Ethereum RSI is at {current_rsi:.2f} (>80):** Time to sell/DCA"
        " out!"
    )
  elif current_rsi < 25:
    st.write(
        f"**Ethereum RSI is at {current_rsi:.2f} (<25):** Time to buy/DCA"
        " in!"
    )
  else:
    st.write(
        f"**Ethereum RSI is at {current_rsi:.2f} (Neutral 25-80):** Hold"
        " position."
    )

  st.pyplot(fig)
  plt.close(fig)



@st.cache_data(ttl=3600)  # Cache data for 1 hour to prevent API rate limiting
def load_btc_weekly_data():
  """Fetches historical weekly Bitcoin (BTC-USD) data directly from Yahoo Finance."""
  try:
    ticker = yf.Ticker("BTC-USD")
    # Set interval='1wk' for weekly timeframe data
    df = ticker.history(period="max", interval="1wk")

    if df.empty:
      st.error("No data returned from Yahoo Finance for BTC-USD.")
      return pd.DataFrame()

    df = df.reset_index()
    # Normalize timezone and extract necessary columns
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df["Value"] = pd.to_numeric(df["Close"], errors="coerce")

    df = df[["Date", "Value"]].dropna()
    df = df[df["Value"] > 0].sort_values(by="Date").reset_index(drop=True)
    return df
  except Exception as e:
    st.error(f"Error fetching Bitcoin data from Yahoo Finance: {e}")
    return pd.DataFrame()


# ==========================================
# MODULE: BITCOIN WEEKLY MOMENTUM STRATEGY
# ==========================================
def btc_weekly_momentum_strat():
  warnings.filterwarnings("ignore")

  df = load_btc_weekly_data()
  if df.empty:
    return

  fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(10, 6))

  # Price Subplot (using Bitcoin orange color #F7931A)
  ax1.semilogy(df.Date, df.Value, linewidth=0.8, color="#F7931A")
  ax1.set_ylabel("BTC Weekly Price (USD, Log Scale)")
  ax1.grid(True, which="both", ls="--", alpha=0.3)

  # RSI Subplot (14-week RSI)
  df["rsi"] = ta.momentum.rsi(close=df.Value, window=14)
  ax2.axhline(87, color="red", linewidth=0.8)
  ax2.axhline(30, color="green", linewidth=0.8)

  ax2.text(
      df.Date.iloc[-1],
      93,
      "Aggressively DCA out",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.text(
      df.Date.iloc[-1],
      25,
      "Aggressively DCA in",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.plot(df.Date, df.rsi, linewidth=0.8, color="purple")
  ax2.set_ylabel("Weekly RSI (14)")
  ax2.grid(True, ls="--", alpha=0.3)

  current_rsi = df["rsi"].iloc[-1]
  if current_rsi > 87:
    st.write(
        f"**Bitcoin Weekly RSI is at {current_rsi:.2f} (>87):** Overbought -"
        "SELL THE TOP!: The market will top in the next Higher high, watchout for a bearish divergence"
    )
  elif current_rsi < 30:
    st.write(
        f"**Bitcoin Weekly RSI is at {current_rsi:.2f} (<30):** Oversold - Time"
        "BUY THE BOTTOM!: The market will bottom in the next lower low, watchout for a bullish divergence"
    )
  else:
    st.write(
        f"**Bitcoin Weekly RSI is at {current_rsi:.2f} (Neutral 30-87):** Hold"
        " position."
    )

  st.pyplot(fig)
  plt.close(fig)


@st.cache_data(ttl=3600)  # Cache data for 1 hour to prevent API rate limiting
def load_sol_weekly_data():
  """Fetches historical weekly Solana (SOL-USD) data directly from Yahoo Finance."""
  try:
    ticker = yf.Ticker("SOL-USD")
    # Set interval='1wk' for weekly timeframe data
    df = ticker.history(period="max", interval="1wk")

    if df.empty:
      st.error("No data returned from Yahoo Finance for SOL-USD.")
      return pd.DataFrame()

    df = df.reset_index()
    # Normalize timezone and extract necessary columns
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df["Value"] = pd.to_numeric(df["Close"], errors="coerce")

    df = df[["Date", "Value"]].dropna()
    df = df[df["Value"] > 0].sort_values(by="Date").reset_index(drop=True)
    return df
  except Exception as e:
    st.error(f"Error fetching Solana data from Yahoo Finance: {e}")
    return pd.DataFrame()


# ==========================================
# MODULE: SOLANA WEEKLY MOMENTUM STRATEGY
# ==========================================
def sol_weekly_momentum_strat():
  warnings.filterwarnings("ignore")

  df = load_sol_weekly_data()
  if df.empty:
    return

  fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(10, 6))

  # Price Subplot (using Solana green color #14F195)
  ax1.semilogy(df.Date, df.Value, linewidth=0.8, color="#14F195")
  ax1.set_ylabel("SOL Weekly Price (USD, Log Scale)")
  ax1.grid(True, which="both", ls="--", alpha=0.3)

  # RSI Subplot (14-week RSI)
  df["rsi"] = ta.momentum.rsi(close=df.Value, window=14)
  ax2.axhline(87, color="red", linewidth=0.8)
  ax2.axhline(30, color="green", linewidth=0.8)

  ax2.text(
      df.Date.iloc[-1],
      93,
      "Aggressively DCA out",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.text(
      df.Date.iloc[-1],
      25,
      "Aggressively DCA in",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.plot(df.Date, df.rsi, linewidth=0.8, color="purple")
  ax2.set_ylabel("Weekly RSI (14)")
  ax2.grid(True, ls="--", alpha=0.3)

  current_rsi = df["rsi"].iloc[-1]
  if current_rsi > 87:
    st.write(
        f"**Solana Weekly RSI is at {current_rsi:.2f} (>87):** Overbought -"
        " SELL THE TOP!: The market will top in the next Higher high, watchout"
        " for a bearish divergence"
    )
  elif current_rsi < 30:
    st.write(
        f"**Solana Weekly RSI is at {current_rsi:.2f} (<30):** Oversold - Time"
        " BUY THE BOTTOM!: The market will bottom in the next lower low,"
        " watchout for a bullish divergence"
    )
  else:
    st.write(
        f"**Solana Weekly RSI is at {current_rsi:.2f} (Neutral 30-87):** Hold"
        " position."
    )

  st.pyplot(fig)
  plt.close(fig)



@st.cache_data(ttl=3600)  # Cache data for 1 hour to prevent API rate limiting
def load_eth_weekly_data():
  """Fetches historical weekly Ethereum (ETH-USD) data directly from Yahoo Finance."""
  try:
    ticker = yf.Ticker("ETH-USD")
    # Set interval='1wk' for weekly timeframe data
    df = ticker.history(period="max", interval="1wk")

    if df.empty:
      st.error("No data returned from Yahoo Finance for ETH-USD.")
      return pd.DataFrame()

    df = df.reset_index()
    # Normalize timezone and extract necessary columns
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df["Value"] = pd.to_numeric(df["Close"], errors="coerce")

    df = df[["Date", "Value"]].dropna()
    df = df[df["Value"] > 0].sort_values(by="Date").reset_index(drop=True)
    return df
  except Exception as e:
    st.error(f"Error fetching Ethereum data from Yahoo Finance: {e}")
    return pd.DataFrame()


# ==========================================
# MODULE: ETHEREUM WEEKLY MOMENTUM STRATEGY
# ==========================================
def eth_weekly_momentum_strat():
  warnings.filterwarnings("ignore")

  df = load_eth_weekly_data()
  if df.empty:
    return

  fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(10, 6))

  # Price Subplot (using official Ethereum brand blue #627EEA)
  ax1.semilogy(df.Date, df.Value, linewidth=0.8, color="#627EEA")
  ax1.set_ylabel("ETH Weekly Price (USD, Log Scale)")
  ax1.grid(True, which="both", ls="--", alpha=0.3)

  # RSI Subplot (14-week RSI)
  df["rsi"] = ta.momentum.rsi(close=df.Value, window=14)
  ax2.axhline(83, color="red", linewidth=0.8)
  ax2.axhline(30, color="green", linewidth=0.8)

  ax2.text(
      df.Date.iloc[-1],
      93,
      "Aggressively DCA out",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.text(
      df.Date.iloc[-1],
      25,
      "Aggressively DCA in",
      fontsize=8,
      ha="left",
      va="center",
      color="blue",
      bbox=dict(boxstyle="round", ec="k", fc="w"),
  )
  ax2.plot(df.Date, df.rsi, linewidth=0.8, color="purple")
  ax2.set_ylabel("Weekly RSI (14)")
  ax2.grid(True, ls="--", alpha=0.3)

  current_rsi = df["rsi"].iloc[-1]
  if current_rsi > 83:
    st.write(
        f"**Ethereum Weekly RSI is at {current_rsi:.2f} (>83):** Overbought -"
        " SELL THE TOP!: The market will top in the next Higher high, watchout"
        " for a bearish divergence"
    )
  elif current_rsi < 30:
    st.write(
        f"**Ethereum Weekly RSI is at {current_rsi:.2f} (<30):** Oversold - Time"
        " BUY THE BOTTOM!: The market will bottom in the next lower low,"
        " watchout for a bullish divergence"
    )
  else:
    st.write(
        f"**Ethereum Weekly RSI is at {current_rsi:.2f} (Neutral 30-83):** Hold"
        " position."
    )

  st.pyplot(fig)
  plt.close(fig)



def market_report():
		import pandas as pd
		import numpy as np
		import streamlit as st
		import base64

		# Load Data
		df = pd.read_csv("coingecko-crypto-data.csv")

		# Categorize Liquidity Risk
		liquidity_risk = []
		for index in df.index:
			vol = df["24h Volume"][index]
			mcap = df["Market Cap"][index]

			if pd.isna(vol) or pd.isna(mcap) or mcap == 0:
				liquidity_risk.append("unknown")
			elif vol < (mcap * 0.05):
				liquidity_risk.append("illiquid")
			elif vol <= (mcap * 0.1):
				liquidity_risk.append("fairly liquid")
			elif vol <= (mcap * 0.3):
				liquidity_risk.append("highly liquid")
			elif vol <= (mcap * 0.5):
				liquidity_risk.append("limited long term potential")
			else:
				liquidity_risk.append("stay off")

		df["liquidity_risk"] = liquidity_risk

		# Stablecoin Overrides
		stablecoins = [ 
			"Tether", "USDC", "USDS", "Dai", "USD1", "Ethena USDe", "Global Dollar",
			"BlackRock USD Institutional Digital Liquidity Fund", "PayPal USD", "Ripple USD", 
			"USDD", "Falcon USD", "BFUSD", "United Stables", "USDGO", "GHO", "YLDS", 
			"Usual USD", "Figure Heloc", "Circle USYC", "Tether Gold", "Ondo US Dollar Yield", 
			"PAX Gold", "Spiko Amundi Overnight Swap Fund (EUR)", "Spiko EU T-Bills Money Market Fund", 
			"Janus Henderson Anemoy Treasury Fund", "Invesco Short Duration US Government Securities Fund", 
			"Janus Henderson Anemoy AAA CLO Fund"
		]

		df.loc[df["Coin"].isin(stablecoins), "liquidity_risk"] = "stablecoin"


		# --- EVALUATION HELPERS ---

		def evaluate_bullish_sentiment(top_10_losers_df, period_type):
			"""Evaluates market bullishness based on stablecoin presence in top 10 worst performers."""
			stablecoin_count = (top_10_losers_df["liquidity_risk"] == "stablecoin").sum()
			
			if period_type == "hourly":
				if stablecoin_count < 5:
					return "this day is not soo bullish"
				elif 5 <= stablecoin_count <= 6:
					return "this day bullishness is kicking in"
				elif 7 <= stablecoin_count <= 8:
					return "this day is bullish"
				else:
					return "this day is extremely bullish : take partial profits on your long day trades and look for potential short day trades"

			elif period_type == "daily":
				if stablecoin_count < 5:
					return "this week is not soo bullish"
				elif 5 <= stablecoin_count <= 6:
					return "this week bullishness is kicking in"
				elif 7 <= stablecoin_count <= 8:
					return "this week is bullish"
				else:
					return "this week is extremely bullish :take partial profits on your long swing trades and look for potential short swing trades"

			elif period_type == "weekly":
				if stablecoin_count < 5:
					return "this month is not soo bullish: not an altseason yet"
				elif 5 <= stablecoin_count <= 6:
					return "this month bullishness is kicking in: the altseason is here"
				elif 7 <= stablecoin_count <= 8:
					return "this month is bullish: the altseason is bullish"
				else:
					return "this month is extremely bullish: the altseason is extremely bullish: take partial profits on alts and use to Buy The Dip (BTD) on BTC, SOL and ETH the dip that is coming in less than a months time"


		def evaluate_bearish_sentiment(top_10_winners_df, period_type):
			"""Evaluates market bearishness based on stablecoin presence in top 10 best performers."""
			stablecoin_count = (top_10_winners_df["liquidity_risk"] == "stablecoin").sum()
			
			if period_type == "hourly":
				if stablecoin_count < 3:
					return "this day is not soo bearish"
				elif 3 <= stablecoin_count <= 6:
					return "this day bearishness is kicking in"
				elif 7 <= stablecoin_count <= 8:
					return "this day is bearish"
				else:
					return "this day is extremely bearish: This day is extremely bearish: take partial profits on your short day trades and look for potential long day trades"

			elif period_type == "daily":
				if stablecoin_count < 3:
					return "this week is not soo bearish"
				elif 3 <= stablecoin_count <= 6:
					return "this week bearishness is kicking in"
				elif 7 <= stablecoin_count <= 8:
					return "this week is bearish"
				else:
					return "this week is extremely bearish: This day is extremely bearish: take partial profits on your short swing trades and look for potential long swing trades"

			elif period_type == "weekly":
				if stablecoin_count < 3:
					return "this month is not soo bearish"
				elif 3 <= stablecoin_count <= 6:
					return "this month bearishness is kicking in"
				elif 7 <= stablecoin_count <= 8:
					return "this month is bearish: start researching on potential Buy The Dip BTD coins IFF we are in bullmarket and start closing your swing shorts trades"
				else:
					return "this month is extremely bearish: the altseason is extremely bearish: take partial profits on your swing shorts trades and use the profits to buy the BTC, SOL and ETH dip that is coming to a near end , you can go long if you want to"


		st.header("Cryptocurrency Market Hourly, Daily and Weekly Report")


		# --- HOURLY WINNERS ---
		st.subheader("Hourly Winners")
		hourly_winners = df.sort_values(by=['1h'], ascending=False).head(10)
		st.dataframe(hourly_winners)

		hourly_bear_msg = evaluate_bearish_sentiment(hourly_winners, "hourly")
		st.warning(f"**Bearish Sentiment Check:** {hourly_bear_msg}")

		if st.button("Download CSV1"):
			csv = hourly_winners.to_csv(index=False)
			b64 = base64.b64encode(csv.encode()).decode()
			href = f'<a href="data:file/csv;base64,{b64}" download="hourly_winners.csv">Download CSV File</a>'
			st.markdown(href, unsafe_allow_html=True)


		# --- HOURLY BIGGEST LOSERS ---
		st.subheader("Hourly Biggest Losers")
		hourly_losers = df.sort_values(by=['1h'], ascending=True).head(10)
		st.dataframe(hourly_losers)

		hourly_bull_msg = evaluate_bullish_sentiment(hourly_losers, "hourly")
		st.info(f"**Bullish Sentiment Check:** {hourly_bull_msg}")

		if st.button("Download CSV2"):
			csv = hourly_losers.to_csv(index=False)
			b64 = base64.b64encode(csv.encode()).decode()
			href = f'<a href="data:file/csv;base64,{b64}" download="hourly_losers.csv">Download CSV File</a>'
			st.markdown(href, unsafe_allow_html=True)


		# --- TODAY'S WINNERS ---
		st.subheader("Today's Winners")
		daily_winners = df.sort_values(by=['24h'], ascending=False).head(10)
		st.dataframe(daily_winners)

		daily_bear_msg = evaluate_bearish_sentiment(daily_winners, "daily")
		st.warning(f"**Bearish Sentiment Check:** {daily_bear_msg}")

		if st.button("Download CSV3"):
			csv = daily_winners.to_csv(index=False)
			b64 = base64.b64encode(csv.encode()).decode()
			href = f'<a href="data:file/csv;base64,{b64}" download="daily_winners.csv">Download CSV File</a>'
			st.markdown(href, unsafe_allow_html=True)


		# --- TODAY'S BIGGEST LOSERS ---
		st.subheader("Today's Biggest Losers")
		daily_losers = df.sort_values(by=['24h'], ascending=True).head(10)
		st.dataframe(daily_losers)

		daily_bull_msg = evaluate_bullish_sentiment(daily_losers, "daily")
		st.info(f"**Bullish Sentiment Check:** {daily_bull_msg}")

		if st.button("Download CSV4"):
			csv = daily_losers.to_csv(index=False)
			b64 = base64.b64encode(csv.encode()).decode()
			href = f'<a href="data:file/csv;base64,{b64}" download="daily_losers.csv">Download CSV File</a>'
			st.markdown(href, unsafe_allow_html=True)


		# --- THIS WEEK'S WINNERS ---
		st.subheader("This Week's Winners")
		weekly_winners = df.sort_values(by=['7d'], ascending=False).head(10)
		st.dataframe(weekly_winners)

		weekly_bear_msg = evaluate_bearish_sentiment(weekly_winners, "weekly")
		st.warning(f"**Bearish Sentiment Check:** {weekly_bear_msg}")

		if st.button("Download CSV5"):
			csv = weekly_winners.to_csv(index=False)
			b64 = base64.b64encode(csv.encode()).decode()
			href = f'<a href="data:file/csv;base64,{b64}" download="weekly_winners.csv">Download CSV File</a>'
			st.markdown(href, unsafe_allow_html=True)


		# --- THIS WEEK'S BIGGEST LOSERS ---
		st.subheader("This Week's Biggest Losers")
		weekly_losers = df.sort_values(by=['7d'], ascending=True).head(10)
		st.dataframe(weekly_losers)

		weekly_bull_msg = evaluate_bullish_sentiment(weekly_losers, "weekly")
		st.info(f"**Bullish Sentiment Check:** {weekly_bull_msg}")

		if st.button("Download CSV6"):
			csv = weekly_losers.to_csv(index=False)
			b64 = base64.b64encode(csv.encode()).decode()
			href = f'<a href="data:file/csv;base64,{b64}" download="weekly_losers.csv">Download CSV File</a>'
			st.markdown(href, unsafe_allow_html=True)




		#streamlit run market_report.py

		
#streamlit run report_lidrisk.py
def macro_analysis():
    
	import streamlit as st
	import matplotlib.pyplot as plt
		#time.sleep(10)
	from PIL import Image
	#image = Image.open('MM4_Investor_sentiment_V3 (1).jpg')
	image2 = Image.open('20200317-the-psychology-of-a-market-cycle.png')
	image3 = Image.open('saupload_manias_bubbles.jpg')
	#st.text("MACRO IS KING")
	#st.image(image, caption='UNITED STATES CPI INFLATION DATA')
	st.image(image2, caption='EMOTIONAL ROLLERCOASTER.1')
	st.image(image3, caption='EMOTIONAL ROLLERCOASTER.2')
	print("hello world")
	#streamlit run sentiment.py




def social_medialinks():
  # st.set_page_config(page_title="Social Media Links", page_icon=":earth_americas:")
  st.write("Feel free to reach out with the links below")

  SOCIAL_MEDIA = {
      "LinkedIn": (
          "https://www.linkedin.com/in/obare-mokua-robert-omae-b58b4a293?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app"
      ),
      "GitHub": "https://github.com/mokuaomae254",
      "Twitter / X": (
          "https://x.com/cipher_ope28850?t=yFhd-KtESrvS8GJTtOSxig&s=08"
      ),
      "YouTube": "https://www.youtube.com/channel/UCYpLThwlwwUnGmK5q9YCMhA",
   
  }

  FAVICON = {
      "LinkedIn": "https://static-exp1.licdn.com/sc/h/7fx9nkd7mx8avdpqm5hqcbi97",
      "GitHub": "https://github.githubassets.com/favicons/favicon-dark.svg",
      "Twitter / X": "https://abs.twimg.com/favicons/twitter.ico",
      "YouTube": (
          "https://www.youtube.com/s/desktop/0356b1aa/img/favicon_32.png"
      ),
      
  }

  # Add phone contact
  PHONE_ICON = "📞"
  PHONE_NUMBER = "+254717150549"
  st.write(f"{PHONE_ICON} [Contact](tel:{PHONE_NUMBER})")

  # Add social media icons and links
  st.subheader("Social & Professional Profiles")
  for platform, link in SOCIAL_MEDIA.items():
    favicon = FAVICON.get(platform)
    col1, col2 = st.columns([1, 15])
    with col1:
      if favicon:
        st.image(favicon, width=24)
    with col2:
      st.write(f"[{platform}]({link})")

  # Updated Publications & Project Links
  st.subheader("Publications & Projects")
  PUBLICATIONS = {
      "1. Is Crypto in a Bullish Bear Market? Unveiling the Secrets with Elliott Wave Theory": (
          "https://medium.com/@omaerobert158/is-crypto-in-a-bullish-bear-market-unveiling-the-secrets-with-elliott-wave-theory-3670119beaf2"
      ),
      "2. Decoding the $100K: Reality or Illusion?": (
          "https://medium.com/@omaerobert158/decoding-the-100k-reality-or-illusion-7af8094db98e"
      ),
      "3. Is Bitcoin Leading the Market? How We Called the Tops on BTC, SOL, DJIA, NASDAQ, and SPX": (
          "https://medium.com/@omaerobert158/is-bitcoin-leading-the-market-how-we-called-the-tops-on-btc-sol-djia-nasdaq-and-spx-89e9e0e22e5a"
      ),
      "4. The Bitcoin Blueprint: From the $126K Liquidity Trap to the 2026 Macro Bottom 🎯": (
          "https://medium.com/@omaerobert158/the-bitcoin-blueprint-from-the-126k-liquidity-trap-to-the-2026-macro-bottom-%EF%B8%8F-d0f4d6ff5854"
      ),
      "5. Is the Crypto Bottom In? The Wyckoff Spring, Macro Divergence, and My Portfolio Positioning": (
          "https://medium.com/@omaerobert158/is-the-crypto-bottom-in-the-wyckoff-spring-macro-divergence-and-my-portfolio-positioning-7786bbf44439"
      ),
      "6. Crypto Track Record Dashboard": (
          "https://my-crypto-track-record.vercel.app/"
      ),
      "7. Degen Connect Analytics Dashboard (Streamlit)": (
          "https://degen-connect.streamlit.app/"
      ),
  }

  for title, link in PUBLICATIONS.items():
    st.write(f"- [{title}]({link})")



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
def investor_connect():
    	
	st.header("investor connect")
	st.text("share your charts below")
	uploaded_file = st.file_uploader("Choose a file")
def investor_connect1():
		import streamlit as st
		import matplotlib.pyplot as plt
		from PIL import Image

		st.header("Investor Connect")
		st.text("Share your charts below")
		username = st.text_input("Enter your username")
		uploaded_file = st.file_uploader("Choose a file")
		if uploaded_file is not None:
			image = Image.open(uploaded_file)
			st.image(image, caption="EMOTIONAL ROLLERCOASTER.1")
			st.write("Posted by " + username)


#streamlit run investor_connect.py
	
def crypto_portfolio():
		import streamlit as st
		import matplotlib.pyplot as plt
		import warnings
        

		#st.header("Portfolio Design and Risk Management")
		st.subheader("Crypto portfolio")

		income = st.number_input("Enter your annual income:")
		investment = income * 0.1
		st.text("Invest 10% of your income, or $" + str(investment) + ", in crypto.")

		if income > 1000:
			labels = 'LAYER 1', 'LAYER 0', 'LAYER 2', 'LAYER 3','INFRA COINS','AI COINS'
			mycolors = ["yellow", "hotpink", "purple", "green","pink","maroon"]
			explode = (0, 0, 0, 0, 0, 0)
			fig1, ax1 = plt.subplots(figsize=(1, 1))  # Adjust the size as needed
    
			sizes = []
			if income <= 100:
				sizes = [30, 10, 20, 20, 10, 10]
			elif income <= 1000:
				sizes = [10, 20, 20, 20, 10, 20]
			elif income <= 10000:
				sizes = [20, 10, 20, 20, 20, 10]
			elif income <= 100000:
				sizes = [30, 10, 20, 20, 10, 10]
			elif income <= 1000000:
				sizes = [40, 10, 20, 10, 10, 10]
			elif income <= 2000000:
				sizes = [50, 10, 10, 10, 10, 10]
			else:
				st.text("consult with Hedge Funds, private Equity Firms or Venture Capitals as you are regarded as an accredited investor.")
				st.stop()

			fig1, ax1 = plt.subplots()
			ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90, colors=mycolors)
			ax1.axis('equal')
			warnings.filterwarnings("ignore")
            # Your existing plotting code here
			#st.pyplot(fig1)
			st.pyplot(fig1)
			plt.close(fig1)

		else:
			st.text("The minimum amount you can buy in an exchange is 10 USD")

		

		
def dca():
	""" This code uses Streamlit to display the plot instead of using plt.show() at the end. The st.set_style("dark") sets the background of the plot to dark and st.pyplot() to show the plot."""
	import streamlit as st
	import pandas as pd
	import matplotlib.pyplot as plt
	import ta
	import warnings

	def dca_strat():
		import streamlit as st
		import pandas as pd

		st.title("Dollar Cost Averaging Strategy for Bitcoin")

		# Load data for bitcoin prices
		df = pd.read_csv("BCHAIN-MKPRU_updated10.csv")
		df.Date = pd.to_datetime(df.Date)
		df = df[df.Value > 0] # remove rows with closing price of 0 or less
		df.sort_values(by="Date", inplace=True)

		# Get user input for investment amount and interval
		investment_amount = st.number_input("Enter investment amount:", min_value=1, step=1)
		investment_interval = st.number_input("Enter investment interval (in days):", min_value=1, step=1)

		# Get user input for start and end date
		start_date = pd.to_datetime(st.date_input("Enter start date:"))
		end_date = pd.to_datetime(st.date_input("Enter end date:"))

		# Filter dataframe to include only rows within the start and end date range
		df = df[(df.Date >= start_date) & (df.Date <= end_date)]

		# Initialize variables to keep track of investment
		investment_count = 0
		total_invested = 0
		shares_bought = 0

		# Validation check for investment amount
		if investment_amount < 10:
			st.error("Investment amount must be greater than $10")
		else:
			# Iterate through the data and make investments at the specified intervals
			for index, row in df.iterrows():
				if investment_count % investment_interval == 0:
					# Make investment
					investment_count = 0
					shares_bought += investment_amount / row["Value"]
					total_invested += investment_amount
					st.write("Bought {:.8f} BTC for ${} on {}".format(investment_amount/row["Value"], investment_amount, row["Date"]))
				investment_count += 1

			# Print total invested and final value of investment
			if df.empty:
				st.warning("No data within the specified date range")
			else:
				final_value = shares_bought * row["Value"]
				st.write("Total invested: ${}".format(total_invested))
				st.write("Final value of investment: {:.2f}".format(final_value))

	#st.set_style("dark")

	df = pd.read_csv("BCHAIN-MKPRU_updated.csv")[["Date","Value"]]
	df.Date = pd.to_datetime(df.Date)
	df = df[df.Value > 0]
	df.sort_values(by="Date", inplace=True)

	fig, (ax1, ax2) = plt.subplots(2, sharex=True)
	ax1.semilogy(df.Date, df.Value,linewidth=0.5)
	df["rsi"] = ta.momentum.rsi(close=df.Value, window=14)
	ax2.axhline(80, color="yellow",linewidth=0.8)
	ax2.axhline(95, color="red",linewidth=0.8)
	#ax2.axhline(50, color="black",linewidth=0.8)
	ax2.axhline(25, color="green",linewidth=0.8)
	ax2.axhline(10, color="green",linewidth=0.8)
	ax2.text(df.Date.iloc[-1], 85, 'Take Profit', fontsize=8, rotation=0,
			ha='left', va='center',color='blue',
			bbox=dict(boxstyle='round', ec='k', fc='w'))
	ax2.text(df.Date.iloc[-1], 15, 'Build a position', fontsize=8, rotation=0,
			ha='left', va='center',color='blue',
			bbox=dict(boxstyle='round', ec='k', fc='w'))
	if df["rsi"].iloc[-1] > 80:
		# Sell/DCA out
		st.write("RSI is above 80, time to sell/DCA out")
		dca_strat()
		
	elif df["rsi"].iloc[-1] < 25:
		# Buy/DCA in
		st.write("RSI is below 20, time to buy/DCA in")
		dca_strat()
		
	else:
		st.write("RSI is between 20 and 80, hold position")


	ax2.plot(df.Date, df.rsi,linewidth=0.5)
	#st.set_option('deprecation.showPyplotGlobalUse', False)
	warnings.filterwarnings("ignore")
    # Your existing plotting code here
	#st.pyplot()
	st.pyplot(fig)
	plt.close(fig)
	#streamlit run momentum_strat.py



def scrapping():
  import io
  import pandas as pd
  import requests
  import streamlit as st

  try:
    # Mimic browser headers to avoid basic bot blocks
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

    # Triggers HTTPError on Cloudflare 403, 1020, or server error
    r.raise_for_status()

    # Parse scraped HTML
    df = pd.read_html(io.StringIO(r.text))[0]

    # Clean & Filter Data
    df = df[
        ['Coin', 'Price', '1h', '24h', '7d', '24h Volume', 'Market Cap']
    ]

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

    # Save live data locally for topcryptos() fallback
    df.to_csv('coingecko-crypto-data.csv', index=False)

    # Categorize Liquidity Risk
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

    # Stablecoin Overrides
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

    # Display Live Scraped Data
    st.title('Top Cryptocurrencies & Liquidity Analysis (Live Data)')
    st.dataframe(df)

  except Exception as e:
    # When scraping throws 403 or times out, seamlessly switch to static CSV
    st.warning('⚠️ Live scraping failed or blocked. Displaying fallback data.')
    topcryptos()


def topcryptos():
  import pandas as pd
  import streamlit as st

  try:
    df = pd.read_csv('coingecko-crypto-data.csv')
    df = df[['Coin', 'Price', '1h', '24h', '7d', '24h Volume', 'Market Cap']]

    # Categorize Liquidity Risk
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

    st.title('Top Cryptocurrencies & Liquidity Analysis (Static Data)')
    st.dataframe(df)

  except FileNotFoundError:
    st.error(
        '❌ Failed to fetch live data and local dataset'
        ' (coingecko-crypto-data.csv) was not found.'
    )




def topcrypto1():
		import pandas as pd
		import numpy as np
		import streamlit as st

		df=pd.read_csv("coingecko-crypto-data.csv")
		df = df[["Coin","Price","1h","24h","7d","24h Volume","Market Cap"]]


		df.index.Coin = "rank"
		#converting column to list
		#df=pd.read_csv("coingecko-crypto-data.csv")

		# Categorize Liquidity Risk
		liquidity_risk = []
		for index in df.index:
			vol = df["24h Volume"][index]
			mcap = df["Market Cap"][index]

			if pd.isna(vol) or pd.isna(mcap) or mcap == 0:
				liquidity_risk.append("unknown")
			elif vol < (mcap * 0.05):
				liquidity_risk.append("illiquid")
			elif vol <= (mcap * 0.1):
				liquidity_risk.append("fairly liquid")
			elif vol <= (mcap * 0.3):
				liquidity_risk.append("highly liquid")
			elif vol <= (mcap * 0.5):
				liquidity_risk.append("limited long term potential")
			else:
				liquidity_risk.append("stay off")

		df["liquidity_risk"] = liquidity_risk
		stablecoins = [ 
			"Tether", "USDC", "USDS", "Dai", "USD1", "Ethena USDe", "Global Dollar",
			"BlackRock USD Institutional Digital Liquidity Fund", "PayPal USD", "Ripple USD", 
			"USDD", "Falcon USD", "BFUSD", "United Stables", "USDGO", "GHO", "YLDS", 
			"Usual USD", "Figure Heloc", "Circle USYC", "Tether Gold", "Ondo US Dollar Yield", 
			"PAX Gold", "Spiko Amundi Overnight Swap Fund (EUR)", "Spiko EU T-Bills Money Market Fund", 
			"Janus Henderson Anemoy Treasury Fund", "Invesco Short Duration US Government Securities Fund", 
			"Janus Henderson Anemoy AAA CLO Fund"
		]

		df.loc[df["Coin"].isin(stablecoins), "liquidity_risk"] = "stablecoin"

		#displaying the dataset

		st.dataframe(df)

		#streamlit run top_cryptos.py

		
	
def risk_environment():
	import streamlit as st
	import pandas as pd
	import matplotlib.pyplot as plt
	import ta
	import warnings


	df = pd.read_csv("BCHAIN-MKPRU_updated1.csv")[["Date","Value"]]
	df.Date = pd.to_datetime(df.Date)
	df = df[df.Value > 0]
	df.sort_values(by="Date", inplace=True)

	# Calculate the 200-day moving average
	df["ma"] = df["Value"].rolling(window=200).mean()

	fig, ax = plt.subplots()
	ax.semilogy(df.Date, df.Value, linewidth=0.5)
	ax.plot(df.Date, df.ma, color='red', linewidth=1)

	#st.set_option('deprecation.showPyplotGlobalUse', False)
	warnings.filterwarnings("ignore")
    # Your existing plotting code here
	#st.pyplot()
	st.pyplot(fig)
	plt.close(fig)

	# Check if the Bitcoin price is above the 200-day moving average
	if df.Value.iloc[-1] > df.ma.iloc[-1]:
		st.write("We are in a risk-on environment!")
	else:
		st.write("We are in a risk-off environment!")
def scrapping1():
        import pandas as pd
        import requests
        import streamlit as st

        r = requests.get("https://www.coingecko.com/en?page=2")

        df = pd.read_html(r.text)[0]

        df = df[["#","Coin","Price","1h","24h","7d","24h Volume","Market Cap"]]

        df["Coin"] = df["Coin"].apply(lambda x: x.split("  ")[0])
        df["Price"] = df["Price"].apply(lambda x: x.replace(",","").replace("$",""))
        df["Market Cap"] = df["Market Cap"].apply(lambda x: x.replace(",","").replace("$",""))
        df["Market Cap"] = pd.to_numeric(df["Market Cap"]).abs()
        df["24h Volume"]=df["24h Volume"].str.replace(',', '').str.replace('$', '')
        df["24h Volume"] = pd.to_numeric(df["24h Volume"]).abs()

        df["1h"]=df["1h"].str.replace('%', '')
        df["1h"] = pd.to_numeric(df["1h"])
        df["24h"]=df["24h"].str.replace('%', '')
        df["24h"] = pd.to_numeric(df["24h"])
        df["7d"]=df["7d"].str.replace('%', '')
        df["7d"] = pd.to_numeric(df["7d"])

        df.to_csv("coingecko-crypto-data.csv", index=True)
        df.index.Coin = "rank"
        df=pd.read_csv("coingecko-crypto-data.csv")
        liquidity_risk=[ ]
        for index in df.index:
                if (df["24h Volume"][index])<(df["Market Cap"][index]*0.05):
                    liquidity_risk.append("illiquid")

                elif (df["24h Volume"][index])>(df["Market Cap"][index]*0.05) and (df["24h Volume"][index])<=(df["Market Cap"][index]*0.1):
                    liquidity_risk.append("fairly liquid")
                elif (df["24h Volume"][index]) > (df["Market Cap"][index] * 0.1) and (df["24h Volume"][index]) <= (df["Market Cap"][index] * 0.3 ):
                    liquidity_risk.append("highly liquid") 
                
                elif (df["24h Volume"][index]) > (df["Market Cap"][index] * 0.3) and (df["24h Volume"][index]) <= (df["Market Cap"][index] * 0.5):
                    
                    liquidity_risk.append("limited long term potential")
                elif (df["24h Volume"][index]) > (df["Market Cap"][index] * 0.5):
                    liquidity_risk.append("stay off")
                
        df['liquidity_risk'] = liquidity_risk

        df.loc[df['Coin'].isin(['Tether USDT','USD Coin USDC','Binance USD BUSD','Dai DAI','Paxos Standard USDP','TrueUSD TUSD','USDD USDD','Neutrino USD USDN','Gemini Dollar GUSD',"cDAI. cdai","cUSDC. cusdc"]), 'liquidity_risk'] = 'stablecoin'

        st.dataframe(df)
        #print(df)

        #streamlit run coingecko_scrapping.py

def altcoinseason():
	

	import pandas as pd
	import streamlit as st
	import matplotlib.pyplot as plt
	import warnings


	st.title("Altcoin Season Indicator")

	# Read in dataframe
	dataframe = pd.read_csv("coingecko-crypto-data.csv")
	stablecoins = ['Tether USDT','USD Coin USDC','Binance USD BUSD','Dai DAI','Paxos Standard USDP','TrueUSD TUSD','USDD USDD','Neutrino USD USDN','Gemini Dollar GUSD',"cDAI. cdai","cUSDC. cusdc","cETH. ceth","Wrapped Bitcoin WBTC"]
	dataframe = dataframe[~dataframe['Coin'].isin(stablecoins)]
	#Check if the dataframe is empty or not
	if dataframe.empty:
		st.error("Dataframe is empty")

	else:
		# Select top 99 coins
		top_99 = dataframe.head(99)

		# Check if there is "Bitcoin" in the dataframe
		#bitcoin_24H_perc = dataframe.loc[dataframe["Coin"] == "Bitcoin  BTC", "1h"]
		bitcoin_24H_perc = dataframe.iloc[0:1]["1h"]
		
		if bitcoin_24H_perc.empty:
			st.error("Bitcoin not found in dataframe")
		else:
			# Prompt user to input the timeframe
			timeframe = st.selectbox("Select a timeframe:", ["Hourly", "Daily", "Weekly"])

			# Use the selected timeframe to select the appropriate column from the dataframe
			if timeframe == "Hourly":
				selected_column = "1h"
			elif timeframe == "Daily":
				selected_column = "24h"
			elif timeframe == "Weekly":
				selected_column = "7d"
			else:
				st.error("Invalid timeframe selected")
				#return

			# Create a new column that calculates the percentage difference between each coin's selected column and Bitcoin's selected column
			top_99["Difference"] = top_99[selected_column] - bitcoin_24H_perc.values[0]

			# Create a new column that indicates whether each coin outperforms Bitcoin or not
			top_99["Outperforms"] = top_99["Difference"] > 0

			# Count the number of coins that outperform Bitcoin
			outperformers = top_99["Outperforms"].sum()

			# Calculate the percentage of coins that outperform Bitcoin
			percent_outperform = (outperformers / len(top_99)) * 100

			# Create a pie chart to visualize the results
			fig, ax = plt.subplots()
			labels = ["Altcoin Season", "Bitcoin Season"]
			mycolors = ["yellow","b"]
			sizes = [percent_outperform, 100 - percent_outperform]
			#st.set_option('deprecation.showPyplotGlobalUse', False)
			warnings.filterwarnings("ignore")
			# Your existing plotting code here
			plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,colors=mycolors)
			plt.axis('equal')
			#st.pyplot()
			st.pyplot(fig)
			plt.close(fig)

			if percent_outperform > 95 and percent_outperform<100:
				st.warning("The altcoins are so overvalued in the timeframe take profits agressively into stablecoins,BTC and ETH")
			elif percent_outperform > 90 and percent_outperform<=95:
				st.warning("Take some profits into BTC,ETH and stablecoins")
			elif percent_outperform > 80 and percent_outperform<=90:
				st.warning("Research on coins that could have reached a local top (potential short the reap)")
			elif percent_outperform > 10 and percent_outperform<=20:
				st.warning("Research on coins that could have reached a local bottom (potential buy the dip coins gradually)")    
			elif percent_outperform > 5 and percent_outperform<=10:
				st.warning("Sell some BTC into altcoins")
			elif percent_outperform > 1 and percent_outperform<=5:
				st.warning("The altcoins are so undervalued in the timeframe sell stablecoins,BTC and ETH gradually into the altcoins")
			else:
				st.error("stay in your positions")




	#streamlit run altcoinseason_index.py
			
def crypto_quantitative_analysis():
    
	import streamlit as st
	import pandas as pd
	import numpy as np
	import time
	import matplotlib
	#import streamlit as st
	import matplotlib.pyplot as plt
	matplotlib.use('Agg')


	#st.set_page_config(layout="wide")
	tab1, tab2, tab3,tab4,tab5,tab6,tab7,tab8 = st.tabs(["DISCLAIMER","Top Cryptocurrencies","Finding Cycle tops and Bottoms","Sentiment Check","Portfolio Design and Position Sizing","AltSeason Index","Profit taking and DCA","Market Report"])
	with tab1:
		st.header("RISK DISCLAIMER")
		
		st.text(" \n\r       Before deciding to participate in the Crypto market,you should carefully consider your investment objectives, \n\rlevel of experience and risk appetite.Most importantly, do not invest money you cannot afford to lose.\n\rCrypto trading is very risky and you may lose all or some of your investments. \n\rAll the information, analyses, opinions, news, research, prices, or other information  are provided as general market commentary,\n\rand do not constitute or imply any investment advice.\n\rUnder no circumstances will OpenCipher  accept any liability for any loss or damage, including, any loss of profit, \n\rwhich may arise directly or indirectly from the use of or complete reliance on information contained in the given articles or in any analyses.")

	with tab2:
		
		#topcryptos()
		scrapping()
	
	

	with tab3:
		
		st.title("Long Term Position Building & Profit Taking")

		# Asset-level organization sub-tabs
		btc_tab, eth_tab, sol_tab = st.tabs(
			["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"]
		)

		with btc_tab:
			st.subheader("Bitcoin Analytics & DCA Strategies")
			
			btc_weekly_momentum_strat()
			

		with eth_tab:
			st.subheader("Ethereum Analytics")
			
			eth_weekly_momentum_strat()

		with sol_tab:
			st.subheader("Solana Analytics")
			
			sol_weekly_momentum_strat()

			

	with tab4:
		module_sentiment_analysis()
		module_moving_average()
		
		
	with tab5:
		#risk_environment()
		import streamlit as st
		import matplotlib.pyplot as plt
		import warnings


		# Set the option to avoid warnings about global pyplot use
		#st.set_option('deprecation.showPyplotGlobalUse', False)

		age = st.number_input("Enter your age:")

		if 18 <= age <= 200:
			st.text("PORTFOLIO DESIGN AND RISK MANAGEMENT")

			labels = ['CRYPTO', 'SP500', 'DJIA', 'NASDAQ', 'Fine Art']
			mycolors = ["yellow", "hotpink", "b", "#4CAF50", "maroon"]
			explode = (0, 0.1, 0, 0, 0)  # only "explode" the 2nd slice (i.e. 'SP500')

			fig1, ax1 = plt.subplots(figsize=(1, 1))  # Adjust the size as needed
			sizes = []
			
			if 18 <= age <= 30:
				sizes = [40, 15, 15, 15, 15]
			elif 30 < age <= 40:
				sizes = [35, 16.25, 16.25, 16.25, 16.25]
			elif 40 < age <= 50:
				sizes = [30, 17.5, 17.5, 17.5, 17.5]
			elif 50 < age <= 60:
				sizes = [25, 18.75, 18.75, 18.75, 18.75]
			elif 60 < age <= 70:
				sizes = [20, 20, 20, 20, 20]
			elif 70 < age <= 200:
				sizes = [10, 22.5, 22.5, 22.5, 22.5]
			else:
				st.text("Cannot access the model.")
				st.stop()

			
			ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
					shadow=True, startangle=90, colors=mycolors, textprops={'fontsize': 8})
			ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
			warnings.filterwarnings("ignore")
			# Your existing plotting code here

			#st.pyplot(fig1)
			st.pyplot(fig1)
			plt.close(fig1)

		else:
			st.text("Cannot access the model.")
		crypto_portfolio()
		

	with tab6:
		altcoinseason()
		
				
		
	with tab7:
		#altcoinseason()
		st.title("Profit Taking & DCA Strategies")

		# Create sub-tabs inside Tab 8 for asset-level organization
		btc_tab, eth_tab, sol_tab = st.tabs(
			["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"]
		)

		with btc_tab:
			st.subheader("Bitcoin Strategies")
			
			module_rsi_strategy()
			
		with eth_tab:
			eth_momentum_strat()

		with sol_tab:
			sol_momentum_strat()
	
	with tab8:
		market_report()


	
		
		

import hashlib
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



def main():
	"""Simple Login App"""

	#st.title("Simple Login App")
	import streamlit as st
	menu = ["Home","Login","SignUp","Logout","Reset Password","Help","Donation"]
	choice = st.sidebar.selectbox("Menu",menu)

	if choice == "Home":
		#st.subheader("Home")
		#st.write("Welcome to our platform!")
		#topcryptos()
		scrapping()
	elif choice == "Login":
		username = st.sidebar.text_input("User Name")
		password = st.sidebar.text_input("Password",type='password')
		if st.sidebar.checkbox("Login"):
			# if password == '12345':
			create_usertable()
			hashed_pswd = make_hashes(password)

			result = login_user(username,check_hashes(password,hashed_pswd))
			if result:

				st.success("Logged In as {}".format(username))

				#crypto_quantitative_analysis()
				task = st.selectbox("Task",["Qualitative Analysis","Quantitative Analysis","Profiles"])
				if task == "Qualitative Analysis":
					st.subheader("Add Your Post")
					
					investor_connect2()
					#social_medialinks()
					
					comments = st.text_input('Leave a Comment Below: ')
					st.button('Submit Comment')
					social_medialinks()
					

				elif task == "Quantitative Analysis":
		
					
					st.subheader("Quantitative Analysis")
					crypto_quantitative_analysis()
					
					
				elif task == "Profiles":
					
					if(username=="mokua254"):
						st.subheader("User Profiles")
						user_result = view_all_users()
						clean_db = pd.DataFrame(user_result,columns=["Username","Password"])
						st.dataframe(clean_db)
					else:
						st.warning("can not access profiles ")
			else:
				st.warning("Incorrect Username/Password")
	elif choice == "Logout":
			st.subheader("Logout Section")
			logout_button = st.button("Logout")
			if logout_button:
				st.sidebar.empty()
				st.warning("You have been logged out")

	elif choice == "Reset Password":
		st.subheader("Reset Password")
		username = st.text_input("Username")
		old_password = st.text_input("Old Password", type='password')
		new_password = st.text_input("New Password", type='password')

		if st.button("Reset"):
			create_usertable()
			hashed_pswd = make_hashes(old_password)

			result = login_user(username, check_hashes(old_password, hashed_pswd))
			if result:
				reset_password(username, new_password)

			else:
				st.warning("Incorrect Username/Password")


	elif choice == "SignUp":
		st.subheader("Create New Account")
		new_user = st.text_input("Username")
		new_password = st.text_input("Password",type='password')

		if st.button("Signup"):
			create_usertable()
			add_userdata(new_user,make_hashes(new_password))
			st.success("You have successfully created a valid Account")
			st.info("Go to Login Menu to login")

	elif choice == "Help":
		st.subheader("Risk Disclaimer")
		st.text(" \n\r       Risk is fundamental to the investment process, but remains a concept that is not particularly well understood by most regular investors.\n\rThe objective this disclaimer is not only to explain to the investor the nature of the risks involved in the volatile \n\rcrypto market investment vehicles being offered, but also to ensure that there can be no lawsuits if things go badly. ")
		st.subheader("Top 100 Cryptos")
		st.text(" \n\r       The Lindy Effect essentially states that the longer a non-perishable item has been around, the longer it's likely to persist into the future.\n\rThis can translate to technological ideas like cryptocurrencies.This being the first macro correction of bitcoins and other altcoins\n\r most altcoins will trend to zero and give room to quality projects to emerge and loss their market share to existing\n\r fundamentally strong projects.Using the top 100 cryptocurrencies presents a conservative way of investing in this risk off environment.")
		st.subheader("Finding Cycle tops and Bottoms")
		st.text(" \n\r       Headline inflation refers to the overall change in the price level of goods and services in an economy, including all items in the \n\r Consumer Price Index (CPI) basket, which is used to measure inflation. This includes food, energy, and other volatile items that can\n\r experience  significant price swings in short periods of time. Core CPI, on the other hand, is a measure of inflation that \n\rexcludes food and energy prices, which are typically more volatile than other prices. \n\rThis is done to provide a more stable measure of underlying inflation trends, as food and energy prices can be influenced by factors such as \n\rweather events or geopolitical events that can cause temporary price spikes.")
		st.subheader("Sentiment Analysis")
		st.text(" \n\r       Warren Buffett once said that it is wise for investors to be “fearful when others are greedy, and greedy when others are fearful.\n\rThis statement is somewhat of a contrarian view on capital markets and relates directly to the price of an asset: \n\rwhen others are greedy, prices typically boil over, and one should be cautious lest they overpay for an asset that \n\rsubsequently leads to anemic returns.When others are fearful, it may present a good value investment opportunity.\n\rSince the price is what you pay, and value is what you get, paying too high a price can decimate returns.\n\r According to the indicator the ranges between 0-violet -2-light blue present good buy opportunity from a risk to reward \n\rstandpoint(usually calls micro and macro bottoms).According to the indicator the ranges between 14-orange -16-red present good \n\rselling opportunity from a risk to reward standpoint(usually calls micro and macro tops).\n\r The ranges between 4-blue and 12-yellow present an opportunity to hodl your positions for an optimal exit in the future. ")
		st.subheader("Risk Mode")
		st.text(" \n\r       Whenever price action goes above the 200 daily MA we transion to a risk on environment.\n\rTherefore investors should have some skin in the game incase the bottom was in :have exposure to some \n\raltcoins.But whenever the price action is below the 200 daily MA ,investors ought to start derisking\n\r and taking profits Aggressively as were are potentially moving into a risk of environment. ")
		st.subheader("portfolio design and risk management")
		st.text(" \n\r       We help you design an all weather portfolio that can withstand any market conditions . \n\rDepending on your age we help your deploy capital into to the legacy markets and the crypto markets.\n\rDepending on your annual income  we help your deploy capital across the different  crypto narratives.")
		st.subheader("Altcoin Season Index")
		st.text(" \n\r       Altcoin season is a crypto phenomenon, where most cryptocurrency prices surge with the exception of Bitcoin(outperform Bitcoin). \n\rDuring an altcoin season you should a significant exposure to alcoins but in a bitcoin season you should have a significant exposure to Bitcoin.\n\rWhenever more than 80% of the altcoins outperform bitcoins it is usually a good time to start hedging your portfolio.\n\rHedging can be done in two ways :conservatively or Aggressively.\n\rBy being conservative you can sell  a portion of your altcoins  into stablecoins. By taking the Aggressive path you sell a portion of your\n\r altcoins into bitcoin and ethereum(which is a longterm hodl position) or you can open short positions(only for experienced traders). \n\rIf Bitcoin outperforms more than 80% of the altcoins it is usually a good time to start having a significant exposure to some altcoins ,\n\ras this indicates undervaluation of alcoins and vv.")
		st.subheader("Profit Taking and DCA")
		st.text(" \n\r       The success of any retail investor or the trader is measured by how much profits they take home.  \n\rTo achieve this we use the  Dollar-cost averaging (DCA)  an investment strategy in which the intention is to minimize the impact of volatility\n\r when investing or purchasing a fixed large block of a financial asset or instrument over a given period in a fixed  interval.\n\r The strategy is deployed whenever the Relative Strength Index(RSI)is between 80 and 95 or whenever the RSI is below the 25 mark.\n\rHistorically whenever the Relative Strength Index(RSI)is between 80 and 95 it is usually regarded a good time take some partial profits  or\n\r historically whenever the RSI is below the 25 mark it is usually a good time to start building positions(longing,buying coins)")
		st.subheader("Market Report")
		st.text(" \n\r       It shows the top gainers and lossers on the daily,weekly and monthly timeframes. \n\rIf you are using a momentum investing and trend following strategy this could come in handy. \n\rIn addition,if on the daily,weekly or monthly timeframes the top gainers or biggest lossers are stablecoins  this could help predict\n\r the investor behaviour.If stablecoins comprise of the biggest gainers in any timeframe this means investors are moving from\n\r the coins(btc,eth and altcoins)  into the sideline which consequently,means loss of confidence by investors within that timeframe .\n\r If stablecoins comprise of the biggest lossers in any timeframe this means investors are moving from  the sideline into the \n\rcoins(btc,eth and altcoins) which consequently,means gaining of confidence by investors within that timeframe .")
	elif choice == "Donation":
    	
		import streamlit as st

		network_payment_options = {
			'BNB CHAIN': ['BUSD'],
			'SOLANA': ['USDC', 'USDT'],
			'BASE': ['USDBC'],
			'POLYGON': ['USDC', 'DAI', 'USDT'],
			'OPTIMISM': ['USDC'],
			'AVALANCHE': ['EUROC'],
			'ETHEREUM': ['USDC']  # Add options for ETHEREUM
		}

		st.write('Donate to support our development')

		network_options = list(network_payment_options.keys())

		selected_network = st.selectbox('Choose a network:', network_options)

		st.write(f'You selected network: {selected_network}')

		payment_options = network_payment_options.get(selected_network, [])

		if payment_options:
			selected_payment_option = st.selectbox('Choose a payment option:', payment_options)
			st.write(f'You selected payment option: {selected_payment_option}')
			
			# Set receiver address based on the selected network
			if selected_network == 'SOLANA':
				receiver_address = "9N2RjpW6kUdQL9ooU8dobhBeuGjLVVTfjUVmGp1uoghm"
			else:
				receiver_address = "0x1560fE2D29b86a0B0040e96545bDe4531E3feBD3"
			
			# Generate HTML code for the selected payment option
			html_code = f"""
			<script src="https://button.getpip.com/cdn/pipbutton.js"></script>
			<div class="pip-button"
				data-amount="10"
				data-chainNetwork="{selected_network}"
				data-currency="{selected_payment_option}"
				data-label="DONATE"
				data-useLabel="true"
				data-receiver="{receiver_address}"
				data-buttonColor="#1149FF"
				data-buttonTextColor="#FFFFFF"
				data-memo="{receiver_address}">
			</div>
			"""

			st.components.v1.html(html_code, height=600, width=400)
			
		else:
			st.write('No payment options available for the selected network.')

		st.write('Thank you for your donation')


		#streamlit run crypto_donations.py
	

if __name__ == '__main__':
	main()
#streamlit run streamlit_login.py
#streamlit run Degen_connect_test.py

# Megatron1080
#python.exe -m pip install --upgrade pip --user



#run command: streamlit run before_UIUX_design_code.py