import streamlit as st
import pandas as pd
import plotly.express as px
import tabula
from pymongo import MongoClient
import base64

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "SmartFinanceDB"
ACTIVITY_COLLECTION = "user_activities"

# Page Configuration
st.set_page_config(page_title="Smart Finance Dashboard", layout="wide")

# MongoDB Connection
def get_mongo_connection():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

db = get_mongo_connection()

# Function to log user activity
def log_user_activity(activity):
    db[ACTIVITY_COLLECTION].insert_one(activity)

# Function to process PDF to DataFrame
def process_pdf(file):
    try:
        df_list = tabula.read_pdf(file, pages="all", multiple_tables=True, stream=True)
        if df_list:
            return pd.concat(df_list, ignore_index=True)
        else:
            st.error("No tables found in the PDF.")
            return None
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# Function to load data from CSV or PDF
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".pdf"):
        return process_pdf(file)
    else:
        st.error("Unsupported file format. Please upload a CSV or PDF file.")
        return None

# Function to add centered background image
def add_bg_from_local(image_file):
    with open(image_file, "rb") as img:
        encoded_string = base64.b64encode(img.read()).decode()  # Convert to base64 string
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Function to create recommendations
def generate_recommendations(data, priority):
    recommendations = []
    if priority == "Savings":
        recommendations.append("Allocate 20% of your income to savings.")
        recommendations.append("Track your fixed expenses to maximize savings.")
    elif priority == "Investments":
        recommendations.append("Explore SIPs and mutual funds for growth.")
        recommendations.append("Consider diversifying into low-risk bonds.")
    elif priority == "Expenses":
        recommendations.append("Identify areas where overspending occurs.")
        recommendations.append("Set a monthly budget for each expense category.")
    return recommendations

# Function to display recommendations page
def display_recommendations(data):
    st.title("Recommendations")
    st.markdown("### Based on Your Selected Priority")
    priority = st.radio("Select Priority", ["Savings", "Investments", "Expenses"], index=0)
    recommendations = generate_recommendations(data, priority)
    st.markdown("### Your Recommendations:")
    for rec in recommendations:
        st.markdown(f"- {rec}")
    log_user_activity({"type": "Recommendations Page", "priority": priority})

# Dynamic Dashboard Creation
def create_dashboard(data):
    st.sidebar.header("Visualization Options")
    chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Pie Chart", "3D Scatter Plot", "Area Chart"])
    numeric_columns = data.select_dtypes(include=["float", "int"]).columns.tolist()

    if not numeric_columns:
        st.error("No numeric columns found for visualization.")
        return

    x_axis = st.sidebar.selectbox("X-Axis", options=numeric_columns)
    y_axis = st.sidebar.selectbox("Y-Axis", options=numeric_columns)

    if chart_type == "Bar Chart":
        fig = px.bar(data, x=x_axis, y=y_axis, color_discrete_sequence=px.colors.qualitative.Bold)
    elif chart_type == "Line Chart":
        fig = px.line(data, x=x_axis, y=y_axis, color_discrete_sequence=px.colors.qualitative.Pastel)
    elif chart_type == "Pie Chart":
        category = st.sidebar.selectbox("Category Column", options=data.columns)
        fig = px.pie(data, names=category, values=y_axis, color_discrete_sequence=px.colors.qualitative.Safe)
    elif chart_type == "3D Scatter Plot":
        z_axis = st.sidebar.selectbox("Z-Axis", options=numeric_columns)
        fig = px.scatter_3d(data, x=x_axis, y=y_axis, z=z_axis, color=data.columns[0], color_discrete_sequence=px.colors.qualitative.Prism)
    elif chart_type == "Area Chart":
        fig = px.area(data, x=x_axis, y=y_axis, color_discrete_sequence=px.colors.qualitative.Vivid)

    st.plotly_chart(fig, use_container_width=True)
    log_user_activity({"type": "Chart Created", "chart_type": chart_type})

# Main Application
def main():
    add_bg_from_local(r"https://ibb.co/5Gd2747")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Data Analytics", "Recommendations"])

    if page == "Data Analytics":
        st.title("Smart Finance Dashboard")
        st.markdown("Upload your CSV or PDF file to generate dynamic visualizations.")
        uploaded_file = st.file_uploader("Upload CSV or PDF File", type=["csv", "pdf"])

        if uploaded_file is not None:
            with st.spinner("Loading data..."):
                data = load_data(uploaded_file)
            if data is not None:
                st.success("Data loaded successfully!")
                st.write("### Uploaded Data Preview")
                st.dataframe(data)
                create_dashboard(data)
    elif page == "Recommendations":
        st.title("Smart Finance Recommendations")
        st.markdown("Get personalized suggestions based on your financial priorities.")
        uploaded_file = st.file_uploader("Upload CSV or PDF File", type=["csv", "pdf"])
        if uploaded_file is not None:
            with st.spinner("Loading data..."):
                data = load_data(uploaded_file)
            if data is not None:
                display_recommendations(data)

if __name__ == "__main__":
    main()
