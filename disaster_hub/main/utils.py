import json
import streamlit as st
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime, timedelta
from google.genai.types import EmbedContentConfig
from google import genai
from google.genai import types
from google.cloud import aiplatform
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT")
DEPLOYED_INDEX_ID = os.getenv("DEPLOYED_INDEX_ID")

embeddings_json_file = 'disaster_title_desc_vectors.json'
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def load_embeddings():
    return pd.read_json(embeddings_json_file,lines=True)

def rewrite_query_with_gemini(user_query):
    """
    Uses Gemini to rewrite user query for better semantic retrieval.
    Expands regions, adds context, and clarifies disaster-related terms.
    """
    system_prompt = (
        "You are a disaster data retrieval assistant. "
        "Given a user query, rewrite it to make it more effective for semantic search over a disaster database. "
        "Expand region names into countries if necessary. "
        "Preserve the disaster type & location explicitly. "
        "Handle time-sensitive expressions like 'recent' or 'this month' -> limit to 30 days; if specific date/month/year "
        "is mentioned, retain it as is."
        "Make the rewritten text concise, natural, and contextually complete. "
        "Do NOT invent data or add numeric details. "
        "Output only the rewritten query text."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_query,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=2048
        )
    )
    #print(response)
    rewritten_query = response.candidates[0].content.parts[0].text.strip()
    return rewritten_query

def retrieve_similar_disasters_with_gemini(
    df,
    user_query: str,
    top_k: int = 5,
    embedding_model: str = "text-embedding-005",
):
    """
    Retrieve top-K similar disasters using Gemini-assisted query expansion + cosine similarity.
    """

    # --- Step 1: Rewrite query using Gemini ---
    rewritten_query = rewrite_query_with_gemini(user_query)
    print(f"Gemini Rewritten Query:\n{rewritten_query}\n")

    # --- Step 2: Generate embedding for rewritten query ---
    response = client.models.embed_content(
        model=embedding_model,
        contents=rewritten_query,
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    query_embedding = response.embeddings[0].values

    # --- Step 3: Compute cosine similarity ---
    matrix = np.vstack(df["embedding"].values)
    sim_scores = cosine_similarity([query_embedding], matrix)[0]
    df["similarity_score"] = sim_scores

    # --- Step 4: Sort and return top K ---
    df = df.sort_values("similarity_score", ascending=False).head(top_k).reset_index(drop=True)
    return df[["id", "embedding_metadata", "similarity_score"]]

def refined_retrieved_data(results_df):
    refine_retrieved_df = pd.concat([results_df.drop(['embedding_metadata'], axis=1),results_df['embedding_metadata'].apply(pd.Series)], axis=1)
    refine_retrieved_df["date"] = pd.to_datetime(refine_retrieved_df["date"])
    return refine_retrieved_df

def retrieve_similar_disasters_vertex_with_gemini(
    embeds_df,
    user_query: str,
    top_k: int=5,
    embedding_model: str = "text-embedding-005",
):
    """
    Retrieve top-K similar results using Vertex AI Vector Search with Gemini-based query expansion.
    """
    # ------------------------------
    # Step 1: Generate embedding using Gemini text-embedding model
    # ------------------------------

    rewritten_query = rewrite_query_with_gemini(user_query)
    print(f"Gemini Rewritten Query:\n{rewritten_query}\n")

    response = client.models.embed_content(
        model=embedding_model,
        contents=rewritten_query,
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )

    query_embedding = response.embeddings[0].values

    # ------------------------------
    # Step 2: Call Vector Search endpoint
    # ------------------------------
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(INDEX_ENDPOINT_ID)

    response = index_endpoint.find_neighbors(
        deployed_index_id=DEPLOYED_INDEX_ID,
        queries=[query_embedding],
        num_neighbors=top_k,
        return_full_datapoint=True
    )

    # ------------------------------
    # Step 3: Parse and format results
    # ------------------------------
    results = []
    for n in response[0]:  
        row = embeds_df[embeds_df["id"] == int(n.id)]
        results.append({
            "id":int(n.id),
            "embedding_metadata":row.embedding_metadata.iloc[0],
            "similarity_score": n.distance,
        })
    results = pd.DataFrame(results)
    results = results.sort_values("similarity_score", ascending=False).head(top_k).reset_index(drop=True)
    return results

def summarize_with_gemini(doc_desc):
    """
    Uses Gemini to rewrite user query for better semantic retrieval.
    Expands regions, adds context, and clarifies disaster-related terms.
    """
    system_prompt = (
    """
    You are an expert disaster data analyst.
    Summarize the following disaster report in **under 100 words**, focusing only on key facts:
    - What happened
    - Where and when it occurred
    - Main impacts (e.g., casualties, affected areas, damages)
    - Current status if mentioned

    Keep the tone factual and analytical. 
    Do not include speculation, redundant wording, or opinions.
    Output only the concise summary text, without any markdown or extra formatting.
    """
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=doc_desc,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=2048
        )
    )
    #print(response)
    summary = response.candidates[0].content.parts[0].text.strip()
    return summary