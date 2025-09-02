import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ================================
# GOOGLE SHEETS CONNECTION
# ================================
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

# Open Google Sheets
sheet = client.open("LibraryManagementSystem")

# Worksheets
users_ws = sheet.worksheet("Users")
books_ws = sheet.worksheet("Books")
borrow_ws = sheet.worksheet("BorrowRecords")

# ================================
# HELPER FUNCTIONS
# ================================
def get_users():
    return pd.DataFrame(users_ws.get_all_records())

def get_books():
    return pd.DataFrame(books_ws.get_all_records())

def get_borrow_records():
    return pd.DataFrame(borrow_ws.get_all_records())

def add_user(username, password, role):
    users_ws.append_row([username, password, role])

def add_book(title, author, copies):
    books_ws.append_row([title, author, copies])

def borrow_book(user, book_title):
    books = get_books()
    idx = books[books['Title'] == book_title].index
    if not idx.empty and int(books.loc[idx[0], 'Copies']) > 0:
        # Update available copies
        new_copies = int(books.loc[idx[0], 'Copies']) - 1
        books_ws.update_cell(idx[0] + 2, 3, new_copies)  # Row +2 (header offset), Col 3 (Copies)
        # Add borrow record
        borrow_ws.append_row([user, book_title, "Borrowed"])
        return True
    return False

def return_book(user, book_title):
    books = get_books()
    idx = books[books['Title'] == book_title].index
    if not idx.empty:
        new_copies = int(books.loc[idx[0], 'Copies']) + 1
        books_ws.update_cell(idx[0] + 2, 3, new_copies)
        borrow_ws.append_row([user, book_title, "Returned"])
        return True
    return False

# ================================
# APP LOGIC
# ================================
st.title("📚 Library Management System (Google Sheets DB)")

# Session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

# Login
if not st.session_state.logged_in:
    st.subheader("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = get_users()
        user = users[(users["Username"] == username) & (users["Password"] == password)]
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user.iloc[0]["Role"]
            st.success(f"Welcome {username}! You are logged in as {st.session_state.role}.")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# Dashboard
else:
    st.sidebar.title("📌 Menu")
    st.sidebar.write(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.experimental_rerun()

    # Admin/Librarian Features
    if st.session_state.role in ["Admin", "Librarian"]:
        st.subheader("👨‍💼 Manage Users & Books")

        with st.expander("➕ Add User"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            role = st.selectbox("Role", ["User", "Librarian", "Admin"])
            if st.button("Add User"):
                add_user(new_user, new_pass, role)
                st.success(f"User {new_user} added successfully.")

        with st.expander("📖 Add Book"):
            title = st.text_input("Book Title")
            author = st.text_input("Author")
            copies = st.number_input("Copies", min_value=1, step=1)
            if st.button("Add Book"):
                add_book(title, author, copies)
                st.success(f"Book '{title}' added successfully.")

    # User Features
    st.subheader("📚 Library Dashboard")

    option = st.selectbox("Choose Action", ["Search Books", "Borrow Book", "Return Book", "View Borrow Records"])

    if option == "Search Books":
        books = get_books()
        st.dataframe(books)

    elif option == "Borrow Book":
        books = get_books()
        book_list = books["Title"].tolist()
        book_title = st.selectbox("Select Book", book_list)
        if st.button("Borrow"):
            if borrow_book(st.session_state.username, book_title):
                st.success(f"You borrowed '{book_title}' successfully.")
            else:
                st.error("Book not available.")

    elif option == "Return Book":
        records = get_borrow_records()
        borrowed = records[(records["User"] == st.session_state.username) & (records["Status"] == "Borrowed")]
        if not borrowed.empty:
            book_list = borrowed["Book"].tolist()
            book_title = st.selectbox("Select Book to Return", book_list)
            if st.button("Return"):
                if return_book(st.session_state.username, book_title):
                    st.success(f"You returned '{book_title}' successfully.")
        else:
            st.info("You have no borrowed books.")

    elif option == "View Borrow Records":
        records = get_borrow_records()
        st.dataframe(records)
