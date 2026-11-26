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