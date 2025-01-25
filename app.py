import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
from dotenv import load_dotenv
import json
import seaborn as sns

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

# Streamlit Layout
st.set_page_config(layout="wide")
st.title("Enhanced Inventory Data Analyzer")

# CSV Upload Section
st.sidebar.header("Upload Inventory Data")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    inventory_data = pd.read_csv(uploaded_file)
    inventory_data.columns = inventory_data.columns.str.replace(' ', '_')  # Normalize column names
    st.sidebar.write("### Columns in the CSV:")
    st.sidebar.write(inventory_data.columns.tolist())

    # Display data preview
    st.subheader("Inventory Data Preview")
    st.dataframe(inventory_data.head())

    # Layout: Left (Dashboard), Right (Chat)
    col1, col2 = st.columns([2, 2])

    # Chat Interface (Right Side)
    with col2:
        st.header("Ask Inventory Questions")
        user_query = st.text_input("Enter your query:")
        if st.button("Submit"):
            # Prepare the prompt
            columns = ", ".join(inventory_data.columns)
            sample_data = inventory_data.head(5).to_string(index=False)

            prompt = (
                f"You are an inventory analyst. Given the following dataset, answer the query below:\n\n"
                f"Dataset Columns:\n{columns}\n\n"
                f"Sample Data (first 5 rows):\n{sample_data}\n\n"
                f"Query: {user_query}\n\n"
                f"Return the response in this format:\n"
                f"{{'chart_type': 'type_of_chart', 'x_col': 'x_column', 'y_col': 'y_column', 'group_by': 'group_by_column'}}"
            )

            # Azure OpenAI API Request
            headers = {"Content-Type": "application/json", "api-key": API_KEY}
            data = {
                "messages": [
                    {"role": "system", "content": "You are an inventory analyst."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            }

            response = requests.post(
                f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={OPENAI_API_VERSION}",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                try:
                    # Parse and clean the response
                    llm_response = response.json()['choices'][0]['message']['content']
                    llm_response = llm_response.strip().replace("'", '"')
                    chart_details = json.loads(llm_response)

                    # Extract chart parameters
                    chart_type = chart_details.get("chart_type")
                    x_col = chart_details.get("x_col")
                    y_col = chart_details.get("y_col", None)
                    group_by = chart_details.get("group_by", None)

                    # Validate columns
                    missing_cols = [col for col in [x_col, y_col, group_by] if col and col not in inventory_data.columns]
                    if missing_cols:
                        st.error(f"Invalid column(s): {', '.join(missing_cols)}")
                    else:
                        # Generate the chart
                        def generate_chart(chart_type, x_col, y_col=None, group_by=None):
                            fig, ax = plt.subplots(figsize=(10, 6))
                            if chart_type == "bar":
                                chart_data = inventory_data.groupby([x_col])[y_col].sum().reset_index()
                                sns.barplot(data=chart_data, x=x_col, y=y_col, ax=ax)
                            elif chart_type == "pie":
                                chart_data = inventory_data[x_col].value_counts().reset_index()
                                ax.pie(chart_data[x_col], labels=chart_data['index'], autopct='%1.1f%%')
                            elif chart_type == "line":
                                chart_data = inventory_data.groupby([x_col])[y_col].sum().reset_index()
                                sns.lineplot(data=chart_data, x=x_col, y=y_col, ax=ax, marker='o')
                            elif chart_type == "histogram":
                                sns.histplot(data=inventory_data, x=x_col, ax=ax, hue=group_by)
                            else:
                                raise ValueError(f"Unsupported chart type: {chart_type}")
                            ax.set_title(f"{chart_type.capitalize()} Chart")
                            st.pyplot(fig)

                        generate_chart(chart_type, x_col, y_col, group_by)

                except json.JSONDecodeError:
                    st.error("Error: Unable to parse the response from the AI.")
                except Exception as e:
                    st.error(f"Error generating chart: {e}")
            else:
                st.error(f"Error: Received status code {response.status_code}")
                st.write(f"Response content: {response.content}")
