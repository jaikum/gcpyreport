import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="GitHub Copilot Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("GitHub Copilot Analytics Dashboard")
st.markdown("""
This dashboard provides insights into GitHub Copilot usage metrics including:
- IDE Chat usage
- Code completions
- User engagement
- Language-specific metrics
""")

# Function to process the data
def flatten_data(data):
    rows = []
    ide_chat_data = []
    code_completion_data = []
    for entry in data:
        date = pd.to_datetime(entry.get('date'))
        total_active_users = entry.get('total_active_users', 0)
        total_engaged_users = entry.get('total_engaged_users', 0)
        
        # IDE Chat
        ide_chat = entry.get('copilot_ide_chat', {})
        for editor in ide_chat.get('editors', []):
            editor_name = editor.get('name')
            for model in editor.get('models', []):
                ide_chat_data.append({
                    'date': date,
                    'editor': editor_name,
                    'model': model.get('name'),
                    'is_custom_model': model.get('is_custom_model', False),
                    'total_chats': model.get('total_chats', 0),
                    'total_engaged_users': model.get('total_engaged_users', 0),
                    'total_chat_copy_events': model.get('total_chat_copy_events', 0),
                    'total_chat_insertion_events': model.get('total_chat_insertion_events', 0)
                })

        # IDE Code Completions
        ide_code = entry.get('copilot_ide_code_completions', {})
        for editor in ide_code.get('editors', []):
            editor_name = editor.get('name')
            for model in editor.get('models', []):
                model_name = model.get('name')
                is_custom_model = model.get('is_custom_model', False)
                for lang in model.get('languages', []):
                    code_completion_data.append({
                        'date': date,
                        'editor': editor_name,
                        'model': model_name,
                        'is_custom_model': is_custom_model,
                        'language': lang.get('name'),
                        'total_engaged_users': lang.get('total_engaged_users', 0),
                        'total_code_acceptances': lang.get('total_code_acceptances', 0),
                        'total_code_suggestions': lang.get('total_code_suggestions', 0),
                        'total_code_lines_accepted': lang.get('total_code_lines_accepted', 0),
                        'total_code_lines_suggested': lang.get('total_code_lines_suggested', 0)
                    })

        rows.append({
            'date': date,
            'total_active_users': total_active_users,
            'total_engaged_users': total_engaged_users,
            'copilot_ide_chat.total_engaged_users': ide_chat.get('total_engaged_users', 0),
            'copilot_ide_code_completions.total_engaged_users': ide_code.get('total_engaged_users', 0),
            'copilot_dotcom_chat.total_engaged_users': entry.get('copilot_dotcom_chat', {}).get('total_engaged_users', 0),
            'copilot_dotcom_pull_requests.total_engaged_users': entry.get('copilot_dotcom_pull_requests', {}).get('total_engaged_users', 0)
        })

    df = pd.DataFrame(rows)
    ide_chat_df = pd.DataFrame(ide_chat_data)
    code_completion_df = pd.DataFrame(code_completion_data)
    return df, ide_chat_df, code_completion_df

def process_data(data):
    return flatten_data(data)

