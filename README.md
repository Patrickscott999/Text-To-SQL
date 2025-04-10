# Text-to-SQL AI Converter

A powerful Streamlit application that converts natural language questions into SQL queries using OpenAI's API and executes them on various database types with a beautiful user interface.

![Text-to-SQL Demo](https://example.com/demo.gif)

## Features

- **Natural Language Processing**: Converts plain English to SQL using OpenAI's GPT models
- **Multi-Database Support**: 
  - SQLite (via file upload or path)
  - MySQL
  - PostgreSQL
- **Smart Schema Visualization**: 
  - Color-coded data types (INTEGER: Blue, TEXT: Green, REAL: Orange, DATE: Pink)
  - Primary key and constraint indicators
  - Intuitive formatting with proper spacing
- **Query Enhancement**:
  - AI-powered query explanation in plain English
  - Question improvement suggestions
  - Auto-generated follow-up questions based on results
  - SQL editing capability before execution
- **Performance Optimization**:
  - Query caching system to avoid redundant database queries
  - Pagination for large result sets
- **Result Management**:
  - Export options (CSV, Excel, JSON)
  - Data visualization for numeric results
- **Query History**:
  - Track all executed queries
  - Download query history in multiple formats
  - Filter and clear history as needed
- **Modern UI**:
  - Galaxy purple theme with modern styling
  - Responsive design with clear visual hierarchy
  - Enhanced readability with optimal contrast

## Setup

1. Clone this repository:
```bash
git clone https://github.com/Patrickscott999/Text-To-SQL.git
cd Text-To-SQL
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key as an environment variable:
```bash
# On macOS/Linux
export OPENAI_API_KEY=your_api_key_here

# On Windows (Command Prompt)
set OPENAI_API_KEY=your_api_key_here

# On Windows (PowerShell)
$env:OPENAI_API_KEY = "your_api_key_here"
```

## Running the Application

```bash
streamlit run simple_app.py
```

## Usage

1. **Connect to a database**:
   - Upload a SQLite database, or
   - Enter path to a local SQLite database, or
   - Connect to a MySQL/PostgreSQL database

2. **Enter your question** in natural language

3. **Generate & Run SQL**: The app will:
   - Convert your question to SQL
   - Display an explanation of what the query does
   - Execute the query and show results
   - Generate visualizations when possible
   - Suggest follow-up questions

4. **Review Query History**:
   - View all past queries at the bottom of the app
   - Download history in CSV, Excel, or JSON format

## Sample Database

The repository includes a sample retail database (`sample_retail.db`) with tables for:
- customers
- products
- orders
- order_items
- suppliers

## Example Questions

You can ask questions such as:
- "Show me all customers"
- "What is the total amount spent by each customer?"
- "Find products with less than 10 items in stock"
- "Which supplier provides the most products?"
- "Show the most recent orders with customer details"

## Project Structure

- `simple_app.py`: Main Streamlit application with enhanced UI and features
- `app.py`: Alternative simplified version of the application
- `llm_sql.py`: Module for interacting with OpenAI API
- `create_sample_db.py`: Script to regenerate the sample database
- `requirements.txt`: Dependencies
- `sample_retail.db`: Sample SQLite database for testing

## Troubleshooting

- **OpenAI API key issues**: Verify it's set correctly in your environment
- **Database connection problems**: Check that your database is accessible and credentials are correct
- **SQL execution errors**: Review the detailed error information provided in the app

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 