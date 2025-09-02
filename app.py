import streamlit as st
import json
import os

# ========= JSON FILES =========
USERS_FILE = "users.json"
BOOKS_FILE = "books.json"

# ========= JSON HELPERS =========
def load_json(file_path, default_data):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(default_data, f, indent=4)
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ========= USER MANAGEMENT =========
def login(username, password):
    data = load_json(USERS_FILE, {"users": []})
    for user in data["users"]:
        if user["username"] == username and user["password"] == password:
            return True, user["role"], user
    return False, None, None

def register_user(username, password, email, role="reader"):
    data = load_json(USERS_FILE, {"users": []})
    for user in data["users"]:
        if user["username"] == username:
            return False
    new_id = max([u["id"] for u in data["users"]], default=0) + 1
    data["users"].append({
        "id": new_id,
        "username": username,
        "password": password,
        "role": role,
        "email": email,
        "borrowed_books": []
    })
    save_json(USERS_FILE, data)
    return True

# ========= BOOK MANAGEMENT =========
def get_books():
    return load_json(BOOKS_FILE, [])

# ========= STREAMLIT APP =========
st.set_page_config(page_title="📚 Library Management System", layout="wide")
st.title("📚 Library Management System")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

# LOGIN / REGISTER
if not st.session_state.logged_in:
    menu = st.sidebar.radio("Menu", ["Login", "Register"])

    if menu == "Login":
        st.subheader("🔑 Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            success, role, user = login(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = user["username"]
                st.success(f"✅ Welcome {user['username']} ({role})!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password")

    elif menu == "Register":
        st.subheader("📝 Create New Account")
        username = st.text_input("Choose Username")
        email = st.text_input("Email")
        password = st.text_input("Choose Password", type="password")
        role = st.selectbox("Role", ["reader", "librarian"])
        if st.button("Register"):
            if register_user(username, password, email, role):
                st.success("✅ Registration successful! Please login.")
            else:
                st.error("⚠️ Username already exists")

else:
    st.sidebar.success(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.experimental_rerun()

    # ========= LIBRARIAN =========
    if st.session_state.role == "librarian":
        st.subheader("📖 Manage Books")

        books = get_books()
        if books:
            for book in books:
                st.markdown(f"### {book['title']} ({book['year']})")
                st.write(f"👨‍💼 Author: {book['author']}")
                if book.get("image"):
                    st.image(book["image"], width=200)
                st.divider()
        else:
            st.info("No books available yet.")

    # ========= READER =========
    elif st.session_state.role == "reader":
        st.subheader("📚 Available Books")
        books = get_books()
        if books:
            for book in books:
                st.markdown(f"### {book['title']} ({book['year']})")
                st.write(f"👨‍💼 Author: {book['author']}")
                if book.get("image"):
                    st.image(book["image"], width=200)
                st.divider()
        else:
            st.info("No books available yet.")
