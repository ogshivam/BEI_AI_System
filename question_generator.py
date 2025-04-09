import requests
import json
import re
from PyPDF2 import PdfReader

# Configuration
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    reader = PdfReader(pdf_path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n".join(text)

def read_txt_file(txt_path):
    """Read text from TXT file"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()

def clean_text(text):
    """Clean and normalize text"""
    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    return text.strip()

def query_ollama(prompt):
    """Send prompt to Ollama API"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        # First check if server is running
        requests.get("http://localhost:11434/api/health")
    except requests.exceptions.ConnectionError:
        print("Error: Ollama server is not running. Please start it using 'ollama serve'")
        return None
        
    try:
        # Check if model is available
        model_response = requests.get(f"http://localhost:11434/api/tags")
        if model_response.status_code == 200:
            available_models = [model['name'] for model in model_response.json()['models']]
            if MODEL_NAME not in available_models:
                print(f"Error: Model {MODEL_NAME} not found. Available models: {available_models}")
                print(f"Please run: ollama pull {MODEL_NAME}")
                return None
                
        response = requests.post(OLLAMA_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None

def identify_themes(context):
    """Identify key themes using LLM"""
    prompt = """Based on the banking/financial services context, identify 5 clear leadership themes.
    
    Focus specifically on:
    1. Customer service challenges and metrics
    2. Team development and training gaps
    3. Leadership and performance management
    4. Stakeholder management (especially senior citizens)
    5. Process improvement and service standards
    
    Return ONLY a numbered list in this format:
    1. Theme one (make it specific to banking/financial services)
    2. Theme two
    3. Theme three
    """

    response = query_ollama(prompt)
    if response:
        themes = re.findall(r'^\d+\.\s*(.+)$', response, re.MULTILINE)
        
        cleaned_themes = []
        for theme in themes:
            theme = theme.strip()
            if theme and len(theme) > 3:
                cleaned_themes.append(theme)
        
        if not cleaned_themes:
            return [
                "Customer Service Recovery in Banking Operations",
                "Training and Development of Branch Staff",
                "Performance Management and Team Engagement",
                "Senior Citizen Service Enhancement",
                "Branch Operations and Process Improvement"
            ]
            
        return cleaned_themes
    return []

def generate_questions(theme, sample_questions):
    """Generate questions for a theme using LLM"""
    prompt = f"""Generate 5 behavioral interview questions about "{theme}" for banking/financial service leaders.
    
    Use these specific context elements in your questions:
    - Customer satisfaction ratings drop (4.00 to 2.75)
    - Training challenges with new staff (58% training target)
    - Senior citizen complaints about service quality
    - High staff turnover in branches
    - Team ownership and performance issues
    - Conflicting leadership approaches
    
    Reference Questions Style:
    {sample_questions}
    
    Rules:
    1. Each question must start with a number (1-5)
    2. Use STAR format (Situation-Task-Action-Result)
    3. Questions should be specific to banking/financial services
    4. Include metrics and specific scenarios where possible
    5. Focus on leadership challenges from the context
    6. Match the style of the reference questions provided
    
    Example format:
    1. In your branch, customer satisfaction dropped from 4.0 to 2.75 over three months. What specific steps did you take to identify the root causes and how did you engage your team to improve these metrics?
    """

    response = query_ollama(prompt)
    if response:
        # Extract questions using regex
        questions = re.findall(r'^\d+\.\s*(.+)$', response, re.MULTILINE)
        
        # Clean and validate questions
        cleaned_questions = []
        for question in questions:
            question = question.strip()
            if question and len(question) > 10:  # Basic validation
                cleaned_questions.append(question)
                
        # If we don't get enough specific questions, add some default ones
        if len(cleaned_questions) < 5:
            default_questions = [
                f"Given the recent drop in customer satisfaction from 4.00 to 2.75, what specific initiatives did you implement to improve service quality while maintaining team morale?",
                f"How did you handle the situation where senior citizens complained about lack of empathy in service delivery? What changes did you implement and what was the outcome?",
                f"With only 58% training target achievement, how did you modify your approach to ensure new staff received adequate support while maintaining service standards?",
                f"Describe a situation where you had to address high staff turnover in your branch. What retention strategies did you implement and what were the results?",
                f"How did you align different leadership perspectives in your team while ensuring consistent service delivery to customers?"
            ]
            cleaned_questions.extend(default_questions[:(5 - len(cleaned_questions))])
            
        return cleaned_questions[:5]  # Ensure we only return 5 questions
    return []

def main():
    # Load and process documents
    case_text = clean_text(extract_pdf_text("data/case_doc.pdf"))
    sample_text = clean_text(read_txt_file("data/sample_questions.txt"))
    
    # Combine context for theme identification
    combined_context = f"Case Document:\n{case_text}\n\nSample Questions:\n{sample_text}"
    
    # Identify themes
    themes = identify_themes(combined_context)
    print(f"Identified themes: {themes}")
    
    # Generate questions for each theme
    output = {}
    for theme in themes:
        print(f"Generating questions for: {theme}")
        questions = generate_questions(theme, sample_text)
        output[theme] = questions
    
    # Save output
    with open("behavioral_interview_questions.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("Output saved to behavioral_interview_questions.json")

if __name__ == "__main__":
    main()