# app.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# ---------- Config: sheet names (match your Google Sheet) ----------
USERS_SHEET = "users"         # header: username, password, role, email
BOOK_SHEET = "book"           # header: title, author, year, image_url
TRANSACTIONS_SHEET = "transactions"  # header: username, title, action, datetime

# ---------- Google Sheets helpers ----------
def get_gspread_client():
    # expects full service account json placed in st.secrets under "gcp_service_account"
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def open_sheet():
    client = get_gspread_client()
    ssid = st.secrets["SPREADSHEET_ID"]
    sh = client.open_by_key(ssid)
    return sh

def ensure_worksheet(spreadsheet, title, headers):
    """Return worksheet with given title. Create and set headers if missing."""
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=20)
        ws.append_row(headers)
    # Make sure headers exist (first row)
    current = ws.row_values(1)
    if not current or len(current) < len(headers) or any(h not in current for h in headers):
        ws.clear()
        ws.append_row(headers)
    return ws

def get_users_ws():
    sh = open_sheet()
    return ensure_worksheet(sh, USERS_SHEET, ["username", "password", "role", "email"])

def get_book_ws():
    sh = open_sheet()
    return ensure_worksheet(sh, BOOK_SHEET, ["title", "author", "year", "image_url"])

def get_tx_ws():
    sh = open_sheet()
    return ensure_worksheet(sh, TRANSACTIONS_SHEET, ["username", "title", "action", "datetime"])

# ---------- CRUD helpers ----------
def read_all_records(ws):
    return ws.get_all_records()  # returns list[dict]

def append_row(ws, row_values):
    ws.append_row(row_values)

def update_row(ws, row_number, values):
    # values should be list aligned with columns
    # update row via range
    cols = len(values)
    start_col = 1
    end_col = cols
    cell_range = gspread.utils.rowcol_to_a1(row_number, start_col) + ":" + gspread.utils.rowcol_to_a1(row_number, end_col)
    ws.update(cell_range, [values])

def delete_row(ws, row_number):
    ws.delete_rows(row_number)

# ---------- Business logic ----------
def find_user(username):
    ws = get_users_ws()
    records = read_all_records(ws)
    for r in records:
        if str(r.get("username", "")).strip() == str(username).strip():
            return r
    return None

def register_user(username, password, email, role="reader"):
    ws = get_users_ws()
    # check exists
    if find_user(username):
        return False, "Username already exists"
    append_row(ws, [username, password, role, email])
    return True, "Registered successfully"

def authenticate(username, password):
    user = find_user(username)
    if user and str(user.get("password", "")) == str(password):
        return True, user.get("role")
    return False, None

# Books
def list_books():
    ws = get_book_ws()
    return read_all_records(ws)

def add_book(title, author, year, image_url=""):
    ws = get_book_ws()
    append_row(ws, [title, author, year, image_url])

def find_book_rows_by_title(title):
    # returns list of (row_index, row_dict)
    ws = get_book_ws()
    records = ws.get_all_records()
    matches = []
    for i, r in enumerate(records):
        if str(title).strip().lower() == str(r.get("title","")).strip().lower():
            matches.append((i+2, r))  # +2 because gspread records start at row 2
    return matches

def edit_book_by_row(row_number, title, author, year, image_url=""):
    ws = get_book_ws()
    update_row(ws, row_number, [title, author, year, image_url])

def delete_book_by_row(row_number):
    ws = get_book_ws()
    delete_row(ws, row_number)

# Transactions
def record_transaction(username, title, action):
    ws = get_tx_ws()
    ts = datetime.utcnow().isoformat()
    append_row(ws, [username, title, action, ts])

# Borrow / Return logic (no availability count in sheet, so we allow multiple borrows)
def borrow_book(username, title):
    # no copy management in your sheet format — just record transaction
    # you can add availability column if you want counts
    record_transaction(username, title, "borrowed")
    return True

def return_book(username, title):
    record_transaction(username, title, "returned")
    return True

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Library (Google Sheets)", layout="wide")
st.title("📚 Library Management (Google Sheets)")

# Session defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

