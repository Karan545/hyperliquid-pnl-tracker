import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.title("🔥 Hyperliquid P&L CSV Exporter (Debug Mode)")

wallet_address = st.text_input("Enter your Hyperliquid wallet address:")

today = datetime.today()
date_from = st.date_input("From date", today.replace(day=1))
date_to = st.date_input("To date", today)

def get_extended_fills(wallet_address, date_from, date_to):
    try:
        url = "https://api.hyperliquid.xyz/info"
        st.write(f"Requesting fills for: {wallet_address}")
        response = requests.post(url, json={"type": "userFills", "user": wallet_address})
        st.write("API Status Code:", response.status_code)
        raw_data = response.json()
        st.write("API Raw Response:", raw_data)

        response.raise_for_status()
        # Defensive: Handle both list and dict results
        if isinstance(raw_data, dict) and 'error' in raw_data:
            st.error(f"API Error: {raw_data['error']}")
            return []
        if not isinstance(raw_data, list):
            st.error("API didn't return a list of fills.")
            return []

        from_ts = int(datetime.combine(date_from, datetime.min.time()).timestamp() * 1000)
        to_ts = int(datetime.combine(date_to, datetime.max.time()).timestamp() * 1000)
        st.write(f"Filtering fills between {from_ts} and {to_ts} (Unix ms)")

        filtered = [f for f in raw_data if 'time' in f and from_ts <= int(f['time']) <= to_ts]
        st.write(f"Filtered fills (count: {len(filtered)}):", filtered)
        return filtered
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

def format_fills_to_dataframe(fills):
    rows = []
    for fill in fills:
        ts = datetime.fromtimestamp(int(fill['time']) / 1000)
        rows.append({
            'Date': ts.strftime('%Y-%m-%d'),
            'Time': ts.strftime('%H:%M:%S'),
            'Asset': fill.get('coin', ''),
            'Side': 'BUY' if fill.get('side', '') == 'B' else 'SELL',
            'Price': float(fill.get('px', 0)),
            'Size': float(fill.get('sz', 0)),
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
