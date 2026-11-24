from bs4 import BeautifulSoup
from pathlib import Path
import warnings
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import ta
import ta.momentum
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import requests


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

    # Parse raw HTML using BeautifulSoup to catch negative indicators/red arrows
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')

    parsed_data = []
    if table:
      rows = table.find_all('tr')
      for row in rows[1:]:  # Skip header row
        cols = row.find_all(['td', 'th'])
        cols_text = [ele.text.strip() for ele in cols]
        if len(cols_text) >= 8:
          # Extract raw text for columns
          # Typically: [#|Rank, Coin, Price, 1h, 24h, 7d, 24h Vol, Market Cap]
          # Let's inspect raw HTML elements for 1h, 24h, 7d to check for negative signs or classes
          raw_cols = cols

          def extract_percentage(col_elem):
            if not col_elem:
              return 0.0
            text_val = col_elem.text.strip().replace('%', '').replace(',', '')
            # Check if there's a downward indicator class, style, or red color indicator
            is_negative = False
            # CoinGecko commonly uses specific classes or text styles for negative changes
            element_html = str(col_elem)
            if (
                'down' in element_html.lower()
                or 'red' in element_html.lower()
                or '-' in text_val
                or 'text-red' in element_html
            ):
              is_negative = True

            # Clean text value to numeric
            clean_val = (
                text_val.replace('-', '')
                .replace('$', '')
                .replace('▲', '')
                .replace('▼', '')
                .strip()
            )
            try:
              val = float(clean_val)
              return -val if is_negative and val > 0 else val
            except ValueError:
              return 0.0

          # Safely map columns based on standard CoinGecko layout indices
          # Adjust indices if your table offset differs
          rank = cols_text[1] if len(cols_text) > 1 else ''
          coin = cols_text[2] if len(cols_text) > 2 else ''
          price = cols_text[3] if len(cols_text) > 3 else ''

          # Find percentage columns by looking at table cells
          # Usually columns index 4, 5, 6 correspond to 1h, 24h, 7d changes
          p_1h = extract_percentage(cols[4]) if len(cols) > 4 else 0.0
          p_24h = extract_percentage(cols[5]) if len(cols) > 5 else 0.0
          p_7d = extract_percentage(cols[6]) if len(cols) > 6 else 0.0

          vol_24h = cols_text[7] if len(cols_text) > 7 else '0'
          mcap = cols_text[8] if len(cols_text) > 8 else '0'

          parsed_data.append({
              '#': rank,
              'Coin': coin,
              'Price': price,
              '1h': p_1h,
              '24h': p_24h,
              '7d': p_7d,
              '24h Volume': vol_24h,
              'Market Cap': mcap,
          })

    # Fallback to standard pd.read_html if custom table scraping fails to populate
    if parsed_data:
      df = pd.DataFrame(parsed_data)
    else:
      df = pd.read_html(io.StringIO(r.text))[0]
      df = df[['#', 'Coin', 'Price', '1h', '24h', '7d', '24h Volume', 'Market Cap']]

    # Clean text formatting columns
    df['Coin'] = df['Coin'].apply(
        lambda x: str(x).split(' \xa0')[0].split('  ')[0]
    )
    df['Price'] = df['Price'].apply(
        lambda x: str(x).replace(',', '').replace('$', '').strip()
    )
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

    df['Market Cap'] = df['Market Cap'].apply(
        lambda x: str(x).replace(',', '').replace('$', '').strip()
    )
    df['Market Cap'] = pd.to_numeric(df['Market Cap'], errors='coerce').abs()

    df['24h Volume'] = (
        df['24h Volume'].astype(str).str.replace(',', '').str.replace('$', '').str.strip()
    )
    df['24h Volume'] = pd.to_numeric(df['24h Volume'], errors='coerce').abs()

    # Ensure percentage columns are numeric floating points retaining negative signs
    for col in ['1h', '24h', '7d']:
      if col in df.columns:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace('%', '').str.strip(), errors='coerce'
        )

    df.to_csv('coingecko-crypto-data.csv', index=False)

    # Liquidity risk processing
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

    render_plotly_table(
        df, title='Top Cryptocurrencies & Liquidity Analysis (Live Data)'
    )

  except Exception as e:
    st.warning(f'⚠️ Live scraping failed or blocked: {e}. Displaying fallback data.')
    #topcryptos()

scrapping()
#streamlit run fixing_scraping.py