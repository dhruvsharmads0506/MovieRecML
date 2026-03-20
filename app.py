import streamlit as st
import pandas as pd
import pickle
import requests
import os
import numpy as np
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

import gdown

file_id = "1F9uBAD94f2_uZ4104F3rqAC95d850Qvr"
output = "similarity.pkl"

if not os.path.exists(output):
    url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url, output, quiet=False)
# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

# -----------------------------
# Cached function to fetch movie poster
# -----------------------------
@st.cache_data(ttl=86400)
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        else:
            return "https://via.placeholder.com/500x750?text=No+Poster"

    except requests.exceptions.RequestException:
        return "https://via.placeholder.com/500x750?text=No+Poster"

# -----------------------------
# Function to fetch multiple posters in parallel
# -----------------------------
def fetch_multiple_posters(movie_ids):
    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(fetch_poster, movie_ids))

# -----------------------------
# Movie recommender function
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
# Load movies data
# -----------------------------
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title('🎬 Movie Recommender System')

selected_movie_name = st.selectbox(
    'Which movie do you want to get recommendations for?',
    movies['title'].values
)

# Recommend button
if st.button('Recommend'):
    with st.spinner("Finding best movies for you... 🎬"):
        names, posters = recommender(selected_movie_name)

        if len(names) > 0:
            cols = st.columns(5)

            for col, name, poster in zip(cols, names, posters):
                with col:
                    st.image(poster, use_container_width=True)
                    st.caption(name)
        else:
            st.warning("No recommendations found for this movie.")