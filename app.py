import streamlit as st
import pandas as pd
import numpy as np

# 1. MOBILE PAGE CONFIG
st.set_page_config(page_title="Kalshi Mobile", layout="centered")

st.title("🌁 KSFO Trader")

# 2. DATA LOADING (Cloud Compatible)
@st.cache_data
def load_data():
    try:
        # Tries to find your CSV in the 'data' folder
        return pd.read_csv("Data/ksfo_historical.csv", parse_dates=['date'])
    except:
        st.error("CSV not found. Please upload one below.")
        return None

df = load_data()

# 3. SETTINGS (Sidebar for mobile is a slide-out menu)
with st.sidebar:
    st.header("Admin")
    uploaded_file = st.file_uploader("Update CSV", type="csv")
    bankroll = st.number_input("Bankroll ($)", value=1000.0)

# 4. TRADING INTERFACE
st.subheader("Market Inputs")
col1, col2 = st.columns(2)
with col1:
    strike = st.number_input("Strike (°F)", value=70)
with col2:
    price = st.slider("Market Price", 0.01, 0.99, 0.25, step=0.01)

if df is not None:
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

