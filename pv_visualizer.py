#!/usr/bin/env python3
"""
PV Reference Data Visualization Helper
Shows interactive diagrams for PV reference data using JSON configuration files.
"""
import os
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from helper import load_and_transform_data

def get_kw_column_name(df):
    """Find the primary kW column dynamically"""
    if "kW" in df.columns:
        return "kW"
    else:
        return None


def load_pv_data(config_path):
    """Load PV data from JSON configuration file using helper functions."""
    try:
        # Use the same loading logic as analyze.py
        options = {
            "clean_columns": True,
            "show_dataframe": False,
            "show_dataframe_infos": False,
            "calc": False,
            "timer": False
        }
        bundle = load_and_transform_data(config_path, options)
        if bundle is not None:
            return bundle.df, bundle.description
        return None, None
    
    except (FileNotFoundError, ValueError, IOError) as e:
        st.error(f"Error loading file: {e}")
        return None, None


def create_daily_overview(df, description):
    """Create daily overview chart showing power data."""
    # Get the kW column name dynamically
    kw_col = get_kw_column_name(df)
    if not kw_col:
        st.error("No kW column found in data")
        return None
        
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Time Series Overview', 'Daily Pattern (Average)', 
                       'Monthly Totals', 'Power Distribution'],
        specs=[[{"colspan": 2}, None],
               [{"type": "bar"}, {"type": "histogram"}]],
        vertical_spacing=0.12
    )
    
    # 1. Time series overview (top row, full width) - using kW data
    fig.add_trace(
        go.Scatter(x=df['datetime'], y=df[kw_col], 
                  name=description, line=dict(color='gold', width=2)),
        row=1, col=1
    )
    
    # 2. Daily pattern (average by hour) - use kW for power
    df_hourly = df.groupby(df['datetime'].dt.hour)[kw_col].mean()
    
    hours = df_hourly.index
    fig.add_trace(
        go.Bar(x=hours, y=df_hourly.values, name='Hourly Average', 
               marker_color='lightblue', opacity=0.7, showlegend=False),
        row=2, col=1
    )
    
    # 3. Power distribution histogram - use kW values directly
    power_data = df[kw_col][df[kw_col] > 0]
    
    fig.add_trace(
        go.Histogram(x=power_data, name='Power Distribution', 
                    marker_color='lightgreen', opacity=0.7, showlegend=False),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        title_text=f"PV System Analysis: {description}",
        title_x=0.5
    )
    
    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_yaxes(title_text="Power (kW)", row=1, col=1)
    fig.update_xaxes(title_text="Hour of Day", row=2, col=1)
    fig.update_yaxes(title_text="Average Power (kW)", row=2, col=1)
    fig.update_xaxes(title_text="Power (kW)", row=2, col=2)
    fig.update_yaxes(title_text="Frequency", row=2, col=2)
    
    return fig
def create_monthly_comparison(df, description):
    """Create monthly comparison chart showing kW averages by month."""
    # Get the kW column name dynamically
    kw_col = get_kw_column_name(df)
    if not kw_col:
        st.error("No kW column found in data")
        return None
        
    # Calculate monthly averages from kW data
    df['month'] = df['datetime'].dt.month
    df['month_name'] = df['datetime'].dt.month_name()
    df_monthly = df.groupby('month_name')[kw_col].mean()
    
    # Reorder months properly
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    df_monthly = df_monthly.reindex([m for m in month_order if m in df_monthly.index])
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_monthly.index,
        y=df_monthly.values,
        name=description,
        marker_color='skyblue'
    ))
    
    fig.update_layout(
        title=f"Monthly Average Power Production: {description}",
        xaxis_title="Month",
        yaxis_title="Average Power (kW)",
        height=500
    )
    
    return fig


def create_heatmap(df, description):
    """Create heatmap showing power production patterns (kW)."""
    # Get the kW column name dynamically
    kw_col = get_kw_column_name(df)
    if not kw_col:
        st.error("No kW column found in data")
        return None
        
    # Create hour vs day of year heatmap for total power production
    df['hour'] = df['datetime'].dt.hour
    df['day_of_year'] = df['datetime'].dt.dayofyear
    
    pivot_data = df.pivot_table(
        values=kw_col, 
        index='hour', 
        columns='day_of_year', 
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Viridis',
        colorbar=dict(title="Power (kW)")
    ))
    
    fig.update_layout(
        title=f"Power Production Heatmap: {description} (Hour vs Day of Year)",
        xaxis_title="Day of Year",
        yaxis_title="Hour of Day",
        height=500
    )
    
    return fig


