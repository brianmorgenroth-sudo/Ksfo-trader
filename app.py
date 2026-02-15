import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="KSFO Kalshi Trader", layout="centered")
st.title("🌉 KSFO Live Edge Terminal")

# --- 2. LOAD HISTORICAL DATA ---
@st.cache_data
def load_historical():
    try:
        # Looking in your data folder
        df = pd.read_csv("data/ksfo_historical.csv", parse_dates=['date'])
        return df
    except Exception as e:
        st.error(f"⚠️ CSV Error: Make sure your file is at 'data/ksfo_historical.csv'. Details: {e}")
        return None

df = load_historical()

# --- 3. FETCH LIVE KALSHI DATA ---
def get_live_kalshi():
    # 'KXHIGHTSFO' is the ticker for San Francisco High Temp
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXHIGHTSFO&status=open"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get('markets', [])
    except:
        return []

# --- 4. THE TRADING ENGINE ---
st.header("Today's Analysis")
bankroll = st.sidebar.number_input("Your Bankroll ($)", value=1000.0)
kelly_fraction = st.sidebar.slider("Kelly Fraction (Safety)", 0.1, 1.0, 0.5)

live_data = get_live_kalshi()

if df is not None:
    # Get historical stats for today's month/day
    today = datetime.now()
    hist_day = df[(df['date'].dt.month == today.month) & (df['date'].dt.day == today.day)]
    
    if live_data:
        for market in live_data:
            # Parse Kalshi Data
            ticker = market['ticker']
            title = market['title'] # e.g. "72° or higher"
            # Logic to extract the number from title like "72°"
            try:
                strike_temp = int(''.join(filter(str.isdigit, title)))
            except:
                continue

            # Kalshi prices are in cents (1-99). We turn them into decimals (0.01 - 0.99)
            yes_price = market['yes_ask'] / 100 
            
            # Calculate Historical Probability
            total_years = len(hist_day)
            hits = len(hist_day[hist_day['TMAX'] >= strike_temp])
            hist_prob = hits / total_years if total_years > 0 else 0
            
            # Calculate Edge
            edge = hist_prob - yes_price
            
            # UI DISPLAY
            with st.expander(f"📊 Market: {title}", expanded=True):
                col1, col2, col3 = st.columns(3)
                col1.metric("Market Price", f"${yes_price:.2f}")
                col2.metric("Hist. Prob", f"{hist_prob:.1%}")
                
                # Highlight if we have an edge
                color = "normal" if edge < 0.1 else "inverse"
                col3.metric("Your Edge", f"{edge:+.1%}", delta=f"{edge:.1%}")

                if edge > 0.05:
                    # Kelly Formula: (bp - q) / b
                    # b is net odds (1/price - 1)
                    b = (1 / yes_price) - 1
                    q = 1 - hist_prob
                    raw_kelly = (b * hist_prob - q) / b
                    suggested_bet = max(0, bankroll * raw_kelly * kelly_fraction)
                    
                    st.success(f"🔥 TRADE ALERT: Bet YES ${suggested_bet:.2f} on {ticker}")
                else:
                    st.info("No clear edge. Waiting for market price to drop.")

    else:
        st.warning("No live Kalshi markets found for SFO right now. (Markets usually open at 9AM ET)")

# --- 5. VISUAL PROOF ---
st.divider()
if df is not None:
    st.subheader(f"20-Year History for {today.strftime('%B %d')}")
    st.bar_chart(hist_day.set_index('date')['TMAX'])
    # Use today's Month/Day to find historical probability
    today = pd.Timestamp.now()
    hist_day = df[(df['date'].dt.month == today.month) & (df['date'].dt.day == today.day)]
    
    if not hist_day.empty:
        prob = len(hist_day[hist_day['TMAX'] >= strike]) / len(hist_day)
        edge = prob - price

        # BIG METRICS (Easy to read on phone)
        st.divider()
        st.metric("Model Probability", f"{prob:.1%}")
        st.metric("Your Edge", f"{edge:+.1%}", delta=f"{edge:.1%}")

        # 5. THE KELLY STAKE
        if edge > 0.10:
            # Simple Kelly: (bp - q) / b
            b = (1 - price) / price
            stake = bankroll * ((b * prob - (1 - prob)) / b)
            st.success(f"✅ BET YES: ${max(0, stake * 0.5):.2f} (Half-Kelly)")
        else:
            st.warning("❌ NO EDGE: Market price is too high.")
    else:
        st.info("No historical data for today's date.")

# 6. VISUAL PROOF
if df is not None:
    st.divider()
    st.write("Historical Temps for this Date:")
    st.bar_chart(hist_day.set_index('date')['TMAX'])

