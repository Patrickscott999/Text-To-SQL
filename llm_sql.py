import os
import json
import logging
from openai import OpenAI
import re

def gpt_generate_sql(user_input, schema_info):
    """
    Generate SQL query from natural language using OpenAI's GPT.
    
    Args:
        user_input (str): The user's natural language query
        schema_info (dict or str): Dictionary containing database schema information or string with formatted schema
    
    Returns:
        str: Generated SQL query
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    # Format schema information for the prompt if it's a dictionary
    if isinstance(schema_info, dict):
        schema_description = format_schema_for_prompt(schema_info)
    else:
        # Use the schema string directly if provided
        schema_description = schema_info
    
    # Create client with detailed logging
    try:
        client = OpenAI(api_key=api_key)
        
        # Log schema information
        if isinstance(schema_info, dict):
            print(f"Schema information processed: {len(schema_info)} tables found")
        else:
            print("Using provided schema string")
        
        # Construct the system message with schema information
        system_message = f"""You are an expert SQL query generator. 
Your task is to convert natural language questions into valid SQLite SQL queries.
Use the following database schema:

{schema_description}

Important rules:
1. Generate ONLY the SQL query, nothing else - no explanations or comments
2. Make sure the query is compatible with SQLite syntax
3. Use appropriate joins when needed based on the schema
4. Limit results to a reasonable number (e.g., 100) for large tables unless specified otherwise
5. Use column aliases for clarity when needed
6. Use proper SQL formatting but keep it concise
7. Make sure to handle NULL values appropriately
8. For aggregations, always include GROUP BY clauses as needed
9. If using ORDER BY, make sure to include columns in SELECT
10. Add indexes to JOIN columns and WHERE predicates for performance
"""

        # Log the user input
        print(f"Processing user input: '{user_input}'")
        
        # Make the API call to OpenAI
        try:
            print("Making API call to OpenAI...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use GPT-3.5 Turbo - widely available model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,  # Low temperature for more deterministic outputs
                max_tokens=500
            )
            
            print("API call successful, extracting SQL query...")
            # Extract the SQL query from the response
            sql_query = response.choices[0].message.content.strip()
            print(f"Generated SQL query: {sql_query}")
            return sql_query
        
        except Exception as api_error:
            error_msg = f"OpenAI API error: {str(api_error)}"
            print(error_msg)
            raise Exception(error_msg)
    
    except Exception as client_error:
        error_msg = f"Error creating OpenAI client: {str(client_error)}"
        print(error_msg)
        raise Exception(error_msg)

def explain_query(sql_query, schema_info):
    """
    Generate a plain English explanation of what the SQL query does.
    
    Args:
        sql_query (str): The SQL query to explain
        schema_info (dict or str): Database schema information
        
    Returns:
        str: Plain English explanation of the query
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    # Format schema information for context
    if isinstance(schema_info, dict):
        schema_description = format_schema_for_prompt(schema_info)
    else:
        schema_description = schema_info
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Construct prompt for explanation
        prompt = f"""Given the following SQL query and database schema, explain in simple terms what this query does.
Use plain English, as if explaining to someone without technical knowledge. Keep the explanation concise but comprehensive.

Database Schema:
{schema_description}

SQL Query:
{sql_query}

Please provide:
1. A simple one-sentence summary of what this query does
2. A brief explanation of the data being retrieved or manipulated
3. The meaning of any calculations or aggregations
4. How the results are being filtered or sorted, if applicable
"""
        
        print("Generating SQL explanation...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=250
        )
        
        explanation = response.choices[0].message.content.strip()
        return explanation
    
    except Exception as e:
        print(f"Error generating explanation: {str(e)}")
        return "Unable to generate explanation at this time."

def suggest_question_improvements(user_question, schema_info):
    """
    Suggest improvements to the user's natural language question.
    
    Args:
        user_question (str): The user's original question
        schema_info (dict or str): Database schema information
        
    Returns:
        str: Suggested improved question
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    # Format schema information for context
    if isinstance(schema_info, dict):
        schema_description = format_schema_for_prompt(schema_info)
    else:
        schema_description = schema_info
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Construct prompt for question improvement
        prompt = f"""Given the following user question and database schema, suggest an improved version of the question 
that would lead to a more precise SQL query. Make sure the improved question is clear, specific, and uses correct terminology 
based on the schema.

Database Schema:
{schema_description}

User Question: "{user_question}"

Provide ONLY the improved question as your response. Do not include any explanations, preface or quotes.
"""
        
        print("Generating question improvement suggestion...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        improved_question = response.choices[0].message.content.strip()
        return improved_question
    
    except Exception as e:
        print(f"Error generating question improvement: {str(e)}")
        return ""

def generate_followup_questions(user_question, sql_query, schema_info):
    """
    Generate follow-up questions based on the current query and results.
    
    Args:
        user_question (str): The user's original question
        sql_query (str): The executed SQL query
        schema_info (dict or str): Database schema information
        
    Returns:
        list: List of suggested follow-up questions
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    # Format schema information for context
    if isinstance(schema_info, dict):
        schema_description = format_schema_for_prompt(schema_info)
    else:
        schema_description = schema_info
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Construct prompt for follow-up questions
        prompt = f"""Given the following user question, SQL query, and database schema, suggest 3-4 logical follow-up questions 
that the user might be interested in asking next. These questions should be related to the original question but explore 
different aspects or dig deeper into the data.

Database Schema:
{schema_description}

Original User Question: "{user_question}"

SQL Query:
{sql_query}

Provide ONLY a list of follow-up questions, one per line, without numbering or bullet points. Each question should be natural 
and conversational, and should be different enough to provide new insights.
"""
        
        print("Generating follow-up question suggestions...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Higher temperature for more variety
            max_tokens=200
        )
        
        # Split the response into individual questions
        followup_text = response.choices[0].message.content.strip()
        followup_questions = [q.strip() for q in followup_text.split('\n') if q.strip()]
        
        # Limit to 4 questions maximum
        return followup_questions[:4]
    
    except Exception as e:
        print(f"Error generating follow-up questions: {str(e)}")
        return []

