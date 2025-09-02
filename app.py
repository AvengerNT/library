import streamlit as st
import json
import os
from datetime import datetime

BOOK_FILE = "books.json"
USER_FILE = "users.json"
IMAGE_FOLDER = "book_images"

# Ensure image folder exists
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ---------------- Load & Save JSON ----------------
def load_json(file, default_data):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default_data, f, indent=4)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

books = load_json(BOOK_FILE, [])
users = load_json(USER_FILE, [])

# ---------------- User Authentication ----------------
def signup(username, password, role):
    for user in users:
        if user["username"] == username:
            return False, "Username already exists!"
    users.append({"username": username, "password": password, "role": role})
    save_json(USER_FILE, users)
    return True, "Signup successful!"

def login(username, password):
    for user in users:
        if user["username"] == username and user["password"] == password:
            return True, user["role"]
    return False, None

# ---------------- Book Management ----------------
def add_book(title, author, year, image_url=None, image_file=None):
    if image_file:
        file_path = os.path.join(IMAGE_FOLDER, image_file.name)
        with open(file_path, "wb") as f:
            f.write(image_file.getbuffer())
        image_url = file_path
    new_book = {
        "title": title,
        "author": author,
        "year": year,
        "image": image_url if image_url else ""
    }
    books.append(new_book)
    save_json(BOOK_FILE, books)

def edit_book(old_title, new_title, author, year, image_url=None, image_file=None):
    for book in books:
        if book["title"] == old_title:
            book["title"] = new_title
            book["author"] = author
            book["year"] = year
            if image_file:
                file_path = os.path.join(IMAGE_FOLDER, image_file.name)
                with open(file_path, "wb") as f:
                    f.write(image_file.getbuffer())
                book["image"] = file_path
            elif image_url:
                book["image"] = image_url
    save_json(BOOK_FILE, books)

def delete_book(title):
    global books
    books = [book for book in books if book["title"] != title]
    save_json(BOOK_FILE, books)

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="📚 Library System", layout="wide")
st.title("📚 Library Management System")

menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Signup":
    st.subheader("Create an Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["reader", "librarian"])
    if st.button("Signup"):
        success, msg = signup(new_user, new_pass, role)
        st.success(msg) if success else st.error(msg)

elif choice == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        success, role = login(username, password)
        if success:
            st.session_state["user"] = username
            st.session_state["role"] = role
            st.success(f"Welcome {username}! You are logged in as {role}.")
        else:
            st.error("Invalid credentials")

# ---------------- Dashboards ----------------
if "user" in st.session_state:
    st.sidebar.write(f"👤 Logged in as: {st.session_state['user']} ({st.session_state['role']})")

    # ----- Librarian -----
    if st.session_state["role"] == "librarian":
        st.header("📖 Librarian Dashboard")

        st.subheader("Add New Book")
        title = st.text_input("Book Title")
        author = st.text_input("Author")
        year = st.number_input("Year", min_value=0, max_value=datetime.now().year, step=1)
        image_url = st.text_input("Image URL (optional)")
        image_file = st.file_uploader("Or Upload Book Image", type=["jpg", "png", "jpeg"])
        if st.button("Add Book"):
            add_book(title, author, year, image_url, image_file)
            st.success("Book added successfully!")

        st.subheader("Edit Book")
        book_titles = [b["title"] for b in books]
        if book_titles:
            book_to_edit = st.selectbox("Select Book to Edit", book_titles)
            book_data = next(b for b in books if b["title"] == book_to_edit)
            new_title = st.text_input("New Title", value=book_data["title"])
            new_author = st.text_input("New Author", value=book_data["author"])
            new_year = st.number_input("New Year", value=book_data["year"], step=1)
            new_image_url = st.text_input("New Image URL", value=book_data["image"])
            new_image_file = st.file_uploader("Upload New Image (optional)", type=["jpg", "png", "jpeg"], key="edit")
            if st.button("Save Changes"):
                edit_book(book_to_edit, new_title, new_author, new_year, new_image_url, new_image_file)
                st.success("Book updated successfully!")

        st.subheader("Delete Book")
        if book_titles:
            book_to_delete = st.selectbox("Select Book to Delete", book_titles, key="delete")
            if st.button("Delete Book"):
                delete_book(book_to_delete)
                st.success("Book deleted successfully!")

    # ----- Reader -----
    elif st.session_state["role"] == "reader":
        st.header("📚 Reader Dashboard")

        st.subheader("Available Books")
        search = st.text_input("Search books by title/author")
        filtered_books = [b for b in books if search.lower() in b["title"].lower() or search.lower() in b["author"].lower()] if search else books

        for book in filtered_books:
            cols = st.columns([1, 3])
            with cols[0]:
                if book["image"]:
                    st.image(book["image"], width=120)
            with cols[1]:
                st.write(f"**{book['title']}**")
                st.write(f"Author: {book['author']}")
                st.write(f"Year: {book['year']}")
