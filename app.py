import streamlit as st
import pandas as pd
import pickle
import requests
from concurrent.futures import ThreadPoolExecutor

# -----------------------------
# Cached function to fetch movie poster
# -----------------------------
@st.cache_data
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=f9beac9a00e7078e15c531c740ead1f9&language=en-US"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        else:
            return "https://via.placeholder.com/500x750?text=No+Poster"
    except requests.exceptions.RequestException as e:
        print("Error fetching poster:", e)
        return "https://via.placeholder.com/500x750?text=No+Poster"

# -----------------------------
# Function to fetch multiple posters in parallel
# -----------------------------
def fetch_multiple_posters(movie_ids):
    with ThreadPoolExecutor() as executor:
        return list(executor.map(fetch_poster, movie_ids))

# -----------------------------
# Movie recommender function
# -----------------------------
def recommender(movie_name):
    try:
        movie_index = movies[movies['title'] == movie_name].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        movie_ids = [movies.iloc[i[0]].movie_id for i in movies_list]
        recommend_movies = [movies.iloc[i[0]].title for i in movies_list]
        recommended_movies_poster = fetch_multiple_posters(movie_ids)

        return recommend_movies, recommended_movies_poster
    except IndexError:
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

# CSS for hover effect
st.markdown(
    """
    <style>
    .movie-card {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-radius: 12px;
    }
    .movie-card:hover {
        transform: scale(1.05);
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.3);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Recommend button
if st.button('Recommend'):
    names, posters = recommender(selected_movie_name)
    if names:
        cols = st.columns(5, gap="medium")
        for col, name, poster in zip(cols, names, posters):
            with col:
                st.markdown(
                    f"<div style='text-align:center; font-weight:bold; white-space: nowrap; overflow-x: auto;'>{name}</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<img src='{poster}' class='movie-card' style='width:100%; border-radius:12px;'>",
                    unsafe_allow_html=True
                )
    else:
        st.warning("No recommendations found for this movie.")
