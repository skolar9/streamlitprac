import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import json

# Set the page config
st.set_page_config(page_title='LLM-Driven Data Visualizer', layout='centered', page_icon='📊')

# Title
st.title('📊  LLM-Driven Data Visualizer')

# Specify the folder where your CSV files are located
working_dir = os.path.dirname(os.path.abspath(__file__))
folder_path = f"{working_dir}/data"  # Update this to your folder path

# List all files in the folder
files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

# Dropdown to select a file
selected_file = st.selectbox('Select a file', files, index=None)

if selected_file:
    # Construct the full path to the file
    file_path = os.path.join(folder_path, selected_file)

    # Read the selected CSV file
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.replace(' ', '_')  # Normalize column names

    st.write("### Preview of the Selected Dataset")
    st.write(df.head())

    # User query for the LLM
    st.write("### Ask your question")
    user_query = st.text_area("Describe what you want to visualize, e.g., 'Show a bar chart of sales by region'")

    if st.button("Generate Chart"):
        # Define LLM query prompt
        prompt = (
            f"You are a data visualization assistant. Based on the following dataset, "
            f"determine the most suitable chart type, X-axis, and Y-axis for the query.\n\n"
            f"Dataset Columns: {', '.join(df.columns)}\n\n"
            f"Sample Data (first 5 rows):\n{df.head().to_string(index=False)}\n\n"
            f"User Query: {user_query}\n\n"
            f"Provide the response in this JSON format:\n"
            f"{{'chart_type': 'chart_type', 'x_col': 'x_column', 'y_col': 'y_column'}}"
        )

        # Send the prompt to the LLM API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer YOUR_OPENAI_API_KEY"
        }
        data = {"prompt": prompt, "max_tokens": 100, "temperature": 0.7}

        response = requests.post(
            "https://api.openai.com/v1/completions",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            try:
                llm_response = response.json()["choices"][0]["text"]
                chart_details = json.loads(llm_response.strip().replace("'", '"'))

                # Extract chart parameters
                chart_type = chart_details.get("chart_type", None)
                x_col = chart_details.get("x_col", None)
                y_col = chart_details.get("y_col", None)

                # Validate columns
                missing_cols = [col for col in [x_col, y_col] if col and col not in df.columns]
                if missing_cols:
                    st.error(f"Invalid column(s): {', '.join(missing_cols)}")
                elif not chart_type:
                    st.error("No valid chart type provided by the LLM.")
                else:
                    # Generate and display the chart
                    fig, ax = plt.subplots(figsize=(6, 4))

                    try:
                        if chart_type == "Line Plot":
                            sns.lineplot(x=df[x_col], y=df[y_col], ax=ax)
                        elif chart_type == "Bar Chart":
                            sns.barplot(x=df[x_col], y=df[y_col], ax=ax)
                        elif chart_type == "Scatter Plot":
                            sns.scatterplot(x=df[x_col], y=df[y_col], ax=ax)
                        elif chart_type == "Distribution Plot":
                            sns.histplot(df[x_col], kde=True, ax=ax)
                        elif chart_type == "Count Plot":
                            sns.countplot(x=df[x_col], ax=ax)
                        else:
                            raise ValueError(f"Unsupported chart type: {chart_type}")

                        # Set labels and title
                        plt.title(f'{chart_type} of {y_col} vs {x_col}', fontsize=12)
                        plt.xlabel(x_col, fontsize=10)
                        plt.ylabel(y_col, fontsize=10)

                        st.pyplot(fig)
                    except Exception as e:
                        st.error(f"Error generating chart: {e}")

            except json.JSONDecodeError:
                st.error("Failed to parse LLM response.")
        else:
            st.error(f"Error: LLM API returned status code {response.status_code}")
