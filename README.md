# 🌌 Text-to-SQL AI Converter

<div align="center">

![License: MIT](https://img.shields.io/badge/License-MIT-blueviolet.svg)
![Python](https://img.shields.io/badge/Python-3.7+-8b5cf6?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.9+-6d28d9?logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-API-4c1d95?logo=openai&logoColor=white)

</div>

<div align="center">
<img src="https://example.com/demo.gif" alt="Text-to-SQL Demo" width="80%">
</div>

> *Transform natural language into powerful SQL queries with an intuitive, AI-powered interface. Query your data like you're having a conversation.*

## ✨ Features

<table>
  <tr>
    <td width="50%">
      <h3>🧠 AI-Powered Translation</h3>
      <ul>
        <li>Natural language to SQL conversion using OpenAI's GPT models</li>
        <li>Automatic question improvement suggestions</li>
        <li>Plain English explanations of SQL queries</li>
        <li>Smart follow-up questions based on results</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🔌 Multi-Database Support</h3>
      <ul>
        <li>SQLite (file upload or path)</li>
        <li>MySQL connection</li>
        <li>PostgreSQL integration</li>
        <li>Schema visualization with intelligent formatting</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📊 Results Management</h3>
      <ul>
        <li>Pagination for large result sets</li>
        <li>Query caching system</li>
        <li>Export in CSV, Excel, or JSON formats</li>
        <li>Data visualization capabilities</li>
      </ul>
    </td>
    <td width="50%">
      <h3>💫 Modern UI</h3>
      <ul>
        <li>Galaxy purple theme with gradient accents</li>
        <li>Color-coded data types for schema</li>
        <li>Responsive design with clear visual hierarchy</li>
        <li>Enhanced readability with optimal contrast</li>
      </ul>
    </td>
  </tr>
</table>

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- OpenAI API key
- Database (or use the included sample)

### Installation

```bash
# Clone the repository
git clone https://github.com/Patrickscott999/Text-To-SQL.git
cd Text-To-SQL

# Install required packages
pip install -r requirements.txt

# Set up your API key (replace with your actual key)
export OPENAI_API_KEY="your_api_key_here"

# Launch the application
streamlit run simple_app.py
```

## 🔮 Usage Flow

<div align="center">
  <table>
    <tr>
      <td align="center"><b>Step 1</b></td>
      <td align="center"><b>Step 2</b></td>
      <td align="center"><b>Step 3</b></td>
      <td align="center"><b>Step 4</b></td>
    </tr>
    <tr>
      <td align="center">Connect to a database</td>
      <td align="center">Ask a question in plain English</td>
      <td align="center">Get AI-generated SQL with explanation</td>
      <td align="center">View results & download history</td>
    </tr>
  </table>
</div>

## 💬 Example Queries

```
"Show me all customers who spent more than $500."
```
```
"Find the top 3 products by sales volume in the last month."
```
```
"Which supplier provides the most products and how many?"
```
```
"List orders with their customers and total amounts, sorted by date."
```

## 🗂️ Project Structure

```
Text-To-SQL/
├── simple_app.py       # Main application with enhanced UI
├── app.py              # Alternative simplified version
├── llm_sql.py          # OpenAI integration module
├── create_sample_db.py # Database generation script
├── requirements.txt    # Dependencies
└── sample_retail.db    # Sample SQLite database
```

## 🧩 Sample Database Schema

The included `sample_retail.db` contains the following tables:

**customers**: Customer profiles with contact information  
**products**: Product catalog with pricing and inventory  
**orders**: Order headers with customer and date information  
**order_items**: Line items linking orders and products  
**suppliers**: Supplier information for products  

## ⚠️ Troubleshooting

<details>
<summary><b>Common Issues</b></summary>

| Problem | Solution |
|---------|----------|
| OpenAI API key errors | Verify your API key is set correctly |
| Database connection failures | Check credentials and network connectivity |
| SQL execution errors | Review error details in the app's error section |

</details>

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

<div align="center">
<img src="https://example.com/contributors.png" alt="Contributors" width="60%">
</div>

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Made with ❤️ by <a href="https://github.com/Patrickscott999">Patrick Scott</a></p>
  <p>Give it a ⭐ if you found it useful!</p>
</div> 