import streamlit as st
import json
import os

# ========== JSON FILE PATHS ==========
USERS_FILE = "users.json"
BOOKS_FILE = "books.json"

# ========== JSON HELPERS ==========
def load_json(file_path, default_data):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(default_data, f, indent=4)
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ========== USER MANAGEMENT ==========
def login(username, password):
    users = load_json(USERS_FILE, {"users": []})
    for user in users["users"]:
        if user["username"] == username and user["password"] == password:
            return True, user["role"]
    return False, None

def register_user(username, password, role="reader"):
    users = load_json(USERS_FILE, {"users": []})
    for user in users["users"]:
        if user["username"] == username:
            return False
    users["users"].append({"username": username, "password": password, "role": role})
    save_json(USERS_FILE, users)
    return True

# ========== BOOK MANAGEMENT ==========
def add_book(title, author, year, photo_url=None):
    books = load_json(BOOKS_FILE, {"books": []})
    book_id = len(books["books"]) + 1
    books["books"].append({
        "id": book_id,
        "title": title,
        "author": author,
        "year": year,
        "photo": photo_url
    })
    save_json(BOOKS_FILE, books)

def edit_book(book_id, title, author, year, photo_url=None):
    books = load_json(BOOKS_FILE, {"books": []})
    for book in books["books"]:
        if book["id"] == book_id:
            book["title"] = title
            book["author"] = author
            book["year"] = year
            book["photo"] = photo_url
    save_json(BOOKS_FILE, books)

def delete_book(book_id):
    books = load_json(BOOKS_FILE, {"books": []})
    books["books"] = [b for b in books["books"] if b["id"] != book_id]
    save_json(BOOKS_FILE, books)

def get_books():
    return load_json(BOOKS_FILE, {"books": []})["books"]

# ========== STREAMLIT APP ==========
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
            success, role = login(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = username
                st.success(f"✅ Welcome {username} ({role})!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password")

    elif menu == "Register":
        st.subheader("📝 Create New Account")
        username = st.text_input("Choose Username")
        password = st.text_input("Choose Password", type="password")
        role = st.selectbox("Role", ["reader", "librarian"])
        if st.button("Register"):
            if register_user(username, password, role):
                st.success("✅ Registration successful! Please login.")
            else:
                st.error("⚠️ Username already exists")

else:
    st.sidebar.success(f"Logged in as: {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.experimental_rerun()

    # ========== LIBRARIAN ==========
    if st.session_state.role == "librarian":
        st.subheader("📖 Manage Books")

        tab1, tab2, tab3 = st.tabs(["➕ Add Book", "✏️ Edit Book", "🗑️ Delete Book"])

        # Add Book
        with tab1:
            title = st.text_input("Book Title")
            author = st.text_input("Author")
            year = st.text_input("Year")
            photo = st.text_input("Photo URL (Optional)")
            if st.button("Add Book"):
                add_book(title, author, year, photo)
                st.success("✅ Book added successfully!")

        # Edit Book
        with tab2:
            books = get_books()
            if books:
                book_choice = st.selectbox("Select Book", [f"{b['id']} - {b['title']}" for b in books])
                book_id = int(book_choice.split(" - ")[0])
                book = next(b for b in books if b["id"] == book_id)

                new_title = st.text_input("New Title", value=book["title"])
                new_author = st.text_input("New Author", value=book["author"])
                new_year = st.text_input("New Year", value=book["year"])
                new_photo = st.text_input("New Photo URL", value=book.get("photo", ""))

                if st.button("Save Changes"):
                    edit_book(book_id, new_title, new_author, new_year, new_photo)
                    st.success("✅ Book updated successfully!")
            else:
                st.warning("No books available to edit.")

        # Delete Book
        with tab3:
            books = get_books()
            if books:
                book_choice = st.selectbox("Select Book to Delete", [f"{b['id']} - {b['title']}" for b in books])
                book_id = int(book_choice.split(" - ")[0])
                if st.button("Delete Book"):
                    delete_book(book_id)
                    st.success("✅ Book deleted successfully!")
            else:
                st.warning("No books available to delete.")

    # ========== READER ==========
    elif st.session_state.role == "reader":
        st.subheader("📚 Available Books")
        books = get_books()
        if books:
            for book in books:
                st.markdown(f"### {book['title']} ({book['year']})")
                st.write(f"👨‍💼 Author: {book['author']}")
                if book.get("photo"):
                    st.image(book["photo"], width=200)
                st.divider()
        else:
            st.info("No books available yet.")