def analyze_query(sql_query, schema_info=None):
    """
    Analyze the SQL query for potential performance issues and suggest optimizations.
    
    Args:
        sql_query (str): The SQL query to analyze
        schema_info (dict, optional): Database schema information
        
    Returns:
        dict: Analysis results with suggestions
    """
    results = {
        'suggestions': [],
        'warnings': [],
        'complexity': 'Simple',
        'estimated_impact': []
    }
    
    # Convert to uppercase for analysis but keep original for display
    query_upper = sql_query.upper()
    
    # Basic checks
    
    # Check for SELECT * without LIMIT
    if "SELECT *" in query_upper and "LIMIT" not in query_upper:
        results['suggestions'].append({
            'issue': 'SELECT * without LIMIT',
            'suggestion': 'Add a LIMIT clause when using SELECT * to reduce data transfer',
            'impact': 'High',
            'example': f"Original: SELECT * FROM table\nOptimized: SELECT * FROM table LIMIT 100"
        })
    
    # Check for missing indexes on JOIN conditions
    if "JOIN" in query_upper:
        # Extract table names from JOIN clauses
        join_pattern = r'JOIN\s+(\w+)'
        tables = re.findall(join_pattern, sql_query, re.IGNORECASE)
        
        if tables and schema_info:
            for table in tables:
                if table in schema_info:
                    # Check if JOIN columns have indexes
                    results['suggestions'].append({
                        'issue': 'Potential missing indexes on JOIN columns',
                        'suggestion': f'Consider adding indexes on JOIN columns for table "{table}"',
                        'impact': 'High',
                        'example': f"CREATE INDEX idx_{table}_join_col ON {table}(join_column)"
                    })
    
    # Check for aggregations without indexes
    if "GROUP BY" in query_upper:
        results['suggestions'].append({
            'issue': 'GROUP BY operation',
            'suggestion': 'Ensure columns in GROUP BY clause have indexes for faster aggregation',
            'impact': 'Medium',
            'example': "CREATE INDEX idx_table_groupby_col ON table(group_by_column)"
        })
        results['complexity'] = 'Medium'
    
    # Check for ORDER BY on large result sets
    if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
        results['suggestions'].append({
            'issue': 'ORDER BY without LIMIT',
            'suggestion': 'Add LIMIT clause after ORDER BY for large result sets',
            'impact': 'Medium',
            'example': f"Original: {sql_query}\nOptimized: {sql_query} LIMIT 100"
        })
    
    # Check for subqueries which could be optimized
    if "SELECT" in query_upper and "SELECT" in query_upper[query_upper.index("SELECT")+6:]:
        results['suggestions'].append({
            'issue': 'Subquery detected',
            'suggestion': 'Consider replacing subqueries with JOINs where possible',
            'impact': 'Medium',
            'example': "Original: SELECT * FROM table1 WHERE col IN (SELECT col FROM table2)\nOptimized: SELECT table1.* FROM table1 JOIN table2 ON table1.col = table2.col"
        })
        results['complexity'] = 'Complex'
    
    # Check for unnecessary DISTINCT
    if "DISTINCT" in query_upper and "GROUP BY" in query_upper:
        results['suggestions'].append({
            'issue': 'DISTINCT with GROUP BY',
            'suggestion': 'DISTINCT is usually unnecessary with GROUP BY as GROUP BY already returns unique rows',
            'impact': 'Low',
            'example': f"Consider removing DISTINCT when using GROUP BY"
        })
    
    # Estimate query complexity
    if "JOIN" in query_upper and ("GROUP BY" in query_upper or "ORDER BY" in query_upper):
        if query_upper.count("JOIN") > 2:
            results['complexity'] = 'Complex'
        else:
            results['complexity'] = 'Medium'
    
    if "HAVING" in query_upper:
        results['complexity'] = 'Complex'
    
    # Set estimated impact
    if results['complexity'] == 'Complex':
        results['estimated_impact'].append("This query may be resource-intensive on large datasets")
    
    return results

def format_schema_for_prompt(schema_info):
    """
    Format the schema information into a readable format for the prompt.
    
    Args:
        schema_info (dict): Dictionary containing database schema information
    
    Returns:
        str: Formatted schema description
    """
    schema_text = []
    
    for table_name, columns in schema_info.items():
        table_desc = f"Table: {table_name}\nColumns:"
        
        for col in columns:
            primary_key = "PRIMARY KEY" if col['is_primary_key'] else ""
            not_null = "NOT NULL" if col['notnull'] else ""
            constraints = " ".join(filter(None, [primary_key, not_null]))
            
            if constraints:
                table_desc += f"\n  - {col['name']} ({col['type']}) {constraints}"
            else:
                table_desc += f"\n  - {col['name']} ({col['type']})"
        
        schema_text.append(table_desc)
    
    return "\n\n".join(schema_text) 