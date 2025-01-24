import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
from dotenv import load_dotenv
import json
import seaborn as sns  # Added for heatmap support

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
ENDPOINT = os.getenv("OPENAI_API_BASE")
API_VERSION = os.getenv("OPENAI_API_VERSION")

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

    # Display data preview
    st.subheader("Inventory Data Preview")
    st.dataframe(inventory_data.head())

    # Layout: Left (Dashboard), Right (Chat)
    col1, col2 = st.columns([2, 1])

    # Chat Interface (Right Side)
    with col2:
        st.header("Ask Inventory Questions")
        user_query = st.text_input("Enter your query:")
        if st.button("Submit"):
            # Prepare the prompt
            columns = ", ".join(inventory_data.columns)
            sample_data = inventory_data.head(5).to_string(index=False)  # Get the first 5 rows as a sample

            prompt = (
                f"You are an inventory analyst. Given the following dataset, answer the query below:\n\n"
                f"Dataset Columns:\n"
                f"{columns}\n\n"
                f"Sample Data (first 5 rows):\n"
                f"{sample_data}\n\n"
                f"Query: {user_query}\n\n"
                f"Return the response in the following format:\n"
                f"{{\n"
                f"  'chart_type': 'type_of_chart',\n"
                f"  'x_col': 'name_of_column_for_x',\n"
                f"  'y_col': 'name_of_column_for_y',\n"
                f"  'group_by': 'name_of_column_for_grouping' (optional),\n"
                f"  'additional_notes': 'optional_notes_for_the_user'\n"
                f"}}\n"
                f"The chart_type can be one of the following: 'bar', 'pie', 'line', 'scatter', 'histogram', 'box', 'heatmap', or 'stacked_bar'."
            )

            # Azure OpenAI API Request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }

            data = {
                "messages": [
                    {"role": "system", "content": "You are an inventory analyst."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            }

            response = requests.post(
                f"{ENDPOINT}/openai/deployments/gpt-4o/chat/completions?api-version={API_VERSION}",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                llm_response = response.json()['choices'][0]['message']['content']
                st.subheader("LLM Response")
                st.write(llm_response)

                # Parse LLM response for chart details
                try:
                    chart_details = json.loads(llm_response)  # Safely parse JSON string
                    chart_type = chart_details.get("chart_type")
                    x_col = chart_details.get("x_col")
                    y_col = chart_details.get("y_col")
                    group_by = chart_details.get("group_by")

                    # Function to generate the chart based on the response
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

                    # Generate the requested chart
                    generate_chart(chart_type, x_col, y_col, group_by)

                except json.JSONDecodeError:
                    st.error("Failed to parse LLM response. Ensure the query is clear.")
                except Exception as e:
                    st.error(f"Error generating chart: {e}")

            else:
                st.error(f"Error from Azure OpenAI API: {response.status_code} - {response.text}")
