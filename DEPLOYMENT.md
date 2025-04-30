# Simple Deployment Guide for BEI Interview System

This guide provides the essential steps to deploy the BEI Interview System on your internal server.

## System Requirements

- Python 3.11 or higher(3.11.7 preferred)
- 8GB RAM
- 20GB disk space

## Step 1: Initial Setup

1. Copy all project files to your server or clone the repository:
```bash
git clone [your-repository-url]
cd [project-directory]
```

2. Set up Python environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR
.\venv\Scripts\activate   # On Windows

pip install -r requirements.txt
```

## Step 2: Application Setup

1. Run the setup script to create necessary directories:
```bash
python setup.py
```

2. Create a `.env` file with basic configuration:
```
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key-here
```

3. Place required media files:
   - Put intro video in `static/videos/intro_video.mp4`
   - Ensure avatar files are in `SadTalker` directory

## Step 3: Install and Start Ollama (Required for LLM)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh  # On Linux
# OR
brew install ollama  # On MacOS

# Start Ollama
ollama serve

# In a new terminal, pull the required model
ollama pull mistral
```

## Step 4: Run the Application

### For Linux/Mac:
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 3 app:app
```

### For Windows:
```bash
pip install waitress
python run.py  # This will start the server on port 8000
```

The application will be available at: `http://your-server-ip:8000`

## Troubleshooting

If the application doesn't start:
1. Check if Ollama is running
2. Verify all files in `static/videos` are present
3. Ensure Python virtual environment is activated
4. Check error messages in the terminal
