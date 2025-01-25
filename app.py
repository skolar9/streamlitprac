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
                f"  'x_col': 'name_of_column_for_x' (if applicable),\n"
                f"  'y_col': 'name_of_column_for_y' (if applicable),\n"
                f"  'group_by': 'name_of_column_for_grouping' (optional),\n"
                f"  'additional_notes': 'optional_notes_for_the_user'\n"
                f"}}\n"
                f"The chart_type can be one of the following: 'bar', 'pie', 'line', 'scatter', 'histogram', 'box', 'heatmap', or 'stacked_bar'.\n"
                f"If the query is invalid or cannot be answered with a chart, respond with: \n"
                f"{{'error': 'string'}}\n"
                f"to display an error message."
            )

            # Azure OpenAI API Request
            headers = {
                "Content-Type": "application/json",
                "api-key": API_KEY
            }

            data = {
                "messages": [
                    {"role": "system", "content": "You are an inventory analyst."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            }

            response = requests.post(
                f"{AZURE_ENDPOINT}/openai/deployments/gpt-4o/chat/completions?api-version={OPENAI_API_VERSION}",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                llm_response = response.json()['choices'][0]['message']['content']
                st.write(llm_response)

                # Parse LLM response for chart details
                try:
                    # Clean the response to ensure valid JSON
                    llm_response = llm_response.strip()
                    if llm_response.startswith("```") and llm_response.endswith("```"):
                        llm_response = llm_response[3:-3]
                    llm_response = llm_response.replace("'", '"')  # Replace single quotes with double quotes

                    chart_details = json.loads(llm_response)
                    chart_type = chart_details.get("chart_type")
                    x_col = chart_details.get("x_col").replace(" ", "_")
                    y_col = chart_details.get("y_col").replace(" ", "_")
                    group_by = chart_details.get("group_by", None).replace(" ", "_") if chart_details.get("group_by") else None

                    # Rename columns to remove spaces
                    inventory_data.columns = inventory_data.columns.str.replace(' ', '_')

                    # Function to generate charts
                    def generate_chart(chart_type, x_col, y_col=None, group_by=None):
                        fig, ax = plt.subplots(figsize=(10, 6))
                        try:
                            if chart_type == "bar":
                                 if y_col is None:
                                    raise ValueError("y_col must be provided for bar chart")
                                 else:
                                    data_to_plot = inventory_data.groupby(x_col)[y_col].count().reset_index()
                                    ax.bar(data_to_plot[x_col], data_to_plot[y_col])
                                    ax.set_xlabel(x_col.replace('_', ' '))
                                    ax.set_ylabel('Count of ' + y_col.replace('_', ' '))
                                    ax.set_title('Number of items in each ' + x_col.replace('_', ' '))

                            elif chart_type == "pie":
                                if group_by is None:
                                    # Count the occurrences of each x_col
                                    chart_data = inventory_data[x_col].value_counts().reset_index()
                                    chart_data.columns = [x_col, y_col]
                                else:
                                    # Group by the specified column and count occurrences
                                    chart_data = inventory_data.groupby([x_col, group_by]).size().reset_index(name=y_col)
                                    chart_data.columns = [x_col, group_by, y_col]

                                ax.pie(chart_data[y_col], labels=chart_data[x_col], autopct='%1.1f%%')
                                ax.set_title(f'Pie Chart of {y_col} by {x_col}')

                            elif chart_type == "line":
                                if group_by is None:
                                    # Group by x_col and count occurrences
                                    chart_data = inventory_data.groupby(x_col).size().reset_index(name=y_col)
                                else:
                                    # Group by x_col and group_by, then count occurrences
                                    chart_data = inventory_data.groupby([x_col, group_by]).size().reset_index(name=y_col)

                                sns.lineplot(data=chart_data, x=x_col, y=y_col, ax=ax, marker='o')
                                ax.set_title(f'Line Chart of {y_col} over {x_col}')
                                ax.set_xlabel(x_col)
                                ax.set_ylabel(y_col)
                            elif chart_type == "histogram":
                                if group_by is None:
                                    sns.histplot(data=inventory_data, x=x_col, ax=ax)
                                else:
                                    sns.histplot(data=inventory_data, x=x_col, hue=group_by, multiple="stack", ax=ax)
                                ax.set_title(f'Histogram of {x_col}')
                                ax.set_xlabel(x_col)
                                ax.set_ylabel('Frequency')
                            return fig

                        except Exception as e:
                            st.error(f"Error generating chart: {e}")

                    with col1:
                        # Generate and display the chart
                        fig = generate_chart(chart_type, x_col, y_col, group_by)
                        if fig:
                            st.pyplot(fig)

                except json.JSONDecodeError as e:
                    st.error(f"Error parsing LLM response: {e}")
                    st.write("Raw Responses")
                    st.code(llm_response, language='json')
                except Exception as e:
                    st.error(f"Error generating chart: {e}")
            else:
                st.error(f"Error: Received status code {response.status_code}")
                st.write(f"Response content: {response.content}")
