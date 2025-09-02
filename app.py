import streamlit as st
import json
import os
import time

# ---------- Files & folders ----------
USERS_FILE = "users.json"   # format: { "users": [ ... ] }  (you insisted)
BOOKS_FILE = "books.json"   # format: [ {...}, {...} ]     (you insisted)
IMAGE_FOLDER = "book_images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ---------- Helpers ----------
def load_json(file_path, default):
    """Load JSON, create with default if missing."""
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(default, f, indent=4)
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ---------- Users (strictly use {"users":[...]}) ----------
def load_users():
    return load_json(USERS_FILE, {"users": []})

def save_users(data):
    save_json(USERS_FILE, data)

def login(username, password):
    data = load_users()
    for user in data.get("users", []):
        if user.get("username") == username and user.get("password") == password:
            return True, user.get("role"), user
    return False, None, None

def register_user(username, password, email, role="reader"):
    data = load_users()
    # check exist
    for u in data.get("users", []):
        if u.get("username") == username:
            return False, "Username already exists"
    new_id = max([u.get("id", 0) for u in data.get("users", [])], default=0) + 1
    new_user = {
        "id": new_id,
        "username": username,
        "password": password,
        "role": role,
        "email": email,
        "borrowed_books": []
    }
    data["users"].append(new_user)
    save_users(data)
    return True, "Registered successfully"

# ---------- Books (strictly a list) ----------
def load_books():
    # books.json is a list in your format
    return load_json(BOOKS_FILE, [])

def save_books(books_list):
    # preserve list format
    save_json(BOOKS_FILE, books_list)

def add_book(title, author, year, image_url=None, image_file=None):
    books = load_books()
    image_field = image_url or ""
    if image_file is not None:
        safe_name = image_file.name.replace(" ", "_")
        fname = f"{int(time.time())}_{safe_name}"
        path = os.path.join(IMAGE_FOLDER, fname)
        with open(path, "wb") as f:
            f.write(image_file.getbuffer())
        image_field = path
    new_book = {
        "title": title,
        "author": author,
        "year": year,
        "image": image_field
    }
    books.append(new_book)
    save_books(books)

def edit_book(index, title, author, year, image_url=None, image_file=None):
    books = load_books()
    if index < 0 or index >= len(books):
        return False
    image_field = books[index].get("image", "")
    if image_file is not None:
        safe_name = image_file.name.replace(" ", "_")
        fname = f"{int(time.time())}_{safe_name}"
        path = os.path.join(IMAGE_FOLDER, fname)
        with open(path, "wb") as f:
            f.write(image_file.getbuffer())
        image_field = path
    elif image_url is not None:
        image_field = image_url
    # update fields (preserve the list-only structure)
    books[index]["title"] = title
    books[index]["author"] = author
    books[index]["year"] = year
    books[index]["image"] = image_field
    save_books(books)
    return True

def delete_book(index):
    books = load_books()
    if 0 <= index < len(books):
        books.pop(index)
        save_books(books)
        return True
    return False

# ---------- UI ----------
st.set_page_config(page_title="Library", layout="wide")
st.title("📚 Library Management System")

# session defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "user_obj" not in st.session_state:
    st.session_state.user_obj = None

