# -*- coding: utf-8 -*-
"""search_vibe.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1JgEGjLPD_BsBEZHfFZo9rX-uAjc0U7JI
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

# Load original dataset
df_raw = pd.read_pickle("tracks_with_embeddings.pkl")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Check if the mood-enhanced file already exists
if os.path.exists("tracks_with_mood_embeddings.pkl"):
    print(" Precomputed embeddings found. Loading...")
    df = pd.read_pickle("tracks_with_mood_embeddings.pkl")
else:
    print(" No precomputed file found. Generating mood embeddings...")

    def build_mood_description(row):
        mood = []
        if row["valence"] < 0.3:
            mood.append("sad")
        elif row["valence"] > 0.7:
            mood.append("happy")
        else:
            mood.append("emotional")

        if row["energy"] < 0.4:
            mood.append("calm")
        elif row["energy"] > 0.7:
            mood.append("energetic")

        if row["tempo"] < 90:
            mood.append("slow")
        elif row["tempo"] > 140:
            mood.append("fast")

        mood.append(row["genre"].lower())
        return " ".join(mood)

    # Generate mood descriptions and embeddings
    df = df_raw.copy()
    df["mood_description"] = df.apply(build_mood_description, axis=1)
    df["mood_embedding"] = df["mood_description"].apply(lambda x: model.encode(x, convert_to_numpy=True))

    # Save for future use
    df.to_pickle("tracks_with_mood_embeddings.pkl")
    print(" Saved to tracks_with_mood_embeddings.pkl")

# Build embedding matrix for similarity search
mood_matrix = np.vstack(df["mood_embedding"].values)

def get_style_boosts(style):
    style_prompts = {
        "soft": ["calm", "emotional", "acoustic"],
        "lofi": ["lofi", "study", "indie"],
        "energetic": ["energetic", "fast", "intense"],
        "dance": ["dance", "pop", "upbeat"],
        "sadboi": ["sad", "slow", "emotional"]
    }
    return style_prompts.get(style.lower(), [])  # default = empty list

def search_tracks(user_vibe, style="none", top_k=10):
    base_prompts = [user_vibe]
    if style != "none":
        base_prompts += get_style_boosts(style)

    prompt_vecs = [model.encode(p, convert_to_numpy=True) for p in base_prompts]
    vibe_vec = np.mean(prompt_vecs, axis=0)

    similarities = cosine_similarity([vibe_vec], mood_matrix)[0]
    df["similarity"] = similarities

    ranked = df.sort_values("similarity", ascending=False)
    ranked = ranked.drop_duplicates(subset=["artist_name"])

    return ranked.head(top_k).copy()

