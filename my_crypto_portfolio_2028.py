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
    st.title("🚀 2026-2028 High-Performance Crypto Portfolio Tracker")
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



my_crypto_portfolio_2028()
#Run command: streamlit run my_crypto_portfolio_2028.py