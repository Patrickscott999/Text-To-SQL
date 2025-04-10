import streamlit as st
import sqlite3
import pandas as pd
from llm_sql import gpt_generate_sql, explain_query, generate_followup_questions, suggest_question_improvements, analyze_query
import os
import tempfile
import sqlalchemy
import mysql.connector
from sqlalchemy import create_engine, inspect
import time
import hashlib
import traceback
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Text-to-SQL AI", layout="wide")

# Initialize session state for API key
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.environ.get("OPENAI_API_KEY", "")

# Initialize session state for database connection and query caching
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
    
if 'db_type' not in st.session_state:
    st.session_state.db_type = "sqlite"
    
if 'db_path' not in st.session_state:
    st.session_state.db_path = "your_database.db"

if 'schema_info' not in st.session_state:
    st.session_state.schema_info = {}
    
if 'schema_text' not in st.session_state:
    st.session_state.schema_text = ""

# Query cache implementation
if 'query_cache' not in st.session_state:
    st.session_state.query_cache = {}

# Pagination state
if 'page_number' not in st.session_state:
    st.session_state.page_number = 0
    
if 'rows_per_page' not in st.session_state:
    st.session_state.rows_per_page = 10

# AI enhancement states
if 'current_sql' not in st.session_state:
    st.session_state.current_sql = ""
    
if 'follow_up_questions' not in st.session_state:
    st.session_state.follow_up_questions = []
    
if 'sql_edited' not in st.session_state:
    st.session_state.sql_edited = False
    
if 'current_explanation' not in st.session_state:
    st.session_state.current_explanation = ""
    
if 'improved_question' not in st.session_state:
    st.session_state.improved_question = ""

# Query history tracking
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Function to generate cache key for a query
def get_cache_key(query):
    # Create a hash of the query for cache key
    return hashlib.md5(query.encode('utf-8')).hexdigest()

# Database connection functions
def get_sqlite_connection(db_path):
    """Connect to an SQLite database."""
    try:
        if not db_path:
            return None
            
        conn = sqlite3.connect(db_path, check_same_thread=False)
        print(f"SQLite connection successful to {db_path}")
        return conn
    except Exception as e:
        st.error(f"Error connecting to SQLite database: {str(e)}")
        return None

def get_sql_connection(db_type, host, port, database, username, password):
    """Connect to various SQL databases using SQLAlchemy."""
    try:
        if db_type == "mysql":
            connection_string = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "postgresql":
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        else:
            st.error(f"Unsupported database type: {db_type}")
            return None, None
            
        engine = create_engine(connection_string)
        conn = engine.connect()
        print(f"{db_type.upper()} connection successful to {host}:{port}/{database}")
        return conn, engine
    except Exception as e:
        st.error(f"Error connecting to {db_type.upper()} database: {str(e)}")
        return None, None

# Get current database connection
def get_database_connection():
    """Get database connection based on session state."""
    if st.session_state.db_type == "sqlite":
        return get_sqlite_connection(st.session_state.db_path)
    else:
        conn, _ = get_sql_connection(
            st.session_state.db_type,
            st.session_state.db_host,
            st.session_state.db_port,
            st.session_state.db_name,
            st.session_state.db_user,
            st.session_state.db_password
        )
        return conn

# Schema extraction functions
def get_sqlite_schema(db_path):
    """Extract schema information from an SQLite database."""
    try:
        if not db_path:
            return "", {}
            
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_info = {}
        schema_text = ""
        
        for table in tables:
            table_name = table[0]
            schema_text += f"<div class='table-header'>📊 Table: <span class='table-name'>{table_name}</span></div>\n"
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            column_info = []
            for col in columns:
                col_type = col[2]
                # Apply different colors based on data type
                if 'INT' in col_type.upper():
                    type_class = 'number-type'
                elif 'TEXT' in col_type.upper() or 'CHAR' in col_type.upper():
                    type_class = 'text-type'
                elif 'REAL' in col_type.upper() or 'FLOAT' in col_type.upper() or 'DOUB' in col_type.upper():
                    type_class = 'float-type'
                elif 'DATE' in col_type.upper() or 'TIME' in col_type.upper():
                    type_class = 'date-type'
                else:
                    type_class = 'other-type'
                
                # Add primary key indicator
                pk_class = ' primary-key' if col[5] else ''
                
                schema_text += f"<div class='column-row{pk_class}'>"
                schema_text += f"<span class='column-name'>{col[1]}</span>"
                schema_text += f"<span class='column-type {type_class}'>({col_type})</span>"
                
                # Add constraints indicators
                constraints = []
                if col[5]:  # is_pk
                    constraints.append("<span class='pk-badge'>PK</span>")
                if col[3]:  # not_null
                    constraints.append("<span class='nn-badge'>NN</span>")
                
                if constraints:
                    schema_text += f"<span class='constraints'>{''.join(constraints)}</span>"
                
                schema_text += "</div>\n"
                
                column_info.append({
                    "name": col[1],
                    "type": col[2],
                    "notnull": col[3],
                    "default_value": col[4],
                    "is_primary_key": col[5]
                })
            
            schema_info[table_name] = column_info
            print(f"Processed schema for SQLite table: {table_name} ({len(column_info)} columns)")
        
        conn.close()
        return schema_text, schema_info
    except Exception as e:
        st.error(f"Error reading SQLite schema: {str(e)}")
        return "", {}

