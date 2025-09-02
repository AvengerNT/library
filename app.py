import streamlit as st
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------
# Load Book Data
# ---------------------------------------
@st.cache_data
def load_books():
    with open("book.json", "r") as f:
        books = json.load(f)
    return books

books = load_books()
df = pd.DataFrame(books)

# ---------------------------------------
# Title Vectorization for AI Recommendations
# ---------------------------------------
@st.cache_resource
def compute_similarity(df):
    titles = df["title"].tolist()
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(titles)
    similarity = cosine_similarity(tfidf_matrix)
    return similarity, titles

similarity_matrix, title_list = compute_similarity(df)

# ---------------------------------------
# Recommendation Function
# ---------------------------------------
def get_recommendations(input_title, top_n=5):
    if input_title not in title_list:
        return []
    idx = title_list.index(input_title)
    scores = list(enumerate(similarity_matrix[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[1:top_n+1]
    return [title_list[i] for i, _ in scores]

# ---------------------------------------
# Streamlit UI
# ---------------------------------------
st.set_page_config(page_title="Library Recommender", layout="wide")
st.title("📚 Book Recommendation System")

st.markdown("Search for a book title and get recommendations based on content similarity.")

search_input = st.text_input("🔍 Enter a Book Title")

if search_input:
    matches = [t for t in title_list if search_input.lower() in t.lower()]
    if matches:
        selected_book = st.selectbox("Select from matching titles:", matches)
        st.subheader("📖 Selected Book Details")
        book_info = df[df["title"] == selected_book].iloc[0]

        # Show book cover if available
        if "image" in book_info and book_info["image"]:
            st.image(book_info["image"], width=200)

        st.write(f"**Title:** {book_info['title']}")
        st.write(f"**Author:** {book_info['author']}")
        st.write(f"**Year:** {book_info['year']}")

        st.subheader("🤖 Recommended Books")
        recs = get_recommendations(selected_book)
        if recs:
            for i, rec in enumerate(recs, 1):
                rec_info = df[df["title"] == rec].iloc[0]
                cols = st.columns([1,3])
                with cols[0]:
                    if "image" in rec_info and rec_info["image"]:
                        st.image(rec_info["image"], width=100)
                with cols[1]:
                    st.write(f"**{rec_info['title']}**")
                    st.write(f"Author: {rec_info['author']}")
                    st.write(f"Year: {rec_info['year']}")
        else:
            st.info("No recommendations found.")
    else:
        st.warning("No matching books found.")
