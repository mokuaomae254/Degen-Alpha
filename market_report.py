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