import streamlit as st
import utils as ut
import plotly.express as px

@st.cache_data
def get_embeddings():
    return ut.load_embeddings()


@st.cache_data
def get_retrieved_data(df, user_query, vertex=False):
    if not vertex: #manual retrieval
        retrieve_orig = ut.retrieve_similar_disasters_with_gemini(df,user_query)
    else: #retrieve from vertex vector search
        retrieve_orig = ut.retrieve_similar_disasters_vertex_with_gemini(df,user_query)
        
    retrieve_refined = ut.refined_retrieved_data(retrieve_orig)
        
    return retrieve_refined

embeds_df = get_embeddings()

st.set_page_config(page_title="Disaster Analytics Dashboard", layout="wide")
st.title("🌍 Disaster Insights Dashboard")
st.markdown("Explore retrieved disaster data interactively.")
query = st.text_input("Enter your query:", "Recent floods in Asia")

df = get_retrieved_data(embeds_df, query, True)

# Sidebar Filters
disaster_types = ["All"] + sorted(df["type"].unique().tolist())
statuses = ["All"] + sorted(df["status"].unique().tolist())
countries = ["All"] + sorted(df["country"].unique().tolist())

selected_disaster = st.sidebar.selectbox("Select Disaster Type", disaster_types)
selected_status = st.sidebar.selectbox("Select Status", statuses)
selected_country = st.sidebar.selectbox("Select Country", countries)

# Apply filters dynamically
filtered_df = df.copy()
if selected_disaster != "All":
    filtered_df = filtered_df[filtered_df["type"] == selected_disaster]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df["status"] == selected_status]
if selected_country != "All":
    filtered_df = filtered_df[filtered_df["country"] == selected_country]

st.markdown(f"### Showing {len(filtered_df)} records after filters")

# ------------------------------
# 3️⃣ Heatmap: Country vs Status
# ------------------------------
st.subheader("🗺️ Disaster Status Heatmap")
heatmap_data = filtered_df.groupby(["country", "status"]).size().reset_index(name="count")

status_colors = {
    "ongoing": "red",
    "alert": "yellow",
    "past": "skyblue"
}

if not heatmap_data.empty:
    # Add color column manually
    heatmap_data["color"] = heatmap_data["status"].map(status_colors)
    print(heatmap_data)

    # Create a choropleth (world map)
    fig = px.choropleth(
        heatmap_data,
        locations="country",                # Country names
        locationmode="country names",       # Use country names instead of ISO codes
        color="status",                     # Color by status category
        hover_name="country",
        hover_data=["count"],
        color_discrete_map=status_colors,   # Use your fixed colors
        title="🌍 Disaster Status by Country",
    )

    fig.update_geos(projection_type="natural earth",fitbounds="locations")
    fig.update_layout(height=600, margin={"r":0,"t":40,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data available for heatmap.")
    
# ------------------------------
# 4️⃣ Disaster Counts by Type and Status
# ------------------------------
st.subheader("📊 Disaster Counts by Type and Status")
bar_data = df.groupby(["type", "status"]).size().reset_index(name="count")
bar_fig = px.bar(bar_data, x="type", y="count", color="status",
                 title="Disaster Count by Type and Status", barmode="group")
st.plotly_chart(bar_fig, use_container_width=True)

# Pie chart — #countries affected by disaster
st.subheader("🌐 Countries by Disaster Type")
country_disaster = df.groupby("type")["country"].nunique().reset_index(name="countries_affected")
pie_fig = px.pie(country_disaster, names="type", values="countries_affected",
                 title="Number of Countries per Disaster Type", hole=0.4)
st.plotly_chart(pie_fig, use_container_width=True)

# ------------------------------
# 5️⃣ Time Series: Disaster Frequency
# ------------------------------
st.subheader("📈 Disaster Frequency Over Time")
time_data = df.groupby([df["date"].dt.to_period("M"), "status"]).size().reset_index(name="count")
time_data["date"] = time_data["date"].astype(str)
time_fig = px.line(time_data, x="date", y="count", color="status",
                   markers=True, title="Disaster Frequency Over Time")
st.plotly_chart(time_fig, use_container_width=True)

# ------------------------------
# 6️⃣ Interactive Document Titles
# ------------------------------
st.subheader("📰 Retrieved Documents")
for _, row in filtered_df.iterrows():
    if st.button(row["title"]):
        st.session_state["selected_title"] = row["title"]
        st.session_state["selected_id"] = row["id"]
        st.session_state["selected_country"] = row["country"]
        st.session_state["selected_type"] = row["type"]
        st.success(f"Selected document: {row['title']}")
        #st.stop()

if "selected_title" in st.session_state:
    selected_id = st.session_state["selected_id"]
    selected_title = st.session_state["selected_title"]
    st.info(f"Selected document: {selected_title}")
    
    selected_doc = df.loc[df["id"] == selected_id]

    if not selected_doc.empty:
        description_text = selected_doc.iloc[0]["description"]

        with st.spinner("Generating summary with Gemini..."):
            try:
                summary = ut.summarize_with_gemini(description_text)
                st.subheader("🧾 Gemini Summary")
                st.write(summary)
            except Exception as e:
                st.error(f"Gemini summarization failed: {e}")
    else:
        st.warning("No description found for the selected document.")
        

        st.subheader("📰 Retrieved Documents")

