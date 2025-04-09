import os
import json

def ensure_directory_exists(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def create_default_metrics():
    """Create default metrics file if it doesn't exist"""
    metrics = {
        "customer_centricity": {
            "weight": 0.3,
            "criteria": ["customer focus", "empathy", "service recovery"]
        },
        "leadership": {
            "weight": 0.25,
            "criteria": ["decision making", "team motivation", "conflict resolution"]
        },
        "problem_solving": {
            "weight": 0.25,
            "criteria": ["analytical skills", "creativity", "bias for action"]
        },
        "communication": {
            "weight": 0.2,
            "criteria": ["clarity", "structure", "persuasion"]
        }
    }
    
    with open('data/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print("Created default metrics file")

def create_default_questions():
    """Create default questions file if it doesn't exist"""
    questions = {
        "Customer Service Excellence": [
            "Describe a situation where customer satisfaction dropped from 4.00 to 2.75. What actions did you take?",
            "How did you handle a difficult customer complaint about hidden charges?",
            "Tell me about a time when you improved service quality for senior citizens."
        ],
        "Team Management": [
            "How did you handle training completion rate of 58%?",
            "What steps did you take to reduce high staff turnover?",
            "Describe how you motivated your team during performance decline."
        ]
    }
    
    with open('behavioral_interview_questions.json', 'w') as f:
        json.dump(questions, f, indent=2)
    print("Created default questions file")

def setup():
    """Run complete setup"""
    print("Setting up BEI system...")
    
    # Create necessary directories
    ensure_directory_exists('data')
    ensure_directory_exists('reports')
    ensure_directory_exists('static/videos')
    
    # Create default files if they don't exist
    if not os.path.exists('data/metrics.json'):
        create_default_metrics()
    
    if not os.path.exists('behavioral_interview_questions.json'):
        create_default_questions()
    
    print("\nSetup complete! You can now run the application.")
    print("Don't forget to:")
    print("1. Place your intro video in static/videos/intro_video.mp4")
    print("2. Customize the questions in behavioral_interview_questions.json")
    print("3. Adjust the metrics in data/metrics.json if needed")

if __name__ == "__main__":
    setup() 