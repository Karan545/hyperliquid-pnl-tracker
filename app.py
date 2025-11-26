import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# App Title
st.title("Hyperliquid P&L CSV Exporter")

# Inputs
wallet_address = st.text_input("Enter Hyperliquid wallet address:")

today = datetime.today()
date_from = st.date_input("From date", today.replace(day=1))
date_to = st.date_input("To date", today)

# Main function: fetch user fills
def get_hyperliquid_fills(wallet_address):
    """
    Fetch all fills from Hyperliquid API for the given wallet address.
    Returns: list of fills (trade dicts), or None if not found/error.
    """
    try:
        url = "https://api.hyperliquid.xyz/info"
        payload = {"type": "userFills", "user": wallet_address}
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            st.error(f"API returned status {response.status_code}.")
            return None
        data = response.json()
        # Defensive: handle improper formats, error keys
        if isinstance(data, dict) and data.get('error'):
            st.error(f"API Error: {data.get('error')}")
            return None
        if not isinstance(data, list):
            st.error("API did not return a fill list. Check wallet address.")
            return None
        return data
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None

# Format fills by date range
def filter_and_format_fills(fills, date_from, date_to):
    from_ts = int(datetime.combine(date_from, datetime.min.time()).timestamp() * 1000)
    to_ts = int(datetime.combine(date_to, datetime.max.time()).timestamp() * 1000)
    filtered = [
        f for f in fills
        if f.get('time') and from_ts <= int(f['time']) <= to_ts
    ]
    rows = []
    for fill in filtered:
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
    df = pd.DataFrame(rows)
    return df

# Main UI logic
if st.button("Generate P&L CSV"):
    if not wallet_address or len(wallet_address) < 8:
        st.warning("Please enter a valid Hyperliquid wallet address.")
    elif date_from > date_to:
        st.warning("'From date' must not be greater than 'To date'.")
    else:
        st.info("Fetching trades... please wait.")
        fills = get_hyperliquid_fills(wallet_address)
        if fills is None:
            st.error("Could not fetch fills (see error above).")
        elif not fills:
            st.warning(f"No trades found for this wallet: {wallet_address}")
        else:
            df = filter_and_format_fills(fills, date_from, date_to)
            if df.empty:
                st.warning(f"No trades in this date range for wallet: {wallet_address}")
            else:
                st.success(f"Found {len(df)} trades. Download CSV below:")
                st.dataframe(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f'hyperliquid_pnl_{wallet_address[:8]}_{date_from}_{date_to}.csv',
                    mime='text/csv'
                )