def create_statistics_table(df, description, interval_minutes=15):
    """Create statistics table showing both kW and kWh metrics.""" 
    if description is None:
        # get rid of the warning
        description = "PV System"
    # Get the kW column name dynamically
    kw_col = get_kw_column_name(df)
    if not kw_col:
        st.error("No kW column found in data")
        return None
    
    # Calculate both power and energy statistics
    interval_hours = interval_minutes / 60
    
    # Calculate kWh from kW data
    annual_energy = (df[kw_col] * interval_hours).sum()
    max_power = df[kw_col].max()
    avg_power = df[kw_col].mean()
    
    stats = [{
        'Metric': 'Annual Energy (kWh)',
        'Value': f"{annual_energy:,.0f}"
    }, {
        'Metric': 'Daily Average (kWh)',
        'Value': f"{annual_energy / 365:.1f}"
    }, {
        'Metric': 'Max Power (kW)',
        'Value': f"{max_power:.2f}"
    }, {
        'Metric': 'Avg Power (kW)',
        'Value': f"{avg_power:.2f}"
    }, {
        'Metric': 'Capacity Factor (%)',
        'Value': f"{(avg_power / max_power * 100):.1f}" if max_power > 0 else "0.0"
    }]
    
    return pd.DataFrame(stats)


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="PV Data Visualization", 
        page_icon="☀️", 
        layout="wide"
    )
    
    st.title("☀️ PV Data Visualization")
    st.markdown("Interactive analysis of PV system energy production data")
    
    # File selection using the same logic as analyze.py
    data_folder = "projects"
    
    # List all subfolders (projects) in the data folder
    if not os.path.exists(data_folder):
        st.error(f"Data folder '{data_folder}' not found.")
        return
        
    project_folders = [f for f in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, f))]
    if not project_folders:
        st.sidebar.subheader("⛓️‍💥 Projektauswahl")
        st.warning("No project folders found in the data folder.")
        return
    
    project_folders = ["leer"] + project_folders
    st.sidebar.subheader("📁 Projektauswahl")
    selected_project = st.sidebar.selectbox("Wähle ein Projekt", project_folders, index=0)
    
    if selected_project == "leer":
        st.sidebar.subheader("⛓️‍💥 Datenauswahl")
        st.warning("Please select a project first.")
        return
    
    project_path = os.path.join(data_folder, selected_project)
    json_files = sorted([f for f in os.listdir(project_path) if f.endswith(".json")])
    
    if not json_files:
        st.sidebar.subheader("⛓️‍💥 Datenauswahl")
        st.warning("No JSON files found in the selected project.")
        return
    
    st.sidebar.subheader("📂 Datenauswahl")
    selected_file = st.sidebar.selectbox("Wähle eine Datenreihe", json_files, index=0)
    
    # Construct the full file path
    file_path = os.path.join(project_path, selected_file)
    
    # Display the selected file name in the main area
    st.markdown(f"### Selected File: `{selected_file}`")
    
    # Load data
    df, description = load_pv_data(file_path)
    if df is None:
        return
    
    # Sidebar with controls
    st.sidebar.header("🔧 Analysis Controls")
    
    # Date range selector
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=[df['datetime'].min().date(), df['datetime'].max().date()],
        min_value=df['datetime'].min().date(),
        max_value=df['datetime'].max().date()
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['datetime'].dt.date >= start_date) & (df['datetime'].dt.date <= end_date)
        df_filtered = df[mask]
    else:
        df_filtered = df
    
    # Display basic info
    st.sidebar.markdown("### 📊 Data Overview")
    st.sidebar.metric("Total Data Points", f"{len(df_filtered):,}")
    st.sidebar.metric("Date Range", f"{df_filtered['datetime'].min().date()} to {df_filtered['datetime'].max().date()}")
    
    # Calculate peak power directly from kW data
    kw_col = get_kw_column_name(df_filtered)
    if kw_col:
        peak_power = df_filtered[kw_col].max()
        st.sidebar.metric("Peak Power", f"{peak_power:.1f} kW")
        
        # Calculate and display kWh totals
        if len(df_filtered) > 0:
            interval_hours = 0.25  # 15 minutes (adjust based on actual data interval)
            annual_energy = (df_filtered[kw_col] * interval_hours).sum()
            st.sidebar.metric("Total Energy", f"{annual_energy:,.0f} kWh")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("⚡ Power Production Overview") 
        
        # Daily overview chart
        fig_overview = create_daily_overview(df_filtered, description)
        if fig_overview:
            st.plotly_chart(fig_overview, use_container_width=True)
        
        # Monthly comparison
        st.header("📅 Monthly Power Averages")
        fig_monthly = create_monthly_comparison(df_filtered, description)
        if fig_monthly:
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Heatmap
        st.header("🌡️ Power Production Heatmap")
        fig_heatmap = create_heatmap(df_filtered, description)
        if fig_heatmap:
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col2:
        st.header("📋 Statistics")
        
        # Statistics table
        stats_df = create_statistics_table(df_filtered, description)
        if stats_df is not None:
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        # Key metrics from kW data
        st.markdown("### 🎯 Key Metrics")
        if len(df_filtered) > 0 and kw_col:
            # Energy metrics
            interval_hours = 0.25  # 15 minutes
            annual_energy = (df_filtered[kw_col] * interval_hours).sum()
            st.metric("Total Production", f"{annual_energy:,.0f} kWh")
            
            # Power metrics
            peak_power = df_filtered[kw_col].max()
            avg_power = df_filtered[kw_col].mean()
            st.metric("Peak Power Output", f"{peak_power:.1f} kW")
            st.metric("Average Power", f"{avg_power:.2f} kW")
            st.metric("Capacity Factor", f"{(avg_power / peak_power * 100):.1f}%" if peak_power > 0 else "0%")
        
        # Download data option
        st.markdown("### 💾 Export Data")
        csv_data = df_filtered.to_csv(index=False)
        st.download_button(
            label="Download CSV (kW data)",
            data=csv_data,
            file_name=f"pv_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()