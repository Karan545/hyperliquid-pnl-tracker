import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.title("🔥 Hyperliquid P&L CSV Exporter")

wallet_address = st.text_input("Enter your Hyperliquid wallet address:")
days = st.slider("Number of days to analyze", 1, 90, 30)

def get_extended_fills(wallet_address, days=30):
    try:
        url = "https://api.hyperliquid.xyz/info"
        response = requests.post(url, json={"type": "userFills", "user": wallet_address})
        response.raise_for_status()
        all_fills = response.json()
        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp() * 1000
        return [f for f in all_fills if f['time'] >= cutoff_time]
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

def format_fills_to_dataframe(fills):
    rows = []
    cumulative_pnl = 0
    for fill in fills:
        ts = datetime.fromtimestamp(fill['time'] / 1000)
        rows.append({
            'Date': ts.strftime('%Y-%m-%d'),
            'Time': ts.strftime('%H:%M:%S'),
            'Asset': fill['coin'],
            'Side': 'BUY' if fill['side'] == 'B' else 'SELL',
            'Price': float(fill['px']),
            'Size': float(fill['sz']),
            'Fee': float(fill.get('fee', 0)),
            'Closed P&L': float(fill.get('closedPnl', 0))
        })
    return pd.DataFrame(rows)

if st.button("Generate P&L CSV"):
    if wallet_address.strip() == "":
        st.warning("Please enter your wallet address.")
    else:
        st.info("Fetching trades... please wait.")
        fills = get_extended_fills(wallet_address, days)
        if not fills:
            st.error("No trades found for this wallet.")
        else:
            df = format_fills_to_dataframe(fills)
            st.success("Success! Download CSV below:")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f'hyperliquid_pnl_{wallet_address[:8]}.csv',
                mime='text/csv'
            )
