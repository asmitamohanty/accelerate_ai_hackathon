# Disaster Insights Dashboard
An AI-powered disaster intelligence hub that leverages Fivetran Connector SDK, BigQuery, and Vertex AI's Vector Search & Gemini API to make global disaster data more accessible and actionable.
This project is originally inspired by the [Fivetran x Google Cloud Hackathon](https://ai-accelerate.devpost.com/). While not an official submission, it was developed independently to showcase how automated data pipelines and retrieval-augmented generation (RAG) with AI-assistant can transform raw disaster data into meaningful insights and visual analytics to support better decision-making.

Check [**DEMO**](https://www.dropbox.com/scl/fi/8oj5h19q6btuthdenpt9c/video3616112834.mp4?rlkey=wgqsbl8ajmqvvm3eqrvz0bup7&st=v7u2u0do&dl=0) for a quick glance at the App!

## Project Overview
This project connects open disaster data from ReliefWeb API using the **Fivetran Connector SDK**, stores it in **BigQuery**, and powers a **Vertex AI–enabled RAG** workflow to generate insights and summaries for climate and disaster management.

### Key Features

🌐 Automated data extraction using Fivetran Connector SDK

☁️ Data warehousing and transformation in Google BigQuery

🧠 Context-aware document retrieval via Vertex AI Vector Search assisted by Gemini API for Query refinement

💬 Insight generation and summarization using Gemini API

📊 Interactive dashboard built with Streamlit

## Quick Start
#### Data Ingestion & ETL using Fivetran Connector SDK
- Data source: [ReliefWeb API for Disasters](https://reliefweb.int/disasters)
- Follow [Fivetran Connector SDK guide](https://fivetran.com/docs/connector-sdk/setup-guide) to link your Fivetran dashboard with Bigquery 
- Setup your fivetran credentials, debug & then deploy!
```
cd disaster_hub/fivetran
source fivetran_env.sh
fivetran deploy
fivetran deploy
```
- Go to your dashboard once deployment is successful. Check your schema to ensure your table is updated & click on `Sync` to push your table to BigQuery

#### RAG Work Flow
```
cd disaster_hub/main
```
- Refer `disasterhub.ipynb` for more details & visualization
- Setup your GCP credentials required for Bigquery, Google Cloud Storage Bucket & Vertex Vector Search 
- `Generate embeddings`: `title` & `description` are selected to create embeddings. Vector embeddings json file is pushed to Vertex Vector Search
- Use **Gemini Assistant** for the following:
  - `Query Refinement`: To refine the user query that enhances the retrieval. This is done so because typical RAG retrieval is based only on cosine similarity & it doesn't account for semantic meaning. Gemini API will help in expanding the user query based on our system prompt to add more details that can help in retrieval of relevant document
  - `Generating Insight Summary`: To generate concise insights summarizing the necessary impacts from the original description in the retrieved document
- _Note_: Actual Deployment uses Vector Search for document retrieval, however, supporting code is added for manual retrieval using cosine similarity for debug purposes

#### Launch DISH
- Important files:
  - `utils.py`: Important helper functions for RAG workflow that will be used in streamlit
  - `app.py`: streamlit app that creates the dashboard
- Launch the app from `disasterhub.ipynb` notebook terminal