# Authentication UI (sidebar)
if not st.session_state.logged_in:
    st.sidebar.header("Account")
    auth_mode = st.sidebar.radio("Mode", ["Login", "Register"])
    if auth_mode == "Login":
        st.subheader("🔑 Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            ok, role = authenticate(username.strip(), password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.username = username.strip()
                st.session_state.role = role
                st.success(f"Welcome {st.session_state.username} ({role})")
                st.rerun()
            else:
                st.error("Invalid username or password")
    else:
        st.subheader("📝 Register")
        new_username = st.text_input("Choose Username", key="reg_user")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Choose Password", type="password", key="reg_pass")
        new_role = st.selectbox("Role", ["reader", "librarian"], key="reg_role")
        if st.button("Register"):
            ok, msg = register_user(new_username.strip(), new_password, new_email.strip(), new_role)
            if ok:
                st.success(msg + " — please login.")
            else:
                st.error(msg)

# Logged-in UI
else:
    st.sidebar.write(f"👤 {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    # Shared: search box
    st.sidebar.header("Search Books")
    search_q = st.sidebar.text_input("Title or Author")

    # Librarian dashboard
    if st.session_state.role == "librarian":
        st.header("📖 Librarian Dashboard")

        tab_view, tab_add, tab_edit, tab_delete, tab_tx = st.tabs(
            ["View Books", "Add Book", "Edit Book", "Delete Book", "Transactions"]
        )

        # View
        with tab_view:
            st.subheader("All books")
            books = list_books()
            if not books:
                st.info("No books found in sheet.")
            else:
                # apply search if present
                if search_q:
                    books = [b for b in books if search_q.lower() in b.get("title","").lower() or search_q.lower() in b.get("author","").lower()]
                for i, b in enumerate(books):
                    cols = st.columns([1,4])
                    with cols[0]:
                        if b.get("image_url"):
                            try:
                                st.image(b.get("image_url"), width=100)
                            except Exception:
                                st.text("[image error]")
                    with cols[1]:
                        st.markdown(f"**{b.get('title','')}** ({b.get('year','')})")
                        st.write(f"Author: {b.get('author','')}")
                        st.write(f"Row index (for edit/delete): {i+2}")

        # Add
        with tab_add:
            st.subheader("➕ Add Book")
            t_title = st.text_input("Title", key="add_title")
            t_author = st.text_input("Author", key="add_author")
            t_year = st.text_input("Year", key="add_year")
            t_image = st.text_input("Image URL (optional)", key="add_image")
            if st.button("Add Book"):
                if not t_title or not t_author:
                    st.error("Title and author are required")
                else:
                    add_book(t_title.strip(), t_author.strip(), t_year.strip(), t_image.strip())
                    st.success("Book added")
                    st.rerun()

        # Edit
        with tab_edit:
            st.subheader("✏️ Edit Book (select by row index)")
            books = list_books()
            if not books:
                st.info("No books to edit.")
            else:
                options = [f"{i+2}: {b.get('title','')}" for i,b in enumerate(books)]
                choice = st.selectbox("Select book row", options, key="edit_choice")
                row_number = int(choice.split(":")[0])
                # load selected record
                rec = list_books()[row_number-2]
                new_title = st.text_input("Title", value=rec.get("title",""), key="edit_title")
                new_author = st.text_input("Author", value=rec.get("author",""), key="edit_author")
                new_year = st.text_input("Year", value=str(rec.get("year","")), key="edit_year")
                new_image = st.text_input("Image URL", value=rec.get("image_url",""), key="edit_image")
                if st.button("Save changes"):
                    edit_book_by_row(row_number, new_title.strip(), new_author.strip(), new_year.strip(), new_image.strip())
                    st.success("Book updated")
                    st.rerun()

        # Delete
        with tab_delete:
            st.subheader("🗑️ Delete Book")
            books = list_books()
            if not books:
                st.info("No books to delete.")
            else:
                options = [f"{i+2}: {b.get('title','')}" for i,b in enumerate(books)]
                choice = st.selectbox("Select book to delete", options, key="del_choice")
                row_number = int(choice.split(":")[0])
                if st.button("Delete"):
                    delete_book_by_row(row_number)
                    st.warning("Book deleted")
                    st.rerun()

        # Transactions viewer
        with tab_tx:
            st.subheader("📜 Transactions")
            txs = read_all_records(get_tx_ws())
            if not txs:
                st.info("No transactions yet.")
            else:
                for tx in txs:
                    st.write(f"{tx.get('datetime')} — {tx.get('username')} — {tx.get('action')} — {tx.get('title')}")

    # Reader dashboard
    else:
        st.header("📚 Reader Dashboard")
        pages = st.tabs(["Browse/Search", "Borrow / Return", "My Transactions"])
        # Browse/Search
        with pages[0]:
            st.subheader("Library Books")
            books = list_books()
            if search_q:
                books = [b for b in books if search_q.lower() in b.get("title","").lower() or search_q.lower() in b.get("author","").lower()]
            if not books:
                st.info("No books found.")
            else:
                for b in books:
                    cols = st.columns([1,4])
                    with cols[0]:
                        if b.get("image_url"):
                            try:
                                st.image(b.get("image_url"), width=100)
                            except Exception:
                                st.text("[image error]")
                    with cols[1]:
                        st.markdown(f"**{b.get('title','')}** ({b.get('year','')})")
                        st.write(f"Author: {b.get('author','')}")

        # Borrow / Return
        with pages[1]:
            st.subheader("Borrow a book")
            books = list_books()
            titles = [b.get("title","") for b in books]
            sel = st.selectbox("Select book to borrow", titles)
            if st.button("Borrow"):
                borrow_book(st.session_state.username, sel)
                st.success(f"Borrowed '{sel}'")
                st.rerun()

            st.markdown("---")
            st.subheader("Return a book")
            # show user's borrowed titles from transactions
            txs = read_all_records(get_tx_ws())
            borrowed = [t for t in txs if t.get("username")==st.session_state.username and t.get("action")=="borrowed"]
            borrowed_titles = [t.get("title") for t in borrowed]
            if borrowed_titles:
                sel2 = st.selectbox("Select book to return", borrowed_titles, key="return_select")
                if st.button("Return"):
                    return_book(st.session_state.username, sel2)
                    st.success(f"Returned '{sel2}'")
                    st.rerun()
            else:
                st.info("You have no borrowed books recorded.")

        # My Transactions
        with pages[2]:
            st.subheader("My Transactions")
            txs = read_all_records(get_tx_ws())
            my = [t for t in txs if t.get("username")==st.session_state.username]
            if not my:
                st.info("No transactions yet.")
            else:
                for t in my:
                    st.write(f"{t.get('datetime')} — {t.get('action')} — {t.get('title')}")

# end of file
