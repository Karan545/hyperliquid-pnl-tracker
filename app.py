import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.title("Hyperliquid P&L CSV Exporter")

wallet_address = st.text_input("Enter your Hyperliquid wallet address:")
today = datetime.today()
date_from = st.date_input("From date", today.replace(day=1))
date_to = st.date_input("To date", today)

def get_extended_fills(wallet_address, date_from, date_to):
    try:
        url = "https://api.hyperliquid.xyz/info"
        response = requests.post(url, json={"type": "userFills", "user": wallet_address})
        response.raise_for_status()
        all_fills = response.json()
        from_ts = int(datetime.combine(date_from, datetime.min.time()).timestamp() * 1000)
        to_ts = int(datetime.combine(date_to, datetime.max.time()).timestamp() * 1000)
        return [f for f in all_fills if from_ts <= f['time'] <= to_ts]
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

def format_fills_to_dataframe(fills):
    rows = []
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
    elif date_from > date_to:
        st.warning("The 'From date' must be before the 'To date'.")
    else:
        st.info("Fetching trades... please wait.")
        fills = get_extended_fills(wallet_address, date_from, date_to)
        if not fills:
            st.error("No trades found for this wallet and date range.")
        else:
            df = format_fills_to_dataframe(fills)
            st.success(f"Found {len(df)} trades. Download CSV below:")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f'hyperliquid_pnl_{wallet_address[:8]}_{date_from}_{date_to}.csv',
                mime='text/csv'
            )

