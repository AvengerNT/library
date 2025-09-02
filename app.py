# test_gs.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import traceback

st.title("Google Sheets Secrets Test")

# check secrets existence
if "gcp_service_account" not in st.secrets:
    st.error("Missing st.secrets['gcp_service_account']. Add it in Streamlit Secrets.")
    st.stop()

if "SPREADSHEET_ID" not in st.secrets:
    st.error("Missing st.secrets['SPREADSHEET_ID']. Add spreadsheet id in secrets.")
    st.stop()

# show safe info (do NOT print private_key)
sa = st.secrets["gcp_service_account"]
st.write("service account client_email:", sa.get("client_email", "MISSING"))
st.write("service account project_id:", sa.get("project_id", "MISSING"))
st.write("SPREADSHEET_ID present:", st.secrets["SPREADSHEET_ID"][:6] + "..." )

# create credentials (google.auth) and test open
try:
    SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(sa, scopes=SCOPE)
    client = gspread.authorize(creds)
    ss = client.open_by_key(st.secrets["SPREADSHEET_ID"])
    st.success("✅ Opened spreadsheet: " + ss.title)
    # list worksheets
    sheets = [w.title for w in ss.worksheets()]
    st.write("Worksheets:", sheets)
except Exception as e:
    st.error("❌ Failed to open spreadsheet.")
    st.write("Exception type:", type(e).__name__)
    st.write("Exception (short):", str(e))
    st.write("Traceback (full):")
    st.text(traceback.format_exc())
