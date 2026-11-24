import pandas as pd
import requests
import streamlit as st


# ==========================================
# 1. FETCH LIVE BITCOIN FUNDING RATE
# ==========================================
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_btc_funding_rate():
  """Fetches real-time BTCUSDT Perpetual Funding Rate from Binance Futures API."""
  try:
    # Binance Premium Index endpoint delivers live estimated funding rate
    url = 'https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT'
    res = requests.get(url, timeout=10).json()

    # Funding rate comes back as a string decimal (e.g., "0.0001" = 0.01%)
    last_funding_rate = float(res.get('lastFundingRate', 0.0001))
    next_funding_time = int(res.get('nextFundingTime', 0))
    mark_price = float(res.get('markPrice', 0.0))

    # Convert 8-hour rate into Percentage and Annualized Percentage Rate (APR)
    funding_pct = last_funding_rate * 100
    annualized_apr = funding_pct * 3 * 365  # 3 intervals per day * 365 days

    return {
        'funding_rate_pct': funding_pct,
        'annualized_apr': annualized_apr,
        'mark_price': mark_price,
        'next_funding_time': next_funding_time,
        'status': 'success',
    }
  except Exception as e:
    return {'status': 'error', 'message': str(e)}


# ==========================================
# 2. EVALUATE FUNDING RATE STRATEGY
# ==========================================
def evaluate_funding_condition(funding_pct: float):
  """Evaluates market risk and squeeze setups based on Funding Rate thresholds."""
  # Baseline neutral funding rate on Binance is typically +0.01% (0.0100%)
  if funding_pct >= 0.05:
    return {
        'signal': 'EXTREME BULLISH LEVERAGE / HIGH LONG SQUEEZE RISK',
        'color': 'error',
        'icon': '🚨',
        'description': (
            f"Funding Rate ({funding_pct:+.4f}%) is excessively positive."
            ' Longs are paying extreme fees to shorts. Market is overcrowded;'
            ' elevated risk of a cascading Long Squeeze (sharp flash dip).'
        ),
    }
  elif 0.01 <= funding_pct < 0.05:
    return {
        'signal': 'MODERATE BULLISH BIAS / BALANCED LEVERAGE',
        'color': 'success',
        'icon': '🟢',
        'description': (
            f"Funding Rate ({funding_pct:+.4f}%) is healthy and inline with"
            ' baseline spot demand. Longs pay minor fees to maintain positions.'
        ),
    }
  elif 0.0 < funding_pct < 0.01:
    return {
        'signal': 'NEUTRAL / CAUTIOUS POSITIONING',
        'color': 'info',
        'icon': '⚪',
        'description': (
            f"Funding Rate ({funding_pct:+.4f}%) is below baseline (0.01%)."
            ' Leverage demand is low; market is hesitant or consolidating.'
        ),
    }
  else:  # funding_pct <= 0.0
    return {
        'signal': 'BEARISH SENTIMENT / POTENTIAL SHORT SQUEEZE SETUP',
        'color': 'warning',
        'icon': '⚡',
        'description': (
            f"Funding Rate ({funding_pct:+.4f}%) is Negative. Shorts are"
            ' aggressively paying longs to stay open. High short interest'
            ' creates prime conditions for a explosive Short Squeeze rally.'
        ),
    }


# ==========================================
# 3. STREAMLIT UI RENDERER
# ==========================================
def render_btc_funding_dashboard():
  st.subheader('⚓ Bitcoin Funding Rate Strategy Dashboard')

  data = fetch_btc_funding_rate()

  if data['status'] == 'error':
    st.error(f"Failed to fetch market data: {data['message']}")
    return

  # Sidebar / Manual testing controls
  st.sidebar.markdown('### ⚙️ Funding Rate Test Controls')
  simulate_manual = st.sidebar.checkbox(
      'Simulate Manual Funding Rate', value=False
  )

  if simulate_manual:
    # Slider range covers -0.1% (Extreme Short) to +0.1% (Extreme Long)
    sim_funding_pct = st.sidebar.slider(
        'Simulated 8h Funding Rate (%)',
        min_value=-0.1000,
        max_value=0.1000,
        value=0.0100,
        step=0.0050,
        format='%.4f%%',
    )
    funding_pct = sim_funding_pct
    annualized_apr = funding_pct * 3 * 365
  else:
    funding_pct = data['funding_rate_pct']
    annualized_apr = data['annualized_apr']

  # 1. Display Top KPIs
  col1, col2, col3 = st.columns(3)

  with col1:
    st.metric(
        label='Live BTC Mark Price', value=f"${data['mark_price']:,.2f}"
    )

  with col2:
    # Color delta inversely (High funding = red flag for buyers)
    st.metric(
        label='8-Hour Funding Rate',
        value=f'{funding_pct:+.4f}%',
        delta='Baseline: +0.0100%',
        delta_color='inverse' if funding_pct >= 0.05 else 'normal',
    )

  with col3:
    st.metric(
        label='Annualized Cost / Yield (APR)', value=f'{annualized_apr:+.2f}%'
    )

  st.markdown('---')

  # 2. Evaluate and Render Strategy Signal
  strategy = evaluate_funding_condition(funding_pct)

  if strategy['color'] == 'error':
    st.error(f"{strategy['icon']} **{strategy['signal']}**")
  elif strategy['color'] == 'warning':
    st.warning(f"{strategy['icon']} **{strategy['signal']}**")
  elif strategy['color'] == 'success':
    st.success(f"{strategy['icon']} **{strategy['signal']}**")
  else:
    st.info(f"{strategy['icon']} **{strategy['signal']}**")

  st.write(strategy['description'])

  # 3. Reference Table / Explainer
  with st.expander('ℹ️ How Funding Rate Squeezes Work'):
    st.markdown("""
        | Funding Rate Range | Market Bias | Practical Implication |
        | :--- | :--- | :--- |
        | **> +0.0500%** | Extreme Long Leverage | **Long Squeeze Risk:** Take profits or tighten stop-losses. |
        | **+0.0100% to +0.0500%** | Balanced / Bullish | **Healthy Rally:** Spot and futures demand aligned. |
        | **0.0000% to +0.0100%** | Weak / Neutral | **Consolidation:** Low directional leverage commitment. |
        | **< 0.0000% (Negative)** | Heavy Short Leverage | **Short Squeeze Setup:** Potential explosive reversal upwards. |
        """)


if __name__ == '__main__':
  st.set_page_config(
      page_title='BTC Funding Rate Strategy', page_icon='⚓', layout='wide'
  )
  render_btc_funding_dashboard()


# streamlit run btc_funding_rate_dashboard.py