import streamlit as st
import pandas as pd
import os
import json

# File to store book data
BOOKS_FILE = 'books.json'

# Initialize or load data
if not os.path.exists(BOOKS_FILE):
    with open(BOOKS_FILE, 'w') as f:
        json.dump([], f)

def load_books():
    with open(BOOKS_FILE, 'r') as f:
        return json.load(f)

def save_books(data):
    with open(BOOKS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def add_book(title, author, year):
    books = load_books()
    books.append({'Title': title, 'Author': author, 'Year': year})
    save_books(books)

def delete_book(index):
    books = load_books()
    if 0 <= index < len(books):
        books.pop(index)
        save_books(books)

def search_books(keyword):
    books = load_books()
    return [book for book in books if keyword.lower() in book['Title'].lower()]

# Streamlit UI
st.set_page_config(page_title="📚 Library Management System", layout="centered")
st.title("📚 Library Management System")

menu = st.sidebar.selectbox("Menu", ["View Books", "Add Book", "Search", "Delete Book"])

if menu == "Add Book":
    st.subheader("Add New Book")
    title = st.text_input("Title")
    author = st.text_input("Author")
    year = st.text_input("Year")
    if st.button("Add"):
        if title and author and year:
            add_book(title, author, year)
            st.success("Book added successfully.")
        else:
            st.warning("Please fill all fields.")

elif menu == "View Books":
    st.subheader("Book List")
    books = load_books()
    st.dataframe(pd.DataFrame(books))

elif menu == "Search":
    st.subheader("Search Book")
    keyword = st.text_input("Enter keyword")
    if st.button("Search"):
        result = search_books(keyword)
        if result:
            st.write("Results:")
            st.dataframe(pd.DataFrame(result))
        else:
            st.warning("No books found.")

elif menu == "Delete Book":
    st.subheader("Delete Book")
    books = load_books()
    if books:
        df = pd.DataFrame(books)
        index = st.selectbox("Select book index to delete", df.index)
        st.write(df.iloc[index])
        if st.button("Delete"):
            delete_book(index)
            st.success("Book deleted.")
    else:
        st.warning("No books to delete.")


