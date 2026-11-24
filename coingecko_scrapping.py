import io
import pandas as pd
import requests
import streamlit as st

# Custom headers to bypass Cloudflare/bot blocks
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

url = "https://www.coingecko.com/en?page=2"
r = requests.get(url, headers=headers)

# Check if the HTTP request was successful (raises 403/404 if blocked)
r.raise_for_status()

# Wrap r.text in io.StringIO to force pandas to treat it as HTML content
df = pd.read_html(io.StringIO(r.text))[0]

# Filter columns
df = df[[ "Coin", "Price", "1h", "24h", "7d", "24h Volume", "Market Cap"]]

# Clean text and numeric formatting
df["Coin"] = df["Coin"].apply(lambda x: str(x).split(" \xa0")[0].split("  ")[0])
df["Price"] = df["Price"].apply(lambda x: str(x).replace(",", "").replace("$", ""))
df["Market Cap"] = df["Market Cap"].apply(lambda x: str(x).replace(",", "").replace("$", ""))
df["Market Cap"] = pd.to_numeric(df["Market Cap"], errors="coerce").abs()

df["24h Volume"] = df["24h Volume"].astype(str).str.replace(",", "").str.replace("$", "")
df["24h Volume"] = pd.to_numeric(df["24h Volume"], errors="coerce").abs()

df["1h"] = pd.to_numeric(df["1h"].astype(str).str.replace("%", ""), errors="coerce")
df["24h"] = pd.to_numeric(df["24h"].astype(str).str.replace("%", ""), errors="coerce")
df["7d"] = pd.to_numeric(df["7d"].astype(str).str.replace("%", ""), errors="coerce")

# Save and reload data
df.to_csv("coingecko-crypto-data.csv", index=False)
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
    "Tether USDT", "USD Coin USDC", "Binance USD BUSD", "Dai DAI",
    "Paxos Standard USDP", "TrueUSD TUSD", "USDD USDD",
    "Neutrino USD USDN", "Gemini Dollar GUSD", "cDAI. cdai", "cUSDC. cusdc"
]
df.loc[df["Coin"].isin(stablecoins), "liquidity_risk"] = "stablecoin"

# Render Streamlit UI
st.title("CoinGecko Market & Liquidity Analysis")
st.dataframe(df)


#streamlit run coingecko_scrapping.py
