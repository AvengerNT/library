import streamlit as st
import json
import os

BOOKS_FILE = "books.json"
USERS_FILE = "users.json"

# ---------- Utility Functions ----------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def login(username, password):
    users = load_json(USERS_FILE)
    for user in users:
        if user["username"] == username and user["password"] == password:
            return True, user["role"]
    return False, None

# ---------- Login Page ----------
def login_page():
    st.title("📚 Library Management System")
    st.subheader("Login to Your Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        success, role = login(username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.username = username
            st.success(f"Welcome {username} ({role})!")
        else:
            st.error("Invalid username or password")

# ---------- Librarian Dashboard ----------
def librarian_dashboard():
    st.title("👩‍💼 Librarian Dashboard")

    menu = st.sidebar.radio("Menu", ["View Books", "Add Book", "Edit/Delete Book", "Logout"])

    books = load_json(BOOKS_FILE)

    if menu == "View Books":
        st.subheader("All Books in Library")
        for book in books:
            st.write(f"**{book['title']}** by {book['author']} ({book['year']})")
            if "image" in book and book["image"]:
                st.image(book["image"], width=100)

    elif menu == "Add Book":
        st.subheader("➕ Add a New Book")
        title = st.text_input("Book Title")
        author = st.text_input("Author")
        year = st.number_input("Year", min_value=1500, max_value=2100, step=1)
        image = st.file_uploader("Upload Book Cover", type=["png", "jpg", "jpeg"])

        if st.button("Save Book"):
            new_book = {
                "title": title,
                "author": author,
                "year": year,
                "image": None
            }
            if image:
                img_path = os.path.join("uploads", image.name)
                os.makedirs("uploads", exist_ok=True)
                with open(img_path, "wb") as f:
                    f.write(image.getbuffer())
                new_book["image"] = img_path

            books.append(new_book)
            save_json(BOOKS_FILE, books)
            st.success("Book added successfully!")

    elif menu == "Edit/Delete Book":
        st.subheader("✏️ Edit or Delete Books")
        if books:
            book_titles = [book["title"] for book in books]
            choice = st.selectbox("Select a Book", book_titles)
            selected_book = next((b for b in books if b["title"] == choice), None)

            if selected_book:
                new_title = st.text_input("Book Title", selected_book["title"])
                new_author = st.text_input("Author", selected_book["author"])
                new_year = st.number_input("Year", value=selected_book["year"], min_value=1500, max_value=2100, step=1)

                if st.button("Update Book"):
                    selected_book["title"] = new_title
                    selected_book["author"] = new_author
                    selected_book["year"] = new_year
                    save_json(BOOKS_FILE, books)
                    st.success("Book updated successfully!")

                if st.button("Delete Book"):
                    books.remove(selected_book)
                    save_json(BOOKS_FILE, books)
                    st.warning("Book deleted successfully!")

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

# ---------- Reader Dashboard ----------
def reader_dashboard():
    st.title("📖 Reader Dashboard")

    menu = st.sidebar.radio("Menu", ["View Books", "Logout"])
    books = load_json(BOOKS_FILE)

    if menu == "View Books":
        st.subheader("Available Books")
        for book in books:
            st.write(f"**{book['title']}** by {book['author']} ({book['year']})")
            if "image" in book and book["image"]:
                st.image(book["image"], width=100)

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

# ---------- Main App ----------
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None

    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.role == "librarian":
            librarian_dashboard()
        else:
            reader_dashboard()

if __name__ == "__main__":
    main()
