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
                "Historically, extreme fear presents high-conviction DCA long entry points for quality spot positions."
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
                "Consider taking partial profits on speculative altcoins into stablecoins or BTC."
            )
        else:
            st.error(
                "🚨 **Extreme Greed (Macro Top Risk):** Market is in a state of euphoria. "
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


fear_and_greed_indicator()

# Run command : streamlit run crypto_fear_greed_dashboard.py