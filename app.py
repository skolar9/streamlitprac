import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
from sklearn.linear_model import LinearRegression
import numpy as np

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
ENDPOINT = os.getenv("OPENAI_API_BASE")
API_VERSION = os.getenv("OPENAI_API_VERSION")

# Initialize LangChain with Azure OpenAI
llm = AzureChatOpenAI(
    deployment_name="gpt-4o",
    openai_api_base=ENDPOINT,
    openai_api_key=API_KEY,
    openai_api_version=API_VERSION,
    temperature=0.7
)

# Streamlit Layout
st.set_page_config(layout="wide")
st.title("Enhanced Inventory Data Analyzer")

# CSV Upload Section
st.sidebar.header("Upload Inventory Data")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    inventory_data = pd.read_csv(uploaded_file)
    st.sidebar.write("### Columns in the CSV:")
    st.sidebar.write(inventory_data.columns.tolist())

    @st.cache_data
    def load_data():
        return inventory_data

    inventory_data = load_data()

    # Layout: Left (Dashboard), Right (Chat)
    col1, col2 = st.columns([2, 1])  # Adjust the width ratios as needed

    # Left Column: Dashboard and Data Analysis
    with col1:
        st.header("Inventory Data Preview")
        st.dataframe(inventory_data.head())

        # **Deriving Insights**

        # 1. Status Distribution Analysis
        st.subheader("Inventory Status Distribution")
        if "status" in inventory_data.columns:
            status_counts = inventory_data['status'].value_counts()
            fig, ax = plt.subplots(figsize=(8, 5))
            status_counts.plot(kind='bar', ax=ax, color='lightcoral')
            ax.set_title("Inventory Status Distribution")
            ax.set_xlabel("Status")
            ax.set_ylabel("Count")
            st.pyplot(fig)
        else:
            st.error("Missing 'status' column for analysis.")

        # 2. Package Level Distribution
        st.subheader("Package Level Distribution")
        if "package level" in inventory_data.columns:
            package_level_counts = inventory_data['package level'].value_counts()
            fig, ax = plt.subplots(figsize=(8, 5))
            package_level_counts.plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title("Distribution of Package Levels")
            ax.set_xlabel("Package Level")
            ax.set_ylabel("Count")
            st.pyplot(fig)
        else:
            st.error("Missing 'package level' column for analysis.")

        # 3. Event Time Trend Analysis
        st.subheader("Event Time Trend")
        if "event time" in inventory_data.columns:
            inventory_data['event time'] = pd.to_datetime(inventory_data['event time'])
            event_time_trends = inventory_data.groupby(inventory_data['event time'].dt.to_period('M')).size()
            fig, ax = plt.subplots(figsize=(10, 6))
            event_time_trends.plot(kind='line', ax=ax, marker='o', color='green')
            ax.set_title("Event Time Trend")
            ax.set_xlabel("Date")
            ax.set_ylabel("Event Count")
            st.pyplot(fig)
        else:
            st.error("Missing 'event time' column for analysis.")

        # 4. Parent-Child SKU Relationship
        st.subheader("Parent-Child SKU Relationship")
        if "parentuuid" in inventory_data.columns and "uuid" in inventory_data.columns:
            parent_child_count = inventory_data.groupby('parentuuid')['uuid'].count().reset_index()
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(parent_child_count['parentuuid'], parent_child_count['uuid'], color='lightblue')
            ax.set_title("Parent-Child SKU Relationship")
            ax.set_xlabel("Parent UUID")
            ax.set_ylabel("Number of Children")
            st.pyplot(fig)
        else:
            st.error("Missing 'parentuuid' or 'uuid' columns for analysis.")

        # 5. Inventory Creation Trends
        st.subheader("Inventory Creation Trends")
        if "crested_date" in inventory_data.columns:
            inventory_data['crested_date'] = pd.to_datetime(inventory_data['crested_date'])
            inventory_creation_trends = inventory_data.groupby(inventory_data['crested_date'].dt.to_period('M')).size()
            fig, ax = plt.subplots(figsize=(10, 6))
            inventory_creation_trends.plot(kind='line', ax=ax, marker='o', color='blue')
            ax.set_title("Inventory Creation Trends")
            ax.set_xlabel("Month")
            ax.set_ylabel("Inventory Created")
            st.pyplot(fig)
        else:
            st.error("Missing 'crested_date' column for analysis.")

    # Right Column: Chat Interface for Queries
    with col2:
        st.header("Ask Inventory Questions")
        user_query = st.text_input("Enter your query:")
        if st.button("Submit"):
            # Use LangChain to process query
            prompt = PromptTemplate(
                input_variables=["query", "columns"],
                template=(
                    "You are an inventory analyst. Given the dataset with columns {columns}, "
                    "analyze the inventory and answer the following: {query}. Suggest charts if needed."
                )
            )
            structured_query = prompt.format(query=user_query, columns=", ".join(inventory_data.columns))
            response = llm.predict_messages([{"role": "user", "content": structured_query}])
            
            st.subheader("LLM Response")
            st.write(response.content)

            # Parse LLM response for chart details
            try:
                chart_details = eval(response.content)
                chart_type = chart_details.get("chart_type")
                x_col = chart_details.get("x_col")
                y_col = chart_details.get("y_col")
                group_by = chart_details.get("group_by")

                # Generate the requested chart
                def generate_chart(chart_type, x_col, y_col=None, group_by=None):
                    fig, ax = plt.subplots(figsize=(10, 6))
                    if chart_type == "bar":
                        grouped_data = inventory_data.groupby(group_by)[y_col].sum().reset_index()
                        ax.bar(grouped_data[group_by], grouped_data[y_col], color="skyblue")
                        ax.set_title(f"{y_col} by {group_by}")
                        ax.set_xlabel(group_by)
                        ax.set_ylabel(y_col)
                    elif chart_type == "pie":
                        grouped_data = inventory_data.groupby(group_by)[y_col].sum().reset_index()
                        ax.pie(grouped_data[y_col], labels=grouped_data[group_by], autopct='%1.1f%%', startangle=90)
                        ax.set_title(f"Distribution of {y_col} by {group_by}")
                    elif chart_type == "line":
                        grouped_data = inventory_data.groupby(x_col)[y_col].sum().reset_index()
                        ax.plot(grouped_data[x_col], grouped_data[y_col], marker='o')
                        ax.set_title(f"{y_col} over {x_col}")
                        ax.set_xlabel(x_col)
                        ax.set_ylabel(y_col)
                    elif chart_type == "scatter":
                        ax.scatter(inventory_data[x_col], inventory_data[y_col], color='blue')
                        ax.set_title(f"Scatter Plot of {y_col} vs {x_col}")
                        ax.set_xlabel(x_col)
                        ax.set_ylabel(y_col)
                    elif chart_type == "histogram":
                        ax.hist(inventory_data[y_col], bins=20, color='lightgreen')
                        ax.set_title(f"Histogram of {y_col}")
                        ax.set_xlabel(y_col)
                        ax.set_ylabel('Frequency')
                    elif chart_type == "box":
                        ax.boxplot(inventory_data[y_col])
                        ax.set_title(f"Box Plot of {y_col}")
                    elif chart_type == "heatmap":
                        correlation = inventory_data.corr()
                        sns.heatmap(correlation, annot=True, cmap="coolwarm", ax=ax)
                        ax.set_title("Correlation Heatmap")
                    elif chart_type == "stacked_bar":
                        stacked_data = inventory_data.groupby([group_by, x_col])[y_col].sum().unstack().fillna(0)
                        stacked_data.plot(kind='bar', stacked=True, ax=ax)
                        ax.set_title(f"Stacked Bar Chart of {y_col} by {group_by} and {x_col}")
                    else:
                        st.write("Chart type not supported yet.")
                    st.pyplot(fig)

                generate_chart(chart_type, x_col, y_col, group_by)

            except Exception as e:
                st.error(f"Error generating chart: {e}")
