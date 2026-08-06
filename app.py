
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import seaborn as sns
import io
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="CSV Data Analysis & Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = None

def load_data(uploaded_file):
    """Load and validate CSV data"""
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        data = None
        
        for encoding in encodings:
            try:
                uploaded_file.seek(0)  # Reset file pointer
                data = pd.read_csv(uploaded_file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if data is None:
            st.error("Unable to decode the CSV file. Please check the file encoding.")
            return None
            
        return data
    except Exception as e:
        st.error(f"Error loading CSV file: {str(e)}")
        return None

def get_basic_statistics(data, column):
    """Calculate basic statistics for a column"""
    if data[column].dtype in ['object', 'category']:
        return {
            'Count': len(data[column]),
            'Unique Values': data[column].nunique(),
            'Most Frequent': data[column].mode().iloc[0] if not data[column].mode().empty else 'N/A',
            'Missing Values': data[column].isnull().sum()
        }
    else:
        return {
            'Count': len(data[column]),
            'Mean': data[column].mean(),
            'Median': data[column].median(),
            'Mode': data[column].mode().iloc[0] if not data[column].mode().empty else 'N/A',
            'Standard Deviation': data[column].std(),
            'Min': data[column].min(),
            'Max': data[column].max(),
            'Missing Values': data[column].isnull().sum()
        }

def create_histogram(data, column):
    """Create histogram for numerical columns"""
    fig = px.histogram(
        data, 
        x=column, 
        title=f'Distribution of {column}',
        nbins=30,
        marginal="box"
    )
    fig.update_layout(
        xaxis_title=column,
        yaxis_title='Frequency',
        showlegend=False
    )
    return fig

def create_bar_chart(data, column, top_n=20):
    """Create bar chart for categorical columns"""
    value_counts = data[column].value_counts().head(top_n)
    
    fig = px.bar(
        x=value_counts.index,
        y=value_counts.values,
        title=f'Top {min(top_n, len(value_counts))} Values in {column}',
        labels={'x': column, 'y': 'Count'}
    )
    fig.update_layout(
        xaxis_title=column,
        yaxis_title='Count',
        xaxis_tickangle=-45
    )
    return fig

def create_scatter_plot(data, x_col, y_col, color_col=None):
    """Create scatter plot"""
    fig = px.scatter(
        data,
        x=x_col,
        y=y_col,
        color=color_col if color_col else None,
        title=f'{y_col} vs {x_col}',
        hover_data=data.columns[:5].tolist()  # Show first 5 columns on hover
    )
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col
    )
    return fig

def create_line_plot(data, x_col, y_col, color_col=None):
    """Create line plot"""
    if color_col:
        fig = px.line(
            data,
            x=x_col,
            y=y_col,
            color=color_col,
            title=f'{y_col} over {x_col}',
            markers=True
        )
    else:
        fig = px.line(
            data,
            x=x_col,
            y=y_col,
            title=f'{y_col} over {x_col}',
            markers=True
        )
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col
    )
    return fig

def apply_filters(data):
    """Apply filters to the dataset"""
    filtered_data = data.copy()
    
    st.sidebar.subheader("Data Filters")
    
    # Column filters
    for col in data.columns:
        if data[col].dtype in ['object', 'category']:
            # Categorical filter
            unique_values = data[col].unique()
            if len(unique_values) <= 50:  # Only show filter for columns with reasonable number of unique values
                selected_values = st.sidebar.multiselect(
                    f"Filter {col}",
                    options=unique_values,
                    default=unique_values
                )
                if selected_values:
                    filtered_data = filtered_data[filtered_data[col].isin(selected_values)]
        
        elif data[col].dtype in ['int64', 'float64']:
            # Numerical filter
            col_min, col_max = float(data[col].min()), float(data[col].max())
            if col_min != col_max:
                selected_range = st.sidebar.slider(
                    f"Filter {col}",
                    min_value=col_min,
                    max_value=col_max,
                    value=(col_min, col_max),
                    step=(col_max - col_min) / 100
                )
                filtered_data = filtered_data[
                    (filtered_data[col] >= selected_range[0]) & 
                    (filtered_data[col] <= selected_range[1])
                ]
    
    return filtered_data