# ------ Authentication screens ------
if not st.session_state.logged_in:
    st.sidebar.title("Account")
    mode = st.sidebar.radio("Mode", ("Login", "Register"))

    if mode == "Login":
        st.subheader("🔑 Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            success, role, user = login(username.strip(), password)
            if success:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = user["username"]
                st.session_state.user_obj = user
                st.success(f"Welcome {user['username']} ({role})")
                st.rerun()  # safe replacement for experimental_rerun
            else:
                st.error("Invalid username or password")

    else:
        st.subheader("📝 Register")
        new_username = st.text_input("Choose username", key="reg_user")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Choose password", type="password", key="reg_pass")
        new_role = st.selectbox("Role", ["reader", "librarian"], key="reg_role")
        if st.button("Register"):
            ok, msg = register_user(new_username.strip(), new_password, new_email.strip(), new_role)
            if ok:
                st.success(msg + ". Now login.")
            else:
                st.error(msg)

# ------ Logged-in UI ------
else:
    st.sidebar.write(f"👤 {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.user_obj = None
        st.rerun()

    # Librarian area
    if st.session_state.role == "librarian":
        st.header("📖 Librarian Dashboard")

        tab = st.tabs(["View Books", "Add Book", "Edit Book", "Delete Book", "Manage Borrowing"])
        # Tab 0: View
        with tab[0]:
            st.subheader("All books (from books.json)")
            books = load_books()
            if not books:
                st.info("No books in library.")
            for i, b in enumerate(books):
                cols = st.columns([1, 4])
                with cols[0]:
                    if b.get("image"):
                        try:
                            st.image(b["image"], width=110)
                        except Exception:
                            st.text("[image load error]")
                with cols[1]:
                    st.markdown(f"**{b.get('title','')}** ({b.get('year','')})")
                    st.write(f"Author: {b.get('author','')}")
                    st.write(f"Index: {i}")

        # Tab 1: Add
        with tab[1]:
            st.subheader("➕ Add a book (keeps the same list-format)")
            a_title = st.text_input("Title", key="add_title")
            a_author = st.text_input("Author", key="add_author")
            a_year = st.text_input("Year", key="add_year")
            a_image_url = st.text_input("Image URL (optional)", key="add_image_url")
            a_image_file = st.file_uploader("Or upload cover image (jpg/png)", type=["jpg","jpeg","png"], key="add_image_file")
            if st.button("Add book", key="add_book_btn"):
                if not a_title or not a_author:
                    st.error("Title and Author required")
                else:
                    add_book(a_title.strip(), a_author.strip(), a_year.strip(), a_image_url.strip() if a_image_url else None, a_image_file)
                    st.success("Book added")
                    st.rerun()

        # Tab 2: Edit
        with tab[2]:
            st.subheader("✏️ Edit a book (select by index)")
            books = load_books()
            if not books:
                st.info("No books to edit.")
            else:
                options = [f"{i+1}. {b.get('title','')}" for i,b in enumerate(books)]
                sel = st.selectbox("Select book", options, key="edit_select")
                idx = int(sel.split(".")[0]) - 1
                b = books[idx]
                e_title = st.text_input("Title", value=b.get("title",""), key="edit_title")
                e_author = st.text_input("Author", value=b.get("author",""), key="edit_author")
                e_year = st.text_input("Year", value=str(b.get("year","")), key="edit_year")
                e_img_url = st.text_input("Image URL (optional)", value=b.get("image",""), key="edit_img_url")
                e_img_file = st.file_uploader("Upload new image (optional)", type=["jpg","jpeg","png"], key="edit_image_file")
                if st.button("Save changes", key="save_edit"):
                    success = edit_book(idx, e_title.strip(), e_author.strip(), e_year.strip(), e_img_url.strip() if e_img_url else None, e_img_file)
                    if success:
                        st.success("Book updated")
                        st.rerun()
                    else:
                        st.error("Failed to update book")

        # Tab 3: Delete
        with tab[3]:
            st.subheader("🗑️ Delete a book")
            books = load_books()
            if not books:
                st.info("No books to delete.")
            else:
                options = [f"{i+1}. {b.get('title','')}" for i,b in enumerate(books)]
                sel = st.selectbox("Select book to delete", options, key="del_select")
                idx = int(sel.split(".")[0]) - 1
                if st.button("Delete book", key="delete_book_btn"):
                    ok = delete_book(idx)
                    if ok:
                        st.warning("Book deleted")
                        st.rerun()
                    else:
                        st.error("Failed to delete")

        # Tab 4: Borrowing management (optional quick view)
        with tab[4]:
            st.subheader("Borrowing (viewer) - Users data from users.json")
            users_data = load_users()
            for u in users_data.get("users", []):
                st.write(f"- {u.get('username')} ({u.get('role')}) borrowed: {u.get('borrowed_books', [])}")

    # Reader area
    elif st.session_state.role == "reader":
        st.header("📚 Reader Dashboard")
        st.subheader("Available books")
        books = load_books()
        if not books:
            st.info("No books available yet.")
        else:
            q = st.text_input("Search (title or author)", key="reader_search")
            if q:
                filtered = [b for b in books if q.lower() in b.get("title","").lower() or q.lower() in b.get("author","").lower()]
            else:
                filtered = books
            for b in filtered:
                cols = st.columns([1,4])
                with cols[0]:
                    if b.get("image"):
                        try:
                            st.image(b["image"], width=110)
                        except Exception:
                            st.text("[image load error]")
                with cols[1]:
                    st.markdown(f"**{b.get('title','')}** ({b.get('year','')})")
                    st.write(f"Author: {b.get('author','')}")
                    st.divider()
