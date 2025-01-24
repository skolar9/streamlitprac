import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from io import StringIO

# Function to load and preview data
def load_data(uploaded_file):
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return None

# Function to create sample charts (you can expand this with more chart types)
def create_charts(df):
    # Example chart: Count of different statuses in the inventory
    st.subheader("Inventory Status Distribution")
    status_count = df['status'].value_counts()
    st.bar_chart(status_count)
    
    # Example chart: Distribution of Package Levels
    st.subheader("Package Level Distribution")
    package_count = df['package level'].value_counts()
    st.bar_chart(package_count)
    
    # Example chart: SKU vs Event Time scatter plot
    st.subheader("SKU vs Event Time")
    fig = px.scatter(df, x="event time", y="sku", title="SKU vs Event Time")
    st.plotly_chart(fig)

# Streamlit App layout
def app():
    st.title("CSV Dashboard Visualizer")
    
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Load and display the preview of the data
        df = load_data(uploaded_file)
        
        if df is not None:
            st.subheader("Data Preview")
            st.dataframe(df.head())  # Show the first 5 rows of the data

            # Display dashboards after the data preview
            st.subheader("Dashboards & Visualizations")
            create_charts(df)

# Run the app
if __name__ == "__main__":
    app()