def main():
    st.title("📊 CSV Data Analysis & Visualization")
    st.markdown("Upload a CSV file to perform data analysis and create interactive visualizations.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file to analyze. Supported encodings: UTF-8, Latin-1, ISO-8859-1, CP1252"
    )
    
    if uploaded_file is not None:
        # Load data
        with st.spinner("Loading data..."):
            data = load_data(uploaded_file)
        
        if data is not None:
            st.session_state.data = data
            st.success(f"Successfully loaded {len(data)} rows and {len(data.columns)} columns!")
            
            # Data preview
            st.subheader("📋 Data Preview")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Rows", len(data))
            with col2:
                st.metric("Total Columns", len(data.columns))
            with col3:
                st.metric("Missing Values", data.isnull().sum().sum())
            
            # Show first few rows
            st.dataframe(data.head(10), use_container_width=True)
            
            # Data types and info
            with st.expander("📊 Column Information"):
                col_info = pd.DataFrame({
                    'Column': data.columns,
                    'Data Type': data.dtypes.astype(str),
                    'Non-Null Count': data.count(),
                    'Null Count': data.isnull().sum(),
                    'Unique Values': data.nunique()
                })
                st.dataframe(col_info, use_container_width=True)
            
            # Apply filters
            filtered_data = apply_filters(data)
            st.session_state.filtered_data = filtered_data
            
            if len(filtered_data) != len(data):
                st.info(f"Showing {len(filtered_data)} rows after filtering (from {len(data)} total rows)")
            
            # Analysis tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Statistical Analysis", "📊 Single Variable Analysis", "🔗 Multi-Variable Analysis", "📋 Data Summary"])
            
            with tab1:
                st.subheader("Statistical Analysis")
                
                # Select column for analysis
                numeric_columns = filtered_data.select_dtypes(include=[np.number]).columns.tolist()
                categorical_columns = filtered_data.select_dtypes(include=['object', 'category']).columns.tolist()
                all_columns = filtered_data.columns.tolist()
                
                selected_column = st.selectbox("Select column for statistical analysis:", all_columns)
                
                if selected_column:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.subheader("Statistics")
                        stats = get_basic_statistics(filtered_data, selected_column)
                        for stat, value in stats.items():
                            if isinstance(value, float):
                                st.metric(stat, f"{value:.2f}")
                            else:
                                st.metric(stat, value)
                    
                    with col2:
                        st.subheader("Distribution")
                        if selected_column in numeric_columns:
                            fig = create_histogram(filtered_data, selected_column)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            fig = create_bar_chart(filtered_data, selected_column)
                            st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.subheader("Single Variable Analysis")
                
                # Chart type selection
                chart_type = st.selectbox(
                    "Select chart type:",
                    ["Histogram", "Bar Chart", "Box Plot"]
                )
                
                if chart_type == "Histogram":
                    if numeric_columns:
                        column = st.selectbox("Select numeric column:", numeric_columns)
                        bins = st.slider("Number of bins:", 10, 100, 30)
                        
                        fig = px.histogram(filtered_data, x=column, nbins=bins, title=f'Histogram of {column}')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Export option
                        if st.button("Export Histogram"):
                            fig.write_html("histogram.html")
                            st.success("Chart exported as histogram.html")
                    else:
                        st.warning("No numeric columns available for histogram.")
                
                elif chart_type == "Bar Chart":
                    if categorical_columns:
                        column = st.selectbox("Select categorical column:", categorical_columns)
                        top_n = st.slider("Show top N values:", 5, 50, 20)
                        
                        fig = create_bar_chart(filtered_data, column, top_n)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Export option
                        if st.button("Export Bar Chart"):
                            fig.write_html("bar_chart.html")
                            st.success("Chart exported as bar_chart.html")
                    else:
                        st.warning("No categorical columns available for bar chart.")
                
                elif chart_type == "Box Plot":
                    if numeric_columns:
                        column = st.selectbox("Select numeric column:", numeric_columns)
                        
                        fig = px.box(filtered_data, y=column, title=f'Box Plot of {column}')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Export option
                        if st.button("Export Box Plot"):
                            fig.write_html("box_plot.html")
                            st.success("Chart exported as box_plot.html")
                    else:
                        st.warning("No numeric columns available for box plot.")
            
            with tab3:
                st.subheader("Multi-Variable Analysis")
                
                # Chart type selection
                multi_chart_type = st.selectbox(
                    "Select visualization type:",
                    ["Scatter Plot", "Line Plot", "Correlation Heatmap"]
                )
                
                if multi_chart_type == "Scatter Plot":
                    if len(numeric_columns) >= 2:
                        col1, col2 = st.columns(2)
                        with col1:
                            x_column = st.selectbox("Select X-axis:", numeric_columns)
                        with col2:
                            y_column = st.selectbox("Select Y-axis:", numeric_columns)
                        
                        # Optional color column
                        color_column = st.selectbox("Color by (optional):", [None] + all_columns)
                        
                        fig = create_scatter_plot(filtered_data, x_column, y_column, color_column)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Export option
                        if st.button("Export Scatter Plot"):
                            fig.write_html("scatter_plot.html")
                            st.success("Chart exported as scatter_plot.html")
                    else:
                        st.warning("Need at least 2 numeric columns for scatter plot.")
                
                elif multi_chart_type == "Line Plot":
                    if len(all_columns) >= 2:
                        col1, col2 = st.columns(2)
                        with col1:
                            x_column = st.selectbox("Select X-axis:", all_columns)
                        with col2:
                            y_columns = st.multiselect("Select Y-axis:", numeric_columns)
                        
                        if y_columns:
                            # Optional color column
                            color_column = st.selectbox("Group by (optional):", [None] + categorical_columns)
                            
                            for y_col in y_columns:
                                fig = create_line_plot(filtered_data, x_column, y_col, color_column)
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Export option
                            if st.button("Export Line Plot"):
                                fig.write_html("line_plot.html")
                                st.success("Chart exported as line_plot.html")
                    else:
                        st.warning("Need at least 2 columns for line plot.")
                
                elif multi_chart_type == "Correlation Heatmap":
                    if len(numeric_columns) >= 2:
                        correlation_matrix = filtered_data[numeric_columns].corr()
                        
                        fig = px.imshow(
                            correlation_matrix,
                            title="Correlation Heatmap",
                            color_continuous_scale="RdBu_r",
                            aspect="auto"
                        )
                        fig.update_layout(width=800, height=600)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Export option
                        if st.button("Export Heatmap"):
                            fig.write_html("correlation_heatmap.html")
                            st.success("Chart exported as correlation_heatmap.html")
                    else:
                        st.warning("Need at least 2 numeric columns for correlation heatmap.")
            
            with tab4:
                st.subheader("Data Summary")
                
                # Overall summary
                st.write("**Dataset Overview:**")
                summary_stats = filtered_data.describe(include='all')
                st.dataframe(summary_stats, use_container_width=True)
                
                # Missing values analysis
                st.write("**Missing Values Analysis:**")
                missing_data = pd.DataFrame({
                    'Column': filtered_data.columns,
                    'Missing Count': filtered_data.isnull().sum(),
                    'Missing Percentage': (filtered_data.isnull().sum() / len(filtered_data)) * 100
                })
                missing_data = missing_data[missing_data['Missing Count'] > 0].sort_values('Missing Count', ascending=False)
                
                if not missing_data.empty:
                    st.dataframe(missing_data, use_container_width=True)
                    
                    # Visualize missing values
                    fig = px.bar(
                        missing_data,
                        x='Column',
                        y='Missing Count',
                        title='Missing Values by Column'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.success("No missing values found in the dataset!")
                
                # Data export
                st.subheader("Export Data")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Download Filtered Data as CSV"):
                        csv = filtered_data.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with col2:
                    if st.button("Download Summary Statistics"):
                        summary_csv = summary_stats.to_csv()
                        st.download_button(
                            label="Download Summary",
                            data=summary_csv,
                            file_name=f"summary_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
    
    else:
        st.info("👆 Please upload a CSV file to begin analysis.")
        
        # Sample data format info
        with st.expander("ℹ️ Supported CSV Format"):
            st.write("""
            **Supported file format:**
            - CSV files (.csv extension)
            - Multiple encodings supported: UTF-8, Latin-1, ISO-8859-1, CP1252
            - First row should contain column headers
            - Data can contain both numerical and categorical columns
            
            **Tips for best results:**
            - Ensure consistent data formatting within columns
            - Use clear, descriptive column names
            - Handle missing values appropriately (empty cells are okay)
            - Avoid special characters in column names when possible
            """)

if __name__ == "__main__":
    main()
