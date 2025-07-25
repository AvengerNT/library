import streamlit as st
import pandas as pd
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BOOKS_FILE = 'books.json'

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

def get_recommendations(selected_title):
    books = load_books()
    df = pd.DataFrame(books)
    if df.empty or len(df) < 2:
        return []
    df['Text'] = df['Title'] + " " + df['Author']
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['Text'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    idx = df[df['Title'] == selected_title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:4]
    recommended_titles = [df.iloc[i[0]]['Title'] for i in sim_scores]
    return recommended_titles

st.set_page_config(page_title="📚 Smart Library System", layout="centered")
st.title("📚 AI Library Management System")

menu = st.sidebar.selectbox("Menu", ["View Books", "Add Book", "Search & Recommend"])

if menu == "Add Book":
    st.subheader("➕ Add New Book")
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
    st.subheader("📖 Book List")
    books = load_books()
    st.dataframe(pd.DataFrame(books))

elif menu == "Search & Recommend":
    st.subheader("🔍 Search & Get Recommendations")
    books = load_books()
    if books:
        titles = [book['Title'] for book in books]
        selected = st.selectbox("Choose a book", titles)
        st.write("📘 Selected Book:", selected)
        recs = get_recommendations(selected)
        if recs:
            st.success("📚 You may also like:")
            for r in recs:
                st.markdown(f"- {r}")
        else:
            st.warning("Not enough data for recommendation.")
    else:
        st.warning("No books found.")