def get_sql_schema(engine):
    """Extract schema information from a SQL database using SQLAlchemy."""
    try:
        if not engine:
            return "", {}

        inspector = inspect(engine)
        schema_info = {}
        schema_text = ""
        
        # Get all table names
        tables = inspector.get_table_names()
        
        for table_name in tables:
            schema_text += f"<div class='table-header'>📊 Table: <span class='table-name'>{table_name}</span></div>\n"
            columns = inspector.get_columns(table_name)
            
            column_info = []
            for col in columns:
                col_type = str(col['type'])
                
                # Apply different colors based on data type
                if 'INT' in col_type.upper():
                    type_class = 'number-type'
                elif 'TEXT' in col_type.upper() or 'CHAR' in col_type.upper() or 'VARCHAR' in col_type.upper():
                    type_class = 'text-type'
                elif 'REAL' in col_type.upper() or 'FLOAT' in col_type.upper() or 'DOUB' in col_type.upper() or 'DECIMAL' in col_type.upper():
                    type_class = 'float-type'
                elif 'DATE' in col_type.upper() or 'TIME' in col_type.upper():
                    type_class = 'date-type'
                else:
                    type_class = 'other-type'
                
                # Add primary key indicator
                pk_class = ' primary-key' if col.get('primary_key', False) else ''
                
                schema_text += f"<div class='column-row{pk_class}'>"
                schema_text += f"<span class='column-name'>{col['name']}</span>"
                schema_text += f"<span class='column-type {type_class}'>({col_type})</span>"
                
                # Add constraints indicators
                constraints = []
                if col.get('primary_key', False):
                    constraints.append("<span class='pk-badge'>PK</span>")
                if not col.get('nullable', True):
                    constraints.append("<span class='nn-badge'>NN</span>")
                
                if constraints:
                    schema_text += f"<span class='constraints'>{''.join(constraints)}</span>"
                
                schema_text += "</div>\n"
                
                column_info.append({
                    "name": col['name'],
                    "type": col_type,
                    "notnull": not col.get('nullable', True),
                    "default_value": str(col.get('default', "")),
                    "is_primary_key": col.get('primary_key', False)
                })
            
            schema_info[table_name] = column_info
            print(f"Processed schema for SQL table: {table_name} ({len(column_info)} columns)")
        
        return schema_text, schema_info
    except Exception as e:
        st.error(f"Error reading SQL schema: {str(e)}")
        return "", {}

def update_schema():
    """Update schema information based on current connection."""
    if st.session_state.db_type == "sqlite":
        st.session_state.schema_text, st.session_state.schema_info = get_sqlite_schema(st.session_state.db_path)
    else:
        # For MySQL/PostgreSQL
        _, engine = get_sql_connection(
            st.session_state.db_type,
            st.session_state.db_host,
            st.session_state.db_port,
            st.session_state.db_name,
            st.session_state.db_user,
            st.session_state.db_password
        )
        if engine:
            st.session_state.schema_text, st.session_state.schema_info = get_sql_schema(engine)

# Execute SQL query with caching
def execute_sql_query(query, use_cache=True, user_question=""):
    """Execute SQL query and return results as a DataFrame."""
    conn = None
    try:
        # Check if we have this query in cache
        cache_key = get_cache_key(query)
        if use_cache and cache_key in st.session_state.query_cache:
            cache_entry = st.session_state.query_cache[cache_key]
            # Check if cache is not too old (30 minutes)
            if time.time() - cache_entry['timestamp'] < 1800:
                print(f"Using cached result for query (cache age: {int(time.time() - cache_entry['timestamp'])}s)")
                
                # Still add to history when using cache
                if not any(item['query'] == query for item in st.session_state.query_history):
                    history_entry = {
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'user_question': user_question,
                        'query': query,
                        'execution_time': cache_entry['execution_time'],
                        'rows_returned': len(cache_entry['data']),
                        'from_cache': True
                    }
                    st.session_state.query_history.append(history_entry)
                
                return cache_entry['data'], None, True
        
        # Not in cache or cache disabled, execute the query
        # Create a new connection for each query execution
        conn = get_database_connection()
        if conn is None:
            return None, "Database connection failed", False
            
        print(f"Executing SQL query: {query}")
        
        start_time = time.time()
        if st.session_state.db_type == "sqlite":
            df = pd.read_sql_query(query, conn)
        else:
            # For SQL Alchemy connections
            df = pd.read_sql_query(sqlalchemy.text(query), conn)
        
        execution_time = time.time() - start_time
        print(f"Query executed successfully in {execution_time:.2f}s, returned {len(df)} rows")
        
        # Add to query history
        history_entry = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_question': user_question,
            'query': query,
            'execution_time': execution_time,
            'rows_returned': len(df),
            'from_cache': False
        }
        st.session_state.query_history.append(history_entry)
        
        # Cache the result
        if use_cache:
            st.session_state.query_cache[cache_key] = {
                'data': df.copy(),
                'timestamp': time.time(),
                'execution_time': execution_time
            }
        
        return df, None, False
    except Exception as e:
        error_msg = f"SQL execution error: {str(e)}"
        print(error_msg)
        
        # Add failed query to history
        history_entry = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_question': user_question,
            'query': query,
            'execution_time': 0,
            'rows_returned': 0,
            'error': str(e),
            'from_cache': False
        }
        st.session_state.query_history.append(history_entry)
        
        return None, error_msg, False
    finally:
        # Always close the connection
        if conn:
            if st.session_state.db_type != "sqlite":
                conn.close()

