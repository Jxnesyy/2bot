import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="NFT Bot Live Dashboard", layout="wide")
st.title("🕵️‍♂️ NFT Bot Live Dashboard")

LEADS_CSV = Path("leads.csv")

@st.cache_data(ttl=10)  # cache for 10 seconds
def load_leads():
    if LEADS_CSV.exists():
        return pd.read_csv(LEADS_CSV)
    return pd.DataFrame()

# Load data
df = load_leads()

# Show last 20 leads
st.subheader("Latest Leads")
st.dataframe(df.tail(20), use_container_width=True)

# Show intent breakdown chart
st.subheader("Intent Breakdown")
if not df.empty:
    counts = df['intent'].value_counts().to_frame("count")
    st.bar_chart(counts)

st.write(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
