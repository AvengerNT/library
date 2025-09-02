import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- Authentication ---
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
client = gspread.authorize(creds)

# --- Open Google Sheet ---
SPREADSHEET_ID = st.secrets["general"]["SPREADSHEET_ID"]
sheet = client.open_by_key(SPREADSHEET_ID)

# Get worksheets
users_sheet = sheet.worksheet("users")
books_sheet = sheet.worksheet("book")

# --- Streamlit UI ---
st.title("📚 Library Management System")

menu = st.sidebar.radio("Navigation", ["Login", "Register", "Books"])

# --- Register ---
if menu == "Register":
    st.subheader("Create Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email")
    role = st.selectbox("Role", ["student", "admin"])

    if st.button("Register"):
        users_sheet.append_row([username, password, role, email])
        st.success("✅ Account created successfully!")

# --- Login ---
elif menu == "Login":
    st.subheader("Login")
    username = st.text_input("Username (Login)")
    password = st.text_input("Password (Login)", type="password")

    if st.button("Login"):
        users = users_sheet.get_all_records()
        user = next((u for u in users if u["username"] == username and u["password"] == password), None)

        if user:
            st.success(f"Welcome {user['username']} ({user['role']})")
        else:
            st.error("❌ Invalid credentials")

# --- Books ---
elif menu == "Books":
    st.subheader("Available Books")
    books = books_sheet.get_all_records()

    for book in books:
        st.image(book["image_url"], width=100)
        st.write(f"**{book['title']}** by {book['author']} ({book['year']})")
        st.markdown("---")