# Function to display paginated results
def display_paginated_results(df):
    if df is None or df.empty:
        return
    
    # Calculate total pages
    total_rows = len(df)
    rows_per_page = st.session_state.rows_per_page
    total_pages = (total_rows + rows_per_page - 1) // rows_per_page  # Ceiling division
    
    # Ensure current page is valid
    if st.session_state.page_number >= total_pages:
        st.session_state.page_number = 0
    
    # Display pagination controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col1:
        if st.button("◀️ Previous", disabled=(st.session_state.page_number <= 0)):
            st.session_state.page_number -= 1
            st.experimental_rerun()
    
    with col2:
        st.write(f"Page {st.session_state.page_number + 1} of {max(1, total_pages)}")
    
    with col3:
        # Rows per page selector
        new_rows_per_page = st.selectbox(
            "Rows per page:",
            options=[10, 25, 50, 100],
            index=[10, 25, 50, 100].index(st.session_state.rows_per_page)
        )
        if new_rows_per_page != st.session_state.rows_per_page:
            st.session_state.rows_per_page = new_rows_per_page
            st.session_state.page_number = 0  # Reset to first page
            st.experimental_rerun()
    
    with col4:
        if st.button("Next ▶️", disabled=(st.session_state.page_number >= total_pages - 1)):
            st.session_state.page_number += 1
            st.experimental_rerun()
    
    # Display the current page of results
    start_row = st.session_state.page_number * rows_per_page
    end_row = min(start_row + rows_per_page, total_rows)
    
    # Show range information
    st.caption(f"Showing rows {start_row + 1} to {end_row} of {total_rows}")
    
    # Display the paginated dataframe
    st.dataframe(df.iloc[start_row:end_row], use_container_width=True)

