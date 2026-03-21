import streamlit as st
import pandas as pd
import pickle
import requests
import os
import numpy as np
import gdown
from concurrent.futures import ThreadPoolExecutor

# -----------------------------
# Download files from Google Drive
# -----------------------------
def download_file(file_id, output):
    if not os.path.exists(output):
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output, quiet=False)

# similarity file
download_file("1F9uBAD94f2_uZ4104F3rqAC95d850Qvr", "similarity.pkl")

# movies_dict file
download_file("1bQ0dWzvt-DJ-ZYD9l1ao9pVzwO52xwKL", "movies_dict.pkl")


# -----------------------------
# API KEY
# -----------------------------
try:
    API_KEY = st.secrets["TMDB_API_KEY"]
except:
    st.error("⚠️ TMDB API key missing! Add it in Streamlit Secrets.")
    st.stop()


# -----------------------------
# Load data (cached)
# -----------------------------
@st.cache_data
def load_data():
    movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity

movies, similarity = load_data()


# -----------------------------
# Fetch movie poster
# -----------------------------
@st.cache_data(ttl=86400)
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        response = requests.get(url, timeout=10)
        data = response.json()

        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w200/" + poster_path  # 🔥 smaller = faster
    except:
        pass

    return "https://via.placeholder.com/500x750?text=No+Poster"


# -----------------------------
# Fetch posters in parallel
# -----------------------------
def fetch_multiple_posters(movie_ids):
    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(fetch_poster, movie_ids))


# -----------------------------
# Recommender
# -----------------------------
def recommender(movie_name):
    try:
        movie_index = movies[movies['title'].str.lower() == movie_name.lower()].index[0]
        distances = similarity[movie_index]

        movie_indices = np.argsort(distances)[::-1][1:6]

        movie_ids = movies.iloc[movie_indices].movie_id.values
        recommend_movies = movies.iloc[movie_indices].title.values

        posters = fetch_multiple_posters(movie_ids)

        return recommend_movies, posters

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return [], []


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Movie Recommender", layout="wide")

# 🎨 Simple Styling
st.markdown("""
<style>
.movie-title {
    text-align: center;
    font-size: 14px;
    font-weight: bold;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

st.title('🎬 Movie Recommender System')

# Loader while loading movies
with st.spinner("Loading movies... 🎬"):
    if movies.empty:
        st.error("Movies data not loaded properly.")
        st.stop()

# Movie selection
selected_movie_name = st.selectbox(
    '🔍 Search or select a movie',
    movies['title'].values,
    key="movie_select"
)

# -----------------------------
# Recommend Button
# -----------------------------
if st.button('🚀 Recommend'):

    # Loader while recommending
    with st.spinner(f"Finding movies like '{selected_movie_name}' 🍿..."):
        names, posters = recommender(selected_movie_name)

    if len(names) > 0:
        cols = st.columns(5)

        for col, name, poster in zip(cols, names, posters):
            with col:
                if poster:
                    st.image(poster, width=180)
                else:
                    st.image("https://via.placeholder.com/500x750?text=No+Image", width=180)

                st.markdown(f"<div class='movie-title'>{name}</div>", unsafe_allow_html=True)
    else:
        st.warning("No recommendations found.")
