import streamlit as st
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
import pandas as pd
import matplotlib.pyplot as plt

# Initialize LangChain LLM
API_KEY = "your_api_key_here"
llm = OpenAI(api_key=API_KEY)

# Load CSV Data
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

data = load_data()

# Streamlit Layout
st.set_page_config(layout="wide")
st.title("Chat-Based Dashboard Visualizer")

# Layout: Left (Dashboard), Right (Chat)
col1, col2 = st.columns([2, 1])

# Chat Interface (Right Side)
with col2:
    st.header("Ask a Question")
    user_query = st.text_input("Enter your question:")
    if st.button("Submit"):
        # Use LangChain to process query
        prompt = PromptTemplate(
            input_variables=["query"],
            template="You are a data analyst. Analyze the CSV file and answer the following: {query}"
        )
        structured_query = prompt.format(query=user_query)
        response = llm.predict(structured_query)
        
        st.subheader("LLM Response")
        st.write(response)

# Dashboard (Left Side)
with col1:
    st.header("Dashboard")
    if user_query:
        # Example: Generate visualization based on LLM response
        st.write("Sample visualization based on user query")
        
        # Example: Show a bar chart
        if "sales" in user_query.lower():
            grouped_data = data.groupby("Region")["Sales"].sum().reset_index()
            fig, ax = plt.subplots()
            ax.bar(grouped_data["Region"], grouped_data["Sales"], color="skyblue")
            ax.set_title("Total Sales by Region")
            ax.set_xlabel("Region")
            ax.set_ylabel("Sales")
            st.pyplot(fig)
        else:
            st.write("No visualization available for this query.")