# Custom CSS with additions for AI enhancements
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stTextInput>div>div>input {
            background-color: #f0f2f6;
            padding: 12px;
            font-size: 16px;
            color: black;
        }
        .stButton>button {
            background: linear-gradient(135deg, #4c1d95 0%, #6d28d9 100%);
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            box-shadow: 0 3px 10px rgba(76, 29, 149, 0.2);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 29, 149, 0.3);
        }
        .stButton>button:active {
            transform: translateY(0);
        }
        .stSpinner {
            text-align: center;
            color: #8b5cf6;
        }
        .st-emotion-cache-16txtl3 h1 {
            font-weight: 700;
            color: #4c1d95;
        }
        .st-emotion-cache-16txtl3 h3 {
            color: #6d28d9;
            margin-top: 1.5rem;
        }
        .connection-card {
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
        }
        /* Improved schema viewer styling */
        .schema-viewer {
            font-family: 'Courier New', monospace;
            background-color: #1e1e1e;
            color: #ffffff;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #4CAF50;
            overflow: auto;
            max-height: 500px;
            margin-top: 10px;
            line-height: 1.5;
            font-size: 14px;
        }
        .table-header {
            font-weight: bold;
            padding: 8px 0;
            margin-top: 12px;
            margin-bottom: 6px;
            border-bottom: 1px solid #8b5cf6;
            color: #6d28d9;
            font-size: 16px;
        }
        .table-name {
            color: #ff9900;
            font-weight: bold;
        }
        .column-row {
            padding: 3px 0 3px 15px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            border-left: 1px solid #444;
            margin: 2px 0;
        }
        .column-row.primary-key {
            border-left: 2px solid gold;
            background-color: rgba(255, 215, 0, 0.1);
        }
        .column-name {
            color: #ffffff;
            margin-right: 8px;
            font-weight: 500;
        }
        .column-type {
            margin-right: 10px;
            font-style: italic;
            border-radius: 4px;
            padding: 0 5px;
        }
        .number-type {
            color: #42A5F5;  /* blue */
            background-color: rgba(66, 165, 245, 0.1);
        }
        .text-type {
            color: #66BB6A;  /* green */
            background-color: rgba(102, 187, 106, 0.1);
        }
        .float-type {
            color: #FFA726;  /* orange */
            background-color: rgba(255, 167, 38, 0.1);
        }
        .date-type {
            color: #EC407A;  /* pink */
            background-color: rgba(236, 64, 122, 0.1);
        }
        .other-type {
            color: #BDBDBD;  /* grey */
            background-color: rgba(189, 189, 189, 0.1);
        }
        .constraints {
            display: flex;
            gap: 5px;
        }
        .pk-badge {
            background-color: gold;
            color: black;
            font-size: 10px;
            font-weight: bold;
            padding: 1px 4px;
            border-radius: 3px;
        }
        .nn-badge {
            background-color: #ff5252;
            color: white;
            font-size: 10px;
            font-weight: bold;
            padding: 1px 4px;
            border-radius: 3px;
        }
        /* Pagination styles */
        .pagination-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 10px 0;
            gap: 10px;
        }
        .pagination-info {
            font-size: 0.9em;
            color: #666;
        }
        /* Cache indicator */
        .cache-indicator {
            font-size: 0.8em;
            color: #8b5cf6;
            display: flex;
            align-items: center;
            gap: 5px;
            margin-bottom: 10px;
        }
        footer {visibility: hidden;}
        
        /* SQL editor styling */
        .sql-editor {
            font-family: 'Courier New', monospace;
            background-color: #f9f9f9;
            border-left: 4px solid #8b5cf6;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        
        /* Explanation box styling */
        .explanation-box {
            background: linear-gradient(135deg, rgba(76, 29, 149, 0.97) 0%, rgba(124, 58, 237, 0.97) 100%);
            color: #f5f3ff;
            border-left: 4px solid #c4b5fd;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            font-size: 16px;
            line-height: 1.6;
            box-shadow: 0 4px 15px rgba(76, 29, 149, 0.2);
            letter-spacing: 0.3px;
            font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, sans-serif;
        }
        .explanation-box p {
            position: relative;
            padding-left: 1.5em;
            margin-bottom: 12px;
            line-height: 1.8;
        }
        .explanation-box p:before {
            content: "•";
            color: #c4b5fd;
            font-weight: bold;
            position: absolute;
            left: 0.3em;
        }
        .explanation-box strong, 
        .explanation-box b {
            color: #ddd6fe;
            font-weight: 600;
        }
        .explanation-box .ai-badge {
            margin-bottom: 15px;
            display: inline-block;
        }
        
        /* Follow-up questions styling */
        .followup-question {
            background-color: #ddd6fe;
            color: #4c1d95;
            border: 1px solid #c4b5fd;
            border-radius: 25px;
            padding: 10px 18px;
            margin: 6px;
            display: inline-block;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 2px 5px rgba(76, 29, 149, 0.1);
        }
        .followup-question:hover {
            background-color: #c4b5fd;
            box-shadow: 0 4px 8px rgba(76, 29, 149, 0.2);
            transform: translateY(-2px);
        }
        
        /* Improved question suggestion */
        .improved-question {
            background: linear-gradient(135deg, #2e1065 0%, #4c1d95 100%);
            color: #f5f3ff;
            border-left: 6px solid #c4b5fd;
            padding: 18px;
            margin: 15px 0;
            border-radius: 12px;
            font-size: 16px;
            line-height: 1.6;
            box-shadow: 0 4px 15px rgba(76, 29, 149, 0.3);
            transform: translateY(-2px);
            transition: all 0.3s ease;
            letter-spacing: 0.3px;
        }
        
        /* AI badge */
        .ai-badge {
            background-color: #c4b5fd;
            color: #4c1d95;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
            margin-right: 10px;
            display: inline-block;
            box-shadow: 0 2px 5px rgba(76, 29, 149, 0.2);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Query History styling */
        .query-history-container {
            background: rgba(255, 255, 255, 0.8);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(76, 29, 149, 0.1);
            border-top: 3px solid #8b5cf6;
        }
        .download-options {
            display: flex;
            gap: 10px;
            margin: 15px 0;
        }
        /* Clear history button */
        .clear-history-btn {
            background: linear-gradient(135deg, #b91c1c 0%, #ef4444 100%) !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            box-shadow: 0 4px 6px rgba(185, 28, 28, 0.25) !important;
            transition: all 0.3s ease !important;
        }
        .clear-history-btn:hover {
            box-shadow: 0 6px 8px rgba(185, 28, 28, 0.3) !important;
            transform: translateY(-2px) !important;
        }
        /* Override dataframe styling */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
        }
        .stDataFrame div[data-testid="stDataFrameResizable"] {
            background-color: #f9f7ff;
        }
        .stDataFrame th {
            background-color: #6d28d9 !important;
            color: white !important;
            font-weight: 600;
        }
        .stDataFrame tr:nth-child(even) {
            background-color: #f3eeff;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar for database connection
with st.sidebar:
    st.title("🌌 Text-to-SQL AI")
    
    # API Key Management
    st.header("🔑 API Key")
    
    api_key_container = st.container()
    
    with api_key_container:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(76, 29, 149, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%); 
                    padding: 10px; 
                    border-radius: 8px; 
                    border-left: 3px solid #8b5cf6;
                    margin-bottom: 12px;">
            <p style="margin: 0; padding: 0; font-size: 0.85rem; color: #6d28d9;">
                Your API key stays in your browser and is never stored on our servers.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        api_key_input = st.text_input(
            "Enter OpenAI API Key:",
            type="password",
            value=st.session_state.api_key,
            help="This API key is used for all OpenAI operations and is never stored on the server."
        )
        
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input
            os.environ["OPENAI_API_KEY"] = api_key_input
            
            # Clear validation status when key changes
            if 'api_key_valid' in st.session_state:
                del st.session_state.api_key_valid
            
        api_key_status = st.empty()
        
        # Show API key validation
        if 'api_key_valid' not in st.session_state and st.session_state.api_key:
            # We'll validate the API key by making a small request
            try:
                with st.spinner("Validating API key..."):
                    # Make a quick test call to the OpenAI API
                    client = OpenAI(api_key=st.session_state.api_key)
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    st.session_state.api_key_valid = True
            except Exception as e:
                st.session_state.api_key_valid = False
                st.session_state.api_key_error = str(e)
        
        if st.session_state.api_key:
            if st.session_state.get('api_key_valid', False):
                api_key_status.success("✅ API Key valid")
            elif 'api_key_valid' in st.session_state:
                api_key_status.error(f"❌ Invalid API Key: {st.session_state.get('api_key_error', 'Unknown error')}")
            else:
                api_key_status.info("🔄 API Key provided (not validated yet)")
        else:
            api_key_status.error("⚠️ API Key required to use AI features")
    
    st.markdown("---")
    
    st.header("🔌 Database Connection")
    
    # Database type selection
    db_type = st.selectbox(
        "Select Database Type:",
        ["SQLite", "MySQL", "PostgreSQL"],
        index=0,
        key="db_type_select"
    )
    
    # Map UI selection to internal type
    db_type_map = {
        "SQLite": "sqlite",
        "MySQL": "mysql",
        "PostgreSQL": "postgresql"
    }
    
    selected_db_type = db_type_map[db_type]
    
    # Connection form based on database type
    with st.form(key=f"{selected_db_type}_connection_form"):
        st.subheader(f"Connect to {db_type}")
        
        if selected_db_type == "sqlite":
            # SQLite options
            uploaded_file = st.file_uploader("Upload a SQLite database file", type=["db", "sqlite", "sqlite3"])
            db_path_input = st.text_input("Or enter the path to your database:", 
                                          st.session_state.db_path if st.session_state.db_type == "sqlite" else "")
        else:
            # MySQL/PostgreSQL options
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host:", "localhost")
            with col2:
                port = st.text_input("Port:", "3306" if selected_db_type == "mysql" else "5432")
            
            col1, col2 = st.columns(2)
            with col1:
                database = st.text_input("Database Name:")
            with col2:
                username = st.text_input("Username:")
                
            password = st.text_input("Password:", type="password")
        
        connect_btn = st.form_submit_button("Connect to Database")
        
        if connect_btn:
            if selected_db_type == "sqlite":
                # Handle SQLite connection
                if uploaded_file is not None:
                    # Create a temporary file and save the uploaded file to it
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_db_path = tmp_file.name
                    
                    # Test connection
                    conn = get_sqlite_connection(temp_db_path)
                    if conn:
                        st.session_state.db_type = "sqlite"
                        st.session_state.db_path = temp_db_path
                        st.session_state.db_connected = True
                        conn.close()
                        st.success(f"Connected to uploaded database: {uploaded_file.name}")
                        update_schema()
                elif db_path_input and os.path.exists(db_path_input):
                    # Test connection to local file
                    conn = get_sqlite_connection(db_path_input)
                    if conn:
                        st.session_state.db_type = "sqlite"
                        st.session_state.db_path = db_path_input
                        st.session_state.db_connected = True
                        conn.close()
                        st.success(f"Connected to database: {db_path_input}")
                        update_schema()
                else:
                    st.error("Please upload a file or provide a valid path")
            else:
                # Handle MySQL/PostgreSQL connection
                conn, engine = get_sql_connection(
                    selected_db_type,
                    host,
                    port,
                    database,
                    username,
                    password
                )
                
                if conn:
                    st.session_state.db_type = selected_db_type
                    st.session_state.db_host = host
                    st.session_state.db_port = port
                    st.session_state.db_name = database
                    st.session_state.db_user = username
                    st.session_state.db_password = password
                    st.session_state.db_connected = True
                    conn.close()
                    st.success(f"Connected to {db_type} database: {database}")
                    update_schema()
    
    # Disconnect button
    if st.session_state.db_connected:
        if st.button("Disconnect Database"):
            st.session_state.db_connected = False
            if st.session_state.db_type != "sqlite" and st.session_state.db_type != "":
                for attr in ['db_host', 'db_port', 'db_name', 'db_user', 'db_password']:
                    if attr in st.session_state:
                        del st.session_state[attr]
            st.session_state.schema_info = {}
            st.session_state.schema_text = ""
            st.success("Database disconnected")
    
    # Display current connection status
    st.markdown("### Connection Status")
    if st.session_state.db_connected:
        if st.session_state.db_type == "sqlite":
            st.success(f"✅ Connected to SQLite: {os.path.basename(st.session_state.db_path)}")
        else:
            st.success(f"✅ Connected to {st.session_state.db_type.upper()}: {st.session_state.db_name}")
    else:
        st.error("❌ Not connected to any database")
    
    # Schema viewer in sidebar with improved styling
    if st.session_state.db_connected and st.session_state.schema_text:
        st.markdown("### Database Schema")
        st.markdown(f'<div class="schema-viewer">{st.session_state.schema_text}</div>', unsafe_allow_html=True)

# Main application UI
st.title("🤖 Ask Your Data – Natural Language to SQL")

st.markdown("Enter a natural language question below and let AI translate it into an SQL query. The system will automatically run the query and show your data!")

# Check connection status
if not st.session_state.db_connected:
    st.warning("⚠️ Please connect to a database using the sidebar options first")

# Check if API key is provided and valid
has_valid_api_key = st.session_state.get('api_key_valid', False)
if not has_valid_api_key and not st.session_state.api_key:
    st.error("⚠️ Please enter your OpenAI API key in the sidebar to use AI features")
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(76, 29, 149, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%); 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;">
        <h4 style="margin-top: 0; color: #6d28d9;">How to get an OpenAI API key:</h4>
        <ol style="margin-bottom: 0;">
            <li>Go to <a href="https://platform.openai.com/signup" target="_blank">OpenAI Platform</a> and sign up or log in</li>
            <li>Navigate to the API Keys section in your account</li>
            <li>Create a new secret key</li>
            <li>Copy and paste it into the sidebar field</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# Main query area
col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input("🔍 What do you want to know? (e.g., 'Show me all customers' or 'Total order amounts by customer')")

# Add cache control
with col2:
    run_disabled = not st.session_state.db_connected
    use_cache = st.checkbox("Use query cache", value=True, help="Enable to use cached results for faster performance")
    run = st.button("🚀 Generate & Run SQL", disabled=run_disabled)

# Question improvement suggestion (if available)
if st.session_state.improved_question and st.session_state.improved_question != user_input:
    st.markdown(f"""<div class="improved-question">
        <span class="ai-badge">AI Suggestion</span>
        Try this improved question: "{st.session_state.improved_question}"
        </div>""", unsafe_allow_html=True)
    
    if st.button("Use Suggested Question"):
        user_input = st.session_state.improved_question
        st.session_state.user_input = st.session_state.improved_question
        st.experimental_rerun()

if run:
    if not user_input:
        st.warning("⚠️ Please enter a question first")
    elif not st.session_state.api_key:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar to use AI features")
    elif not st.session_state.get('api_key_valid', False) and 'api_key_valid' in st.session_state:
        st.error("❌ The provided API key is invalid. Please check and update your API key.")
    else:
        # Check connection
        if not st.session_state.db_connected:
            st.error("⚠️ Please connect to a database first")
        else:
            # Check if we have schema info
            if not st.session_state.schema_info:
                with st.spinner("🔄 Reading database schema..."):
                    update_schema()
            
            # Generate question improvement suggestion
            with st.spinner("🔄 Analyzing your question..."):
                improved_question = suggest_question_improvements(
                    user_input, 
                    st.session_state.schema_info,
                    api_key=st.session_state.api_key
                )
                if improved_question and improved_question != user_input:
                    st.session_state.improved_question = improved_question
            
            with st.spinner("💡 Generating SQL using AI..."):
                try:
                    # Generate SQL query using GPT
                    generated_sql = gpt_generate_sql(
                        user_input, 
                        st.session_state.schema_info,
                        api_key=st.session_state.api_key
                    )
                    st.session_state.current_sql = generated_sql
                    
                    # SQL editing option
                    st.markdown("### 🧾 Generated SQL")
                    st.markdown('<span class="ai-badge">AI Generated</span> You can edit this SQL before execution:', unsafe_allow_html=True)
                    
                    # Allow user to edit the SQL
                    edited_sql = st.text_area("Edit SQL Query:", value=generated_sql, height=150, key="sql_editor")
                    
                    # Check if SQL was edited
                    sql_to_execute = edited_sql
                    st.session_state.sql_edited = (edited_sql != generated_sql)
                    
                    # Display SQL explanation in plain English
                    with st.spinner("🔄 Generating explanation..."):
                        explanation = explain_query(
                            sql_to_execute, 
                            st.session_state.schema_info,
                            api_key=st.session_state.api_key
                        )
                        st.session_state.current_explanation = explanation
                        
                        # Clean the explanation - remove any unwanted HTML tags
                        explanation = explanation.replace("</div>", "")
                        
                        # Convert explanation text to bullet points
                        explanation_lines = explanation.split("\n")
                        bullet_explanation = ""
                        
                        for line in explanation_lines:
                            line = line.strip()
                            if line:
                                # Remove existing bullet points or numbers if present
                                if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                                    # Extract the content after the bullet point or number
                                    parts = line.split(' ', 1)
                                    if len(parts) > 1:
                                        line = parts[1].strip()
                                
                                # Wrap each bullet point in a paragraph
                                bullet_explanation += f"<p>{line}</p>\n"
                        
                        st.markdown("### 📖 Query Explanation")
                        formatted_explanation = f"""
                        <div class="explanation-box">
                            <span class="ai-badge">SQL Explained</span>
                            {bullet_explanation}
                        </div>
                        """
                        st.markdown(formatted_explanation, unsafe_allow_html=True)
                    
                    # Execute button for the possibly edited SQL
                    execute_query = st.button("▶️ Execute SQL")
                    
                    if execute_query:
                        try:
                            # Execute the SQL query with caching
                            with st.spinner("⚙️ Executing SQL query..."):
                                df, error, from_cache = execute_sql_query(sql_to_execute, use_cache=use_cache, user_question=user_input)
                            
                            if error:
                                st.error("❌ SQL Execution Error")
                                with st.expander("See error details"):
                                    st.markdown(f'<div class="error-box">{error}</div>', unsafe_allow_html=True)
                            else:
                                # Show cache indicator if result was from cache
                                if from_cache:
                                    st.markdown(f"""<div class="cache-indicator">
                                        <span>⚡ Results loaded from cache</span>
                                        <span>(Query execution time: {st.session_state.query_cache[get_cache_key(sql_to_execute)]['execution_time']:.2f}s)</span>
                                    </div>""", unsafe_allow_html=True)
                                
                                # Display a message about query history
                                st.success(f"✅ Query executed and added to history. View query history below.")
                                
                                st.markdown("### 📊 Query Results")
                                
                                # Display results with pagination if more than 10 rows
                                if len(df) > 10:
                                    display_paginated_results(df)
                                else:
                                    st.dataframe(df, use_container_width=True)

                                # Generate visualization if we have numeric columns
                                if not df.empty and df.select_dtypes(include='number').shape[1] > 0:
                                    st.markdown("### 📈 Visualization")
                                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                                    
                                    if len(df.columns) > 1 and len(numeric_cols) > 0:
                                        # Try to find a text column for x-axis
                                        text_cols = df.select_dtypes(exclude=['number']).columns.tolist()
                                        if text_cols:
                                            # Allow selecting columns for visualization
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                selected_x = st.selectbox("Select X-axis column:", text_cols, index=0)
                                            with col2:
                                                selected_y = st.selectbox("Select Y-axis column:", numeric_cols, index=0)
                                            
                                            st.bar_chart(df.set_index(selected_x)[selected_y])
                                        else:
                                            st.bar_chart(df)
                                    
                                    # Add export options
                                    st.markdown("### 📤 Export Data")
                                    col1, col2, col3 = st.columns(3)
                                    
                                    # CSV Export
                                    with col1:
                                        csv = df.to_csv(index=False)
                                        st.download_button(
                                            label="📥 Download as CSV",
                                            data=csv,
                                            file_name="query_results.csv",
                                            mime="text/csv",
                                        )
                                    
                                    # Excel Export
                                    with col2:
                                        buffer = pd.ExcelWriter('query_results.xlsx', engine='xlsxwriter')
                                        df.to_excel(buffer, index=False, sheet_name='Results')
                                        buffer.close()
                                        
                                        with open('query_results.xlsx', 'rb') as f:
                                            excel_data = f.read()
                                        
                                        st.download_button(
                                            label="📊 Download as Excel",
                                            data=excel_data,
                                            file_name="query_results.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        )
                                    
                                    # JSON Export
                                    with col3:
                                        json_str = df.to_json(orient='records')
                                        st.download_button(
                                            label="📋 Download as JSON",
                                            data=json_str,
                                            file_name="query_results.json",
                                            mime="application/json",
                                        )
                                
                                # Generate follow-up questions after seeing the results
                                with st.spinner("🔄 Generating follow-up questions..."):
                                    follow_up_questions = generate_followup_questions(
                                        user_input,
                                        sql_to_execute,
                                        st.session_state.schema_info,
                                        api_key=st.session_state.api_key
                                    )
                                    st.session_state.follow_up_questions = follow_up_questions
                                
                                if follow_up_questions:
                                    st.markdown("### 🔍 Follow-up Questions")
                                    st.markdown("<span class='ai-badge'>AI Suggested</span> You might also want to ask:", unsafe_allow_html=True)
                                    
                                    # Create buttons for each follow-up question
                                    for q in follow_up_questions:
                                        if st.button(q, key=f"followup_{q}"):
                                            st.session_state.user_input = q
                                            st.experimental_rerun()

                        except Exception as e:
                            st.error("❌ SQL Execution Error")
                            with st.expander("See error details"):
                                st.markdown(f'<div class="error-box">{str(e)}</div>', unsafe_allow_html=True)
                                st.code(traceback.format_exc(), language="python")
                
                except Exception as e:
                    st.error("❌ Error Generating SQL")
                    with st.expander("See error details"):
                        st.markdown(f'<div class="error-box">{str(e)}</div>', unsafe_allow_html=True)
                        st.code(traceback.format_exc(), language="python")

# Display Query History Report Section if there are queries in history
if 'query_history' in st.session_state and len(st.session_state.query_history) > 0:
    # Display query history section
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4c1d95 0%, #6d28d9 100%); 
                padding: 15px; 
                border-radius: 10px; 
                color: white; 
                margin: 20px 0; 
                text-align: center;
                box-shadow: 0 4px 15px rgba(76, 29, 149, 0.2);">
        <h2 style="margin: 0; padding: 0; color: white;">📜 Query History Report</h2>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Track and export your SQL query history</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a DataFrame from the query history
    history_df = pd.DataFrame(st.session_state.query_history)
    
    # Format the DataFrame for display
    display_df = history_df.copy()
    if not display_df.empty:
        # Limit query length for display
        if 'query' in display_df.columns:
            display_df['query'] = display_df['query'].apply(lambda x: (x[:75] + '...') if len(x) > 75 else x)
        
        # Format execution time
        if 'execution_time' in display_df.columns:
            display_df['execution_time'] = display_df['execution_time'].apply(lambda x: f"{x:.3f}s")
        
        # Add a cached indicator
        if 'from_cache' in display_df.columns:
            display_df['cached'] = display_df['from_cache'].apply(lambda x: '✅' if x else '❌')
            
        # Reorder and rename columns for better display
        cols_order = ['timestamp', 'user_question', 'query', 'rows_returned', 'execution_time', 'cached']
        cols_rename = {
            'user_question': 'Question',
            'timestamp': 'Time',
            'query': 'SQL Query',
            'rows_returned': 'Rows',
            'execution_time': 'Duration',
            'cached': 'Cached'
        }
        
        display_cols = [col for col in cols_order if col in display_df.columns]
        rename_cols = {k: v for k, v in cols_rename.items() if k in display_df.columns}
        
        display_df = display_df[display_cols].rename(columns=rename_cols)
    
    # Display the history table
    st.markdown('<div class="query-history-container">', unsafe_allow_html=True)
    st.dataframe(display_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Download options
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4c1d95 0%, #6d28d9 100%); 
                padding: 15px; 
                border-radius: 10px; 
                margin: 15px 0; 
                color: white;
                box-shadow: 0 4px 15px rgba(76, 29, 149, 0.2);">
        <h3 style="color: white; margin-top: 0; text-align: center;">📤 Download Query History</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # More prominent download buttons
    download_col1, download_col2, download_col3 = st.columns(3)
    
    # CSV Download
    with download_col1:
        csv = history_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="query_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
    
    # Excel Download
    with download_col2:
        buffer = pd.ExcelWriter('query_history.xlsx', engine='xlsxwriter')
        history_df.to_excel(buffer, index=False, sheet_name='Query History')
        buffer.close()
        
        with open('query_history.xlsx', 'rb') as f:
            excel_data = f.read()
        
        st.download_button(
            label="📊 Download as Excel",
            data=excel_data,
            file_name="query_history.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    
    # JSON Download
    with download_col3:
        json_str = history_df.to_json(orient='records')
        st.download_button(
            label="📋 Download as JSON",
            data=json_str,
            file_name="query_history.json",
            mime="application/json",
            use_container_width=True,
        )
    
    # Clear history button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🗑️ Clear Query History", key="clear_history_btn", use_container_width=True):
            st.session_state.query_history = []
            st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("<center><small>Built with ❤️ by Patrick Scott</small></center>", unsafe_allow_html=True) 