# Function to create visualizations
def create_visualizations(df, ide_chat_df, code_completion_df):
    # Ensure 'date' columns are datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if 'date' in ide_chat_df.columns:
        ide_chat_df['date'] = pd.to_datetime(ide_chat_df['date'], errors='coerce')
    if 'date' in code_completion_df.columns:
        code_completion_df['date'] = pd.to_datetime(code_completion_df['date'], errors='coerce')

    # 1. Daily Active Users
    fig_users = px.line(df, x='date', y='total_active_users',
                       title='Daily Active Users',
                       labels={'date': 'Date', 'total_active_users': 'Active Users'})

    # 2. IDE Chat Usage by Editor
    fig_ide_chat = px.bar(ide_chat_df.groupby(['date', 'editor'])['total_chats'].sum().reset_index(),
                         x='date', y='total_chats', color='editor',
                         title='IDE Chat Usage by Editor',
                         labels={'date': 'Date', 'total_chats': 'Total Chats', 'editor': 'Editor'})

    # 3. Code Completion Metrics by Language
    fig_code_completion = px.bar(code_completion_df.groupby('language')['total_code_suggestions'].sum().reset_index(),
                               x='language', y='total_code_suggestions',
                               title='Total Code Suggestions by Language',
                               labels={'language': 'Language', 'total_code_suggestions': 'Total Suggestions'})

    # 4. Code Acceptance Rate
    code_completion_df['acceptance_rate'] = (code_completion_df['total_code_acceptances'] /
                                           code_completion_df['total_code_suggestions'] * 100)
    fig_acceptance = px.bar(code_completion_df.groupby('language')['acceptance_rate'].mean().reset_index(),
                          x='language', y='acceptance_rate',
                          title='Code Acceptance Rate by Language (%)',
                          labels={'language': 'Language', 'acceptance_rate': 'Acceptance Rate (%)'})

    # 5. User Engagement Over Time
    fig_engagement = px.line(df, x='date', 
                           y=['total_active_users', 'total_engaged_users',
                              'copilot_ide_chat.total_engaged_users',
                              'copilot_ide_code_completions.total_engaged_users',
                              'copilot_dotcom_chat.total_engaged_users',
                              'copilot_dotcom_pull_requests.total_engaged_users'],
                           title='User Engagement Over Time',
                           labels={'date': 'Date', 'value': 'Number of Users', 'variable': 'User Type'})

    # 6. Daily Usage Heatmap
    df['day_of_week'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    usage_heatmap = df.pivot_table(
        values='total_active_users',
        index='day_of_week',
        columns='hour',
        aggfunc='mean'
    ).fillna(0)
    
    fig_heatmap = px.imshow(usage_heatmap,
                           title='Average User Activity by Day and Hour',
                           labels={'x': 'Hour of Day', 'y': 'Day of Week', 'color': 'Active Users'})
    
    return fig_users, fig_ide_chat, fig_code_completion, fig_acceptance, fig_engagement, fig_heatmap

# Main dashboard layout
def main():
    # Sidebar for JSON input and filters
    st.sidebar.title("Data Input & Filters")
    
    # JSON input
    st.sidebar.subheader("Usage Data")
    json_input = st.sidebar.text_area("Paste your usage JSON data here:", height=200)
    
    # Default data
    default_data = [
        # Your provided JSON data here
    ]
    
    try:
        # Process usage data
        if json_input:
            data = json.loads(json_input)
        else:
            data = default_data
            
        # Process data
        df, ide_chat_df, code_completion_df = process_data(data)
        
        # Add date filters in sidebar
        st.sidebar.subheader("Date Range Filter")
        df['date'] = pd.to_datetime(df['date'])
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        
        start_date = st.sidebar.date_input(
            "Start Date",
            min_date,
            min_value=min_date,
            max_value=max_date
        )
        
        end_date = st.sidebar.date_input(
            "End Date",
            max_date,
            min_value=min_date,
            max_value=max_date
        )
        
        # Convert date inputs to datetime
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        # Convert string dates to datetime in dataframes if they aren't already
        df['date'] = pd.to_datetime(df['date'])
        ide_chat_df['date'] = pd.to_datetime(ide_chat_df['date'])
        code_completion_df['date'] = pd.to_datetime(code_completion_df['date'])
        
        # Convert input dates to datetime64[ns] for comparison
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        
        # Filter data based on date range
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        ide_chat_df = ide_chat_df[(ide_chat_df['date'] >= start_date) & (ide_chat_df['date'] <= end_date)]
        code_completion_df = code_completion_df[(code_completion_df['date'] >= start_date) & (code_completion_df['date'] <= end_date)]
        
        # Create visualizations
        fig_users, fig_ide_chat, fig_code_completion, fig_acceptance, fig_engagement, fig_heatmap = create_visualizations(
            df, ide_chat_df, code_completion_df
        )
        
        # Display date range
        st.subheader(f"Data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Active Users", df['total_active_users'].sum())
        with col2:
            st.metric("Total IDE Chats", ide_chat_df['total_chats'].sum())
        with col3:
            st.metric("Total Code Suggestions", code_completion_df['total_code_suggestions'].sum())
        with col4:
            st.metric("Total Code Acceptances", code_completion_df['total_code_acceptances'].sum())
        
        # User Statistics Section
        st.subheader("User Statistics")
        user_col1, user_col2, user_col3 = st.columns(3)
        
        with user_col1:
            st.metric("Average Daily Active Users", round(df['total_active_users'].mean(), 2))
            st.metric("Peak Active Users", df['total_active_users'].max())
            st.metric("Total Unique Engaged Users", df['total_engaged_users'].sum())
        
        with user_col2:
            st.metric("Average Daily Engagement Rate", 
                     round((df['total_engaged_users'].sum() / df['total_active_users'].sum()) * 100, 2),
                     delta=f"{round((df['total_engaged_users'].iloc[-1] / df['total_active_users'].iloc[-1] - df['total_engaged_users'].iloc[0] / df['total_active_users'].iloc[0]) * 100, 2)}%")
            st.metric("Average Chats per User", 
                     round(ide_chat_df['total_chats'].sum() / df['total_active_users'].sum(), 2))
            st.metric("Average Code Acceptances per User",
                     round(code_completion_df['total_code_acceptances'].sum() / df['total_active_users'].sum(), 2))
        
        with user_col3:
            st.metric("GitHub.com Chat Users", df['copilot_dotcom_chat.total_engaged_users'].sum())
            st.metric("GitHub.com PR Users", df['copilot_dotcom_pull_requests.total_engaged_users'].sum())
            engagement_ratio = round((df['copilot_ide_chat.total_engaged_users'].sum() / df['total_engaged_users'].sum()) * 100, 2)
            st.metric("IDE Chat Engagement Ratio", f"{engagement_ratio}%")
        
        # Display visualizations
        st.plotly_chart(fig_users, use_container_width=True)
        st.plotly_chart(fig_engagement, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_ide_chat, use_container_width=True)
        with col2:
            st.plotly_chart(fig_code_completion, use_container_width=True)
        
        st.plotly_chart(fig_acceptance, use_container_width=True)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Additional metrics and tables
        st.subheader("Detailed Metrics")
        tabs = ["IDE Chat Metrics", "Code Completion Metrics", "User Engagement Metrics"]
        
        tab1, tab2, tab3 = st.tabs(tabs)
        
        with tab1:
            # Calculate IDE Chat metrics with totals
            ide_chat_metrics = ide_chat_df.groupby('editor').agg({
                'total_chats': 'sum',
                'total_engaged_users': 'sum',
                'total_chat_copy_events': 'sum',
                'total_chat_insertion_events': 'sum'
            }).reset_index()
            
            # Add total row
            total_row = pd.DataFrame([{
                'editor': 'TOTAL',
                'total_chats': ide_chat_metrics['total_chats'].sum(),
                'total_engaged_users': ide_chat_metrics['total_engaged_users'].sum(),
                'total_chat_copy_events': ide_chat_metrics['total_chat_copy_events'].sum(),
                'total_chat_insertion_events': ide_chat_metrics['total_chat_insertion_events'].sum()
            }])
            
            # Combine metrics with total row
            ide_chat_metrics = pd.concat([ide_chat_metrics, total_row], ignore_index=True)
            st.dataframe(ide_chat_metrics)
        
        with tab2:
            # Calculate Code Completion metrics with totals
            code_completion_metrics = code_completion_df.groupby('language').agg({
                'total_code_suggestions': 'sum',
                'total_code_acceptances': 'sum',
                'total_code_lines_suggested': 'sum',
                'total_code_lines_accepted': 'sum'
            }).reset_index()
            
            # Add total row
            total_row = pd.DataFrame([{
                'language': 'TOTAL',
                'total_code_suggestions': code_completion_metrics['total_code_suggestions'].sum(),
                'total_code_acceptances': code_completion_metrics['total_code_acceptances'].sum(),
                'total_code_lines_suggested': code_completion_metrics['total_code_lines_suggested'].sum(),
                'total_code_lines_accepted': code_completion_metrics['total_code_lines_accepted'].sum()
            }])
            
            # Combine metrics with total row
            code_completion_metrics = pd.concat([code_completion_metrics, total_row], ignore_index=True)
            st.dataframe(code_completion_metrics)
            
        with tab3:
            # Calculate User Engagement metrics
            user_engagement_metrics = df.groupby('date').agg({
                'total_active_users': 'sum',
                'total_engaged_users': 'sum',
                'copilot_ide_chat.total_engaged_users': 'sum',
                'copilot_ide_code_completions.total_engaged_users': 'sum'
            }).reset_index()
            
            # Calculate engagement rates
            user_engagement_metrics['chat_engagement_rate'] = (user_engagement_metrics['copilot_ide_chat.total_engaged_users'] / 
                                                            user_engagement_metrics['total_active_users'] * 100)
            user_engagement_metrics['code_engagement_rate'] = (user_engagement_metrics['copilot_ide_code_completions.total_engaged_users'] / 
                                                            user_engagement_metrics['total_active_users'] * 100)
            
            st.dataframe(user_engagement_metrics)
            
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.info("Please check your JSON input format and try again.")

if __name__ == "__main__":
    main()
