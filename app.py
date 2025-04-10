import os
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
from llm_sql import gpt_generate_sql
import traceback
import tempfile
import mysql.connector
import sqlalchemy

# Page configuration
st.set_page_config(
    page_title="Natural Language to SQL",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        text-align: center;
        color: #0F9D58;
        font-size: 42px;
        margin-bottom: 30px;
        font-weight: 600;
        padding: 20px 0;
        border-bottom: 2px solid #f0f0f0;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #0F9D58;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.7em 1.2em;
        width: 100%;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0b8048;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Input field styling */
    .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 15px;
        background-color: #f9f9f9;
        font-size: 16px;
    }
    
    /* Generic text styling */
    .standard-text {
        font-size: 16px;
        line-height: 1.6;
        color: #333333;
    }
    
    /* Section headings */
    .section-header {
        color: #0F9D58;
        font-size: 24px;
        font-weight: 600;
        margin: 20px 0 10px 0;
        padding-bottom: 5px;
    }
    
    /* Code block styling */
    .sql-code {
        background-color: #f5f5f5;
        border-left: 5px solid #0F9D58;
        border-radius: 5px;
        padding: 15px;
        font-family: 'Courier New', monospace;
        overflow-x: auto;
    }
    
    /* Error box styling */
    .error-box {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    
    /* Success box styling */
    .success-box {
        background-color: #e8f5e9;
        border-left: 5px solid #0F9D58;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    
    /* Info box styling */
    .info-box {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    
    /* Card styling for database connection */
    .db-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Footer styling */
    footer {
        text-align: center;
        padding: 20px;
        font-style: italic;
        color: #666;
        border-top: 1px solid #eee;
        margin-top: 40px;
    }
    
    /* Results container */
    .results-container {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    /* Data visualization container */
    .viz-container {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Database connection function for SQLite
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

# Database connection function for MySQL and other SQL servers
def get_sql_connection(db_type, host, port, database, username, password):
    """Connect to various SQL databases using SQLAlchemy."""
    try:
        if db_type == "mysql":
            connection_string = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "postgresql":
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "mssql":
            connection_string = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            st.error(f"Unsupported database type: {db_type}")
            return None
            
        engine = sqlalchemy.create_engine(connection_string)
        conn = engine.connect()
        print(f"{db_type.upper()} connection successful to {host}:{port}/{database}")
        return conn
    except Exception as e:
        st.error(f"Error connecting to {db_type.upper()} database: {str(e)}")
        return None

# Function to get database connection based on connection info stored in session state
def get_database_connection():
    """Get database connection based on connection type in session state."""
    try:
        if 'db_connected' not in st.session_state or not st.session_state.db_connected:
            st.error("No database connected. Please connect to a database first.")
            return None
            
        if st.session_state.db_type == "sqlite":
            return get_sqlite_connection(st.session_state.db_path)
        else:
            return get_sql_connection(
                st.session_state.db_type,
                st.session_state.db_host,
                st.session_state.db_port,
                st.session_state.db_name,
                st.session_state.db_user,
                st.session_state.db_password
            )
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        return None

# Schema retrieval for SQLite
def get_sqlite_schema(db_path):
    """Extract schema information from an SQLite database."""
    try:
        if not db_path:
            return {}
            
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database")
            return {}
            
        print(f"Found {len(tables)} tables in the database")
        
        schema_info = {}
        for table in tables:
            table_name = table[0]
            # Get column information using PRAGMA
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Format column info
            column_info = []
            for col in columns:
                column_info.append({
                    "name": col[1],
                    "type": col[2],
                    "notnull": col[3],
                    "default_value": col[4],
                    "is_primary_key": col[5]
                })
            
            schema_info[table_name] = column_info
            print(f"Processed schema for SQLite table: {table_name} ({len(column_info)} columns)")
        
        # Close the connection after reading schema
        conn.close()
        
        return schema_info
    except Exception as e:
        st.error(f"Error reading SQLite schema: {str(e)}")
        return {}

# Schema retrieval for MySQL and other SQL servers
def get_sql_schema(db_type, conn):
    """Extract schema information from a SQL database using SQLAlchemy."""
    try:
        if conn is None:
            return {}
            
        schema_info = {}
        
        # Get metadata
        metadata = sqlalchemy.MetaData()
        metadata.reflect(bind=conn.engine)
        
        for table_name, table in metadata.tables.items():
            column_info = []
            for column in table.columns:
                column_info.append({
                    "name": column.name,
                    "type": str(column.type),
                    "notnull": not column.nullable,
                    "default_value": str(column.default) if column.default else None,
                    "is_primary_key": column.primary_key
                })
            
            schema_info[table_name] = column_info
            print(f"Processed schema for {db_type.upper()} table: {table_name} ({len(column_info)} columns)")
        
        return schema_info
    except Exception as e:
        st.error(f"Error reading {db_type.upper()} schema: {str(e)}")
        return {}

# Cache the schema information
@st.cache_data
def get_table_schema():
    """Extract schema information from the connected database."""
    try:
        if 'db_connected' not in st.session_state or not st.session_state.db_connected:
            return {}
            
        if st.session_state.db_type == "sqlite":
            return get_sqlite_schema(st.session_state.db_path)
        else:
            conn = get_sql_connection(
                st.session_state.db_type,
                st.session_state.db_host,
                st.session_state.db_port,
                st.session_state.db_name,
                st.session_state.db_user,
                st.session_state.db_password
            )
            schema = get_sql_schema(st.session_state.db_type, conn)
            if conn:
                conn.close()
            return schema
    except Exception as e:
        st.error(f"Error reading schema: {str(e)}")
        return {}

def execute_sql_query(query):
    """Execute SQL query and return results as a DataFrame."""
    conn = None
    try:
        # Create a new connection for each query execution
        conn = get_database_connection()
        if conn is None:
            return None, "Database connection failed"
            
        print(f"Executing SQL query: {query}")
        
        if st.session_state.db_type == "sqlite":
            df = pd.read_sql_query(query, conn)
        else:
            df = pd.read_sql_query(sqlalchemy.text(query), conn)
            
        print(f"Query executed successfully, returned {len(df)} rows")
        return df, None
    except Exception as e:
        error_msg = f"SQL execution error: {str(e)}"
        print(error_msg)
        return None, error_msg
    finally:
        # Always close the connection
        if conn:
            if st.session_state.db_type != "sqlite":
                conn.close()

# Sidebar configuration
with st.sidebar:
    st.image("https://raw.githubusercontent.com/streamlit/streamlit/develop/examples/data/logo.png", width=100)
    st.markdown("<h2 style='color:#0F9D58;'>Natural Language to SQL</h2>", unsafe_allow_html=True)
    
    st.markdown("### Example Questions")
    example_questions = [
        "Show me all customers",
        "List all orders with customer names",
        "What is the total amount spent by each customer?",
        "Find customers who are older than 30",
        "Show the most expensive order"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"btn_{question}"):
            st.session_state.user_input = question
    
    st.markdown("### Tips")
    st.info("""
    - Be specific with column names if you know them
    - Mention the table name if querying a specific table
    - For complex queries, break them down into simpler parts
    - Try to use proper English syntax for your questions
    - Using "show", "find", or "list" helps in query generation
    """)
    
    # Display API key status
    st.markdown("### API Status")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        st.warning("⚠️ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    else:
        st.success("✅ OpenAI API key found")

# Main application UI
st.markdown('<h1 class="main-title">Natural Language to SQL Converter</h1>', unsafe_allow_html=True)

# Database connection section
st.markdown('<div class="db-card">', unsafe_allow_html=True)
st.markdown('<h3 class="section-header">Connect to a Database</h3>', unsafe_allow_html=True)

# Initialize session state for database connection
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
    
if 'db_type' not in st.session_state:
    st.session_state.db_type = "sqlite"
    
if 'db_path' not in st.session_state:
    st.session_state.db_path = ""
    
# Database type selection
db_type = st.selectbox(
    "Select Database Type:",
    ["SQLite", "MySQL", "PostgreSQL", "Microsoft SQL Server"],
    index=0,
    key="db_type_select"
)

# Map UI selection to internal type
db_type_map = {
    "SQLite": "sqlite",
    "MySQL": "mysql",
    "PostgreSQL": "postgresql",
    "Microsoft SQL Server": "mssql"
}

selected_db_type = db_type_map[db_type]

# SQLite connection options
if selected_db_type == "sqlite":
    st.markdown("#### Connect to SQLite Database")
    
    # Option to upload a database file
    uploaded_file = st.file_uploader("Upload a SQLite database file", type=["db", "sqlite", "sqlite3"])
    
    if uploaded_file is not None:
        # Create a temporary file and save the uploaded file to it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        st.markdown(f'<div class="success-box">Database uploaded successfully: {uploaded_file.name}</div>', unsafe_allow_html=True)
        
        # Set session state values
        st.session_state.db_type = "sqlite"
        st.session_state.db_path = tmp_path
        st.session_state.db_connected = True
        
    # Direct path input option
    col1, col2 = st.columns([3, 1])
    with col1:
        db_path_input = st.text_input("Or enter the path to your database:", st.session_state.db_path if st.session_state.db_type == "sqlite" else "")
    with col2:
        if st.button("Connect", key="sqlite_connect_btn"):
            if os.path.exists(db_path_input):
                # Set session state values
                st.session_state.db_type = "sqlite"
                st.session_state.db_path = db_path_input
                st.session_state.db_connected = True
                
                st.markdown(f'<div class="success-box">Connected to SQLite database: {db_path_input}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">Database file not found: {db_path_input}</div>', unsafe_allow_html=True)

# SQL Server connection options (MySQL, PostgreSQL, MSSQL)
else:
    st.markdown(f"#### Connect to {db_type}")
    
    col1, col2 = st.columns(2)
    with col1:
        host = st.text_input("Host:", "localhost", key=f"{selected_db_type}_host")
    with col2:
        port = st.text_input("Port:", 
                             "3306" if selected_db_type == "mysql" else 
                             "5432" if selected_db_type == "postgresql" else 
                             "1433", 
                             key=f"{selected_db_type}_port")
    
    col1, col2 = st.columns(2)
    with col1:
        database = st.text_input("Database Name:", key=f"{selected_db_type}_db")
    with col2:
        username = st.text_input("Username:", key=f"{selected_db_type}_user")
    
    password = st.text_input("Password:", type="password", key=f"{selected_db_type}_password")
    
    if st.button("Connect", key=f"{selected_db_type}_connect_btn"):
        try:
            # Attempt connection
            conn = get_sql_connection(
                selected_db_type,
                host,
                port,
                database,
                username,
                password
            )
            
            if conn:
                # Set session state values
                st.session_state.db_type = selected_db_type
                st.session_state.db_host = host
                st.session_state.db_port = port
                st.session_state.db_name = database
                st.session_state.db_user = username
                st.session_state.db_password = password
                st.session_state.db_connected = True
                
                conn.close()
                st.markdown(f'<div class="success-box">Connected to {db_type} database: {database} on {host}:{port}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">Failed to connect to {db_type} database. Please check your credentials.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="error-box">Error connecting to {db_type} database: {str(e)}</div>', unsafe_allow_html=True)

# Display database connection status
if st.session_state.db_connected:
    if st.session_state.db_type == "sqlite":
        st.markdown(f'<div class="info-box">Current database: {os.path.basename(st.session_state.db_path)} (SQLite)</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="info-box">Current database: {st.session_state.db_name} on {st.session_state.db_host}:{st.session_state.db_port} ({db_type})</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="error-box">No database connected. Please connect to a database using the options above.</div>', unsafe_allow_html=True)

# Button to disconnect
if st.session_state.db_connected and st.button("Disconnect Database", key="disconnect_btn"):
    st.session_state.db_connected = False
    st.session_state.db_type = "sqlite"
    st.session_state.db_path = ""
    if hasattr(st.session_state, 'db_host'):
        delattr(st.session_state, 'db_host')
    if hasattr(st.session_state, 'db_port'):
        delattr(st.session_state, 'db_port')
    if hasattr(st.session_state, 'db_name'):
        delattr(st.session_state, 'db_name')
    if hasattr(st.session_state, 'db_user'):
        delattr(st.session_state, 'db_user')
    if hasattr(st.session_state, 'db_password'):
        delattr(st.session_state, 'db_password')
    st.markdown('<div class="info-box">Database disconnected.</div>', unsafe_allow_html=True)
    st.cache_data.clear()

st.markdown('</div>', unsafe_allow_html=True)

# Main query area
st.markdown('<div class="db-card">', unsafe_allow_html=True)
st.markdown('<h3 class="section-header">Ask Your Question</h3>', unsafe_allow_html=True)

# Main area
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

user_input = st.text_area(
    "Enter your question in natural language:", 
    value=st.session_state.user_input,
    height=100,
    key="input_area",
    placeholder="e.g., 'Show me all customers who spent more than $50'"
)

col1, col2 = st.columns([4, 1])
with col2:
    generate_btn = st.button("Generate SQL & Execute", key="generate_btn", use_container_width=True)

# Get schema information
schema_info = get_table_schema() if st.session_state.db_connected else {}

# Display the schema in an expandable section
with st.expander("Database Schema", expanded=False):
    if not schema_info:
        st.warning("No schema information found or database is empty.")
    else:
        for table_name, columns in schema_info.items():
            st.markdown(f"**Table: {table_name}**")
            cols_info = [(col['name'], col['type']) for col in columns]
            st.table(pd.DataFrame(cols_info, columns=["Column", "Type"]))

st.markdown('</div>', unsafe_allow_html=True)

# Process the query
if generate_btn:
    if not st.session_state.db_connected:
        st.error("Please connect to a database first.")
    elif user_input:
        st.markdown('<div class="results-container">', unsafe_allow_html=True)
        with st.spinner("Generating SQL query..."):
            try:
                # Generate SQL query using GPT
                generated_sql = gpt_generate_sql(user_input, schema_info)
                
                # Display the generated SQL with syntax highlighting
                st.markdown('<h3 class="section-header">Generated SQL Query</h3>', unsafe_allow_html=True)
                st.markdown(f'<div class="sql-code">{generated_sql}</div>', unsafe_allow_html=True)
                st.code(generated_sql, language="sql")
                
                # Execute the SQL query
                with st.spinner("Executing query..."):
                    results, error = execute_sql_query(generated_sql)
                    
                if error:
                    st.error("Error executing SQL query")
                    with st.expander("View Error Details", expanded=True):
                        st.markdown(f'<div class="error-box">{error}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<h3 class="section-header">Query Results</h3>', unsafe_allow_html=True)
                    st.dataframe(results, use_container_width=True)
                    
                    # Check if we can create a visualization
                    if results is not None and not results.empty and results.select_dtypes(include=['number']).columns.any():
                        numeric_cols = results.select_dtypes(include=['number']).columns.tolist()
                        
                        if len(results.columns) > 1 and len(numeric_cols) > 0:
                            # Try to find a text column for x-axis
                            text_cols = results.select_dtypes(exclude=['number']).columns.tolist()
                            if text_cols:
                                st.markdown('<div class="viz-container">', unsafe_allow_html=True)
                                st.markdown('<h3 class="section-header">Visualization</h3>', unsafe_allow_html=True)
                                x_axis = text_cols[0]
                                
                                # Create a selectbox for the y-axis
                                y_axis = st.selectbox("Select column for visualization:", numeric_cols)
                                
                                # Create a bar chart
                                fig = px.bar(results, x=x_axis, y=y_axis, title=f"{y_axis} by {x_axis}")
                                fig.update_layout(
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    font=dict(color='#333333'),
                                    title_font=dict(size=20, color='#0F9D58'),
                                    xaxis=dict(showgrid=False),
                                    yaxis=dict(showgrid=True, gridcolor='#eee')
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                st.markdown('</div>', unsafe_allow_html=True)
            
            except Exception as e:
                st.error("An error occurred during processing")
                with st.expander("View Error Details", expanded=True):
                    st.markdown(f'<div class="error-box">{str(e)}</div>', unsafe_allow_html=True)
                    st.code(traceback.format_exc(), language="python")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please enter a question first")

# Footer
st.markdown('<footer>Built by Patrick Scott | Data Analyst</footer>', unsafe_allow_html=True) 