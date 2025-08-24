import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
from dateutil import parser

# Set page config
st.set_page_config(
    page_title="Seat Management Dashboard",
    page_icon="💺",
    layout="wide"
)

# Title and description
st.title("💺 Seat Management Dashboard")
st.markdown("""
This dashboard provides insights into seat allocation, usage, and team distribution.
Use the filters on the sidebar to analyze specific time periods and teams.
""")

# Load and process data
@st.cache_data
def process_data(json_data):
    # Convert seats array to DataFrame
    df = pd.DataFrame(json_data.get('seats', []))
    if df.empty:
        return df
    
    # Convert datetime strings to datetime objects
    date_columns = ['created_at', 'updated_at', 'last_activity_at']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    # Extract team information
    if 'assigning_team' in df.columns:
        df['team_name'] = df['assigning_team'].apply(lambda x: x.get('name') if x else None)
        df['team_id'] = df['assigning_team'].apply(lambda x: x.get('id') if x else None)
    
    # Extract assignee information
    if 'assignee' in df.columns:
        df['user_login'] = df['assignee'].apply(lambda x: x.get('login') if x else None)
        df['user_type'] = df['assignee'].apply(lambda x: x.get('type') if x else None)
        df['user_id'] = df['assignee'].apply(lambda x: x.get('id') if x else None)
    
    # Add total seats count from the root level
    df['total_available_seats'] = json_data.get('total_seats', 0)
    
    return df

# Sidebar JSON input
st.sidebar.header("Input Data")
json_input = st.sidebar.text_area(
    "Paste your JSON data here",
    height=300,
    help="Paste the JSON data containing seat information"
)

# Process JSON input
if json_input:
    try:
        data = json.loads(json_input)
        df = process_data(data)
    except json.JSONDecodeError:
        st.error("Invalid JSON format. Please check your input.")
        st.stop()
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.stop()
else:
    st.warning("Please paste your JSON data in the sidebar to begin.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

# Date range filter
min_date = df['created_at'].min().date()
max_date = df['created_at'].max().date()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Team filter
all_teams = ['All Teams'] + sorted(df['team_name'].unique().tolist())
selected_team = st.sidebar.selectbox("Select Team", all_teams)

# Apply filters
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['created_at'].dt.date >= start_date) & (df['created_at'].dt.date <= end_date)
    filtered_df = df[mask]
else:
    filtered_df = df

if selected_team != 'All Teams':
    filtered_df = filtered_df[filtered_df['team_name'] == selected_team]

# Main content
st.header("Overview")
col1, col2, col3, col4 = st.columns(4)

# Key metrics
with col1:
    total_seats = filtered_df['total_available_seats'].iloc[0] if not filtered_df.empty else 0
    st.metric("Total Available Seats", total_seats)

with col2:
    assigned_seats = len(filtered_df)
    st.metric("Assigned Seats", assigned_seats)

with col3:
    active_users = filtered_df['last_activity_at'].notna().sum()
    inactive_users = filtered_df['last_activity_at'].isna().sum()
    st.metric("Active Users", active_users)

with col4:
    unassigned_seats = total_seats - assigned_seats
    st.metric("Unassigned Seats", unassigned_seats)

# Team distribution and activity visualizations
col1, col2 = st.columns(2)

with col1:
    st.subheader("Team Distribution")
    team_counts = filtered_df['team_name'].value_counts()
    fig_team = px.pie(
        values=team_counts.values,
        names=team_counts.index,
        title="Seat Distribution by Team"
    )
    fig_team.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_team, use_container_width=True)

with col2:
    st.subheader("Activity Timeline")
    activity_data = filtered_df[filtered_df['last_activity_at'].notna()].copy()
    activity_data['date'] = activity_data['last_activity_at'].dt.date
    daily_activity = activity_data.groupby('date').size().reset_index(name='count')
    fig_timeline = px.line(
        daily_activity,
        x='date',
        y='count',
        title="Daily Active Users"
    )
    fig_timeline.update_traces(mode='lines+markers')
    st.plotly_chart(fig_timeline, use_container_width=True)

# Team-wise summary table
st.subheader("Team-wise User Summary")
team_summary = filtered_df.groupby('team_name').agg({
    'user_login': 'count',
    'last_activity_at': lambda x: x.notna().sum(),
    'created_at': 'min'
}).reset_index()

team_summary.columns = ['Team', 'Total Users', 'Active Users', 'First Seat Created']
team_summary['Inactive Users'] = team_summary['Total Users'] - team_summary['Active Users']
team_summary['Active %'] = (team_summary['Active Users'] / team_summary['Total Users'] * 100).round(1)
team_summary['First Seat Created'] = team_summary['First Seat Created'].dt.date

# Sort by total users in descending order
team_summary = team_summary.sort_values('Total Users', ascending=False)

# Display the summary table
st.dataframe(
    team_summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Active %": st.column_config.NumberColumn(
            "Active %",
            help="Percentage of active users in the team",
            format="%.1f%%"
        ),
        "First Seat Created": st.column_config.DateColumn(
            "First Seat Created",
            help="Date when the first seat was created for this team"
        )
    }
)

# Detailed view
st.subheader("Detailed Seat Information")
detailed_view = filtered_df[[
    'user_login',
    'team_name',
    'created_at',
    'last_activity_at',
    'last_activity_editor',
    'plan_type'
]].copy()

detailed_view.columns = [
    'User',
    'Team',
    'Created Date',
    'Last Activity',
    'Last Editor',
    'Plan Type'
]

st.dataframe(
    detailed_view,
    use_container_width=True,
    hide_index=True
)

# Export functionality
if st.button("Export to CSV"):
    csv = detailed_view.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="seat_report.csv",
        mime="text/csv"
    )
