# Deployment Instructions

## Updating the Deployed Application

Follow these steps to update your deployed Text-to-SQL application:

### 1. Connect to your deployment server

```bash
ssh username@your-server-ip
```

### 2. Navigate to the application directory

```bash
cd path/to/Text-To-SQL
```

### 3. Pull the latest changes from GitHub

```bash
git pull origin main
```

### 4. Create or update the .env file with your API key

> **IMPORTANT:** The .env file is NOT included in the GitHub repository for security reasons.

```bash
# Create or edit the .env file
nano .env

# Add your API key (replace with your actual key)
OPENAI_API_KEY=your_api_key_here
```

### 5. Install any new dependencies

```bash
pip install -r requirements.txt
```

### 6. Restart the application

If you're using a systemd service:

```bash
sudo systemctl restart text-to-sql
```

If you're using a screen or tmux session:

```bash
# Find your screen session
screen -ls

# Reconnect to your screen session
screen -r session_id

# Stop the current application (Ctrl+C) and restart it
streamlit run simple_app.py

# Detach from screen session (Ctrl+A then D)
```

If you're using Docker:

```bash
docker-compose down
docker-compose up -d
```

### 7. Verify the application is running

Open your browser and navigate to:

```
http://your-server-ip:8501
```

## Troubleshooting

- If the application fails to start, check the logs:
  ```bash
  journalctl -u text-to-sql -f
  # or
  cat logs/streamlit.log
  ```

- If the .env file is not being loaded, make sure python-dotenv is installed:
  ```bash
  pip install python-dotenv
  ```

- If you get permission errors, make sure your application has the correct file permissions:
  ```bash
  chmod +x simple_app.py
  ``` 