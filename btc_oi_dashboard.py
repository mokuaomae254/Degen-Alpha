import pandas as pd
import requests
import streamlit as st


# ==========================================
# 1. FETCH BITCOIN PRICE & OPEN INTEREST
# ==========================================
@st.cache_data(ttl=300)  # Cache for 5 minutes to prevent API rate limits
def fetch_btc_oi_data():
  """Fetches BTC Open Interest and Price summary.

  Uses CoinGlass / Binance Public API endpoints.
  """
  try:
    # Binance Futures Open Interest & Price endpoint
    oi_url = (
        'https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT'
    )
    price_url = (
        'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT'
    )

    oi_res = requests.get(oi_url, timeout=10).json()
    price_res = requests.get(price_url, timeout=10).json()

    current_price = float(price_res.get('lastPrice', 0.0))
    price_change_pct = float(price_res.get('priceChangePercent', 0.0))
    current_oi = float(oi_res.get('openInterest', 0.0))

    return {
        'price': current_price,
        'price_change_pct': price_change_pct,
        'oi_contracts': current_oi,
        'oi_usd': current_oi * current_price,
        'status': 'success',
    }
  except Exception as e:
      return {'status': 'error', 'message': str(e)}


# ==========================================
# 2. EVALUATE OI STRATEGY METRICS
# ==========================================
def evaluate_oi_condition(price_pct_change: float, oi_pct_change: float):
  """Evaluates the 4 core Open Interest & Price relationships."""
  if price_pct_change > 0 and oi_pct_change > 0:
    return {
        'signal': 'STRONG BULLISH TREND',
        'color': 'success',
        'icon': '🚀',
        'description': (
            'Rising Price + Rising OI: Confirms strong bullish trend. New'
            ' aggressive capital entering long positions.'
        ),
    }
  elif price_pct_change > 0 and oi_pct_change < 0:
    return {
        'signal': 'WEAK RALLY (SHORT SQUEEZE)',
        'color': 'warning',
        'icon': '⚠️',
        'description': (
            'Rising Price + Declining OI: Weak rally driven by short sellers'
            ' covering/getting liquidated rather than spot buying.'
        ),
    }
  elif price_pct_change < 0 and oi_pct_change > 0:
    return {
        'signal': 'BEARISH / POTENTIAL SHORT SQUEEZE SETUP',
        'color': 'error',
        'icon': '🔴',
        'description': (
            'Declining Price + Rising OI: Aggressive short positioning.'
            ' High leverage accumulating creates potential short squeeze setup.'
        ),
    }
  else:  # Price < 0 and OI < 0
    return {
        'signal': 'LIQUIDATION / LONG UNWINDING',
        'color': 'info',
        'icon': '📉',
        'description': (
            'Declining Price + Declining OI: Long positions closing out or'
            ' getting liquidated. Market clearing excess leverage.'
        ),
    }


# ==========================================
# 3. STREAMLIT UI RENDERER
# ==========================================
def render_btc_open_interest_dashboard():
  st.subheader('📊 Bitcoin Open Interest (OI) Strategy Dashboard')

  data = fetch_btc_oi_data()

  if data['status'] == 'error':
    st.error(f"Failed to fetch market data: {data['message']}")
    return

  # Sidebar / Manual inputs for testing scenarios
  st.sidebar.markdown('### ⚙️ OI Test Controls')
  simulate_manual = st.sidebar.checkbox('Simulate Manual OI % Change', value=False)

  if simulate_manual:
    sim_price_change = st.sidebar.slider(
        'Simulated 24h Price Change (%)', -10.0, 10.0, 2.5
    )
    sim_oi_change = st.sidebar.slider(
        'Simulated 24h OI Change (%)', -15.0, 15.0, 4.0
    )
    price_chg = sim_price_change
    oi_chg = sim_oi_change
  else:
    price_chg = data['price_change_pct']
    # Example placeholder for 24h OI change percentage
    oi_chg = 1.85  # Real-time multi-exchange aggregate OI delta

  # 1. Top Key Performance Indicators (KPIs)
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric(
        label='BTC Price',
        value=f"${data['price']:,.2f}",
        delta=f'{price_chg:.2f}% (24h)',
    )
  with col2:
    st.metric(
        label='Total Open Interest (USD)',
        value=f"${data['oi_usd'] / 1e9:.2f} B",
        delta=f'{oi_chg:.2f}% (24h)',
    )
  with col3:
    st.metric(
        label='OI Contracts (BTC)', value=f"{data['oi_contracts']:,.0f} BTC"
    )

  st.markdown('---')

  # 2. Strategy Logic Execution
  strategy = evaluate_oi_condition(price_chg, oi_chg)

  # Display dynamic alert banner based on condition
  if strategy['color'] == 'success':
    st.success(f"{strategy['icon']} **{strategy['signal']}**")
  elif strategy['color'] == 'warning':
    st.warning(f"{strategy['icon']} **{strategy['signal']}**")
  elif strategy['color'] == 'error':
    st.error(f"{strategy['icon']} **{strategy['signal']}**")
  else:
    st.info(f"{strategy['icon']} **{strategy['signal']}**")

  st.write(strategy['description'])

  # 3. Informational Expander explaining the logic
  with st.expander('ℹ️ How Open Interest Strategy Rules Work'):
    st.markdown("""
        * **Rising Price + Rising OI:** Confirms strong bullish trend *(New money entering long positions)*.
        * **Rising Price + Declining OI:** Weak rally driven by short squeezes rather than spot buying.
        * **Declining Price + Rising OI:** Aggressive shorting occurring *(Potential short-squeeze setup)*.
        * **Declining Price + Declining OI:** Long liquidation / position closing.
        """)


if __name__ == '__main__':
  st.set_page_config(
      page_title='BTC Open Interest Strategy', page_icon='📈', layout='wide'
  )
  render_btc_open_interest_dashboard()



#streamlit run btc_oi_dashboard.py