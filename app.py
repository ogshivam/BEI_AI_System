from flask import Flask, render_template, request, jsonify, session, url_for, send_from_directory, redirect, send_file
from bei_system import BEI_System
from question_humanizer import QuestionHumanizer
import json
import os
import time
import random
from collections import defaultdict
from datetime import datetime
import requests
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__, static_folder='static')
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Add these configurations
UPLOAD_FOLDER = 'temp_audio'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_questions():
    """Initialize the question system and ensure humanized questions exist"""
    try:
        # Check if humanized questions exist
        if not os.path.exists('humanized_interview_questions.json'):
            print("Generating humanized questions...")
            humanizer = QuestionHumanizer()
            humanizer.process_questions_file(
                'behavioral_interview_questions.json',
                'humanized_interview_questions.json'
            )
        
        # Initialize BEI System
        return BEI_System('humanized_interview_questions.json', '/Users/shivampratapwar/Library/Mobile Documents/com~apple~CloudDocs/Desktop/bei_final/data/metrics.json')
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure both 'behavioral_interview_questions.json' and 'data/metrics.json' exist")
        raise

# Initialize BEI System
try:
    bei_system = initialize_questions()
except Exception as e:
    print(f"Failed to initialize BEI system: {e}")
    bei_system = None

def select_five_questions(questions_dict):
    """Select 5 questions total from all themes"""
    all_questions = []
    for theme, theme_questions in questions_dict.items():
        # Take all questions from each theme
        for question in theme_questions:
            all_questions.append({
                'theme': theme,
                'question': question
            })
    
    # Select 5 questions randomly
    if len(all_questions) > 5:
        all_questions = random.sample(all_questions, 5)
    
    return all_questions

@app.route('/')
def index():
    if bei_system is None:
        return "System initialization failed. Please check the logs.", 500
    return render_template('index.html')

def check_llm_server():
    """Check if the local LLM server is running and responding"""
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        return response.status_code == 200
    except:
        return False

@app.route('/start_interview', methods=['POST'])
def start_interview():
    try:
        # Check if LLM server is running
        if not check_llm_server():
            return jsonify({
                'success': False,
                'error': 'LLM server is not running. Please start the Ollama server first.'
            }), 503
        
        data = request.get_json()
        
        # Store in session
        session['candidate_name'] = data.get('fullName')
        session['candidate_email'] = data.get('email')
        session['start_time'] = time.time()
        
        # Get questions from BEI system
        questions_dict = bei_system.get_questions()
        selected_questions = select_five_questions(questions_dict)
        
        # Store questions in session
        session['selected_questions'] = selected_questions
        session['current_question'] = 0  # Initialize to 0 so first question will be 1
        session['total_questions'] = 5   # Set total questions to 5
        session['answers'] = []          # Initialize answers array
        
        # Return success and redirect to introduction
        return jsonify({
            'success': True,
            'redirect_url': url_for('introduction')
        })
    except Exception as e:
        print(f"Start interview error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/begin_interview', methods=['POST'])
def begin_interview():
    if 'candidate_name' not in session:
        return jsonify({'success': False, 'error': 'Session expired'}), 401
    return jsonify({
        'success': True,
        'redirect_url': url_for('interview')
    })

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        answer = data.get('answer', '')
        
        if not answer:
            return jsonify({'error': 'No answer provided'}), 400
            
        # Get current question number and total questions
        current_number = session.get('current_question', 0)
        total_questions = session.get('total_questions', 2)
        
        # Get the current question from the session
        questions = session.get('selected_questions', [])
        if not questions or current_number >= len(questions):
            return jsonify({'error': 'Invalid question number'}), 400
            
        current_question = questions[current_number]
        
        # Analyze the response using LLM
        try:
            print("Analyzing response with LLM...")
            # Make request to local LLM instance
            prompt = f"""Analyze this behavioral interview response for RBI Grade C-D position:

Question Theme: {current_question['theme']}
Question: {current_question['question']}
Candidate's Answer: {answer}

Rate the response on these three metrics using the exact scoring criteria below:

1. communicate_clearly: Ability to convey information in a clear, structured, and understandable manner
Scoring levels:
1.0: Not able to convey information clearly and logically to ensure understanding
1.5: Shows minimal improvement in conveying information but still lacks clarity and structure
2.0: Shares accurate, timely and concise information in an effective manner
2.5: Demonstrates good information sharing with occasional gaps in structure or clarity
3.0: Consistently shares accurate, timely information with the right people in the right format
3.5: Shows excellent communication skills with minor room for improvement in structure or impact
4.0: Structured, organized and clear in communication - verbal and written to ensure understanding and impact

2. engage_discussion: Ability to participate and contribute effectively in dialogues
Scoring levels:
1.0: Avoids discussions as not able to engage people in fruitful discussions
1.5: Makes limited attempts to engage in discussions but struggles to maintain dialogue
2.0: Maintains open, honest dialogue with others to integrate their thoughts and ideas
2.5: Shows good engagement in discussions with room for improvement in integration of ideas
3.0: Models openness and transparency in sharing information with others to ensure meeting objectives
3.5: Demonstrates strong discussion skills with minor improvements needed in effectiveness
4.0: Actively participates; contributes effectively in discussions to ensure comprehension & meeting desired objectives

3. engage_actively: Level of active involvement and adaptation in communication
Scoring levels:
1.0: Keeps communication to a minimum. Reticent to share thoughts and ideas
1.5: Shows minimal active engagement with limited adaptation to different situations
2.0: Attentive to verbal communication and sometimes adjusts communication style and content
2.5: Demonstrates good active engagement with room for improvement in adaptation
3.0: Attentive to both verbal and non verbal cues and accurately adapts communications to suit most audiences
3.5: Shows excellent engagement with minor improvements needed in adaptation or credibility
4.0: Attentive to both verbal & non verbal communication, interprets and responds appropriately with credibility

Provide analysis in this exact JSON format:
{{
    "communicate_clearly": <score 1.0-4.0>,
    "engage_discussion": <score 1.0-4.0>,
    "engage_actively": <score 1.0-4.0>,
    "feedback": "<detailed constructive feedback based on the scoring criteria above>"
}}

Note: Scores must be one of these exact values: 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0"""

            print("Sending request to LLM server...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            print(f"LLM Response Status: {response.status_code}")
            if response.status_code == 200:
                response_data = response.json()
                response_text = response_data.get('response', '')
                print(f"LLM Raw Response: {response_text}")
                
                # Extract JSON from response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > 0:
                    json_str = response_text[start:end]
                    try:
                        analysis = json.loads(json_str)
                        print(f"Parsed Analysis: {analysis}")
                        
                        # Validate and clean scores
                        valid_scores = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
                        for metric in ['communicate_clearly', 'engage_discussion', 'engage_actively']:
                            if metric not in analysis:
                                print(f"Missing metric {metric}, using default")
                                analysis[metric] = 2.0  # Default to developing level
                            else:
                                # Round to nearest 0.5 and ensure within valid range
                                try:
                                    score = float(analysis[metric])
                                    rounded_score = round(score * 2) / 2  # Round to nearest 0.5
                                    analysis[metric] = min(max(rounded_score, 1.0), 4.0)
                                    # Ensure score is one of the valid increments
                                    if analysis[metric] not in valid_scores:
                                        analysis[metric] = min(valid_scores, key=lambda x: abs(x - analysis[metric]))
                                    print(f"Processed {metric} score: {analysis[metric]}")
                                except (ValueError, TypeError) as e:
                                    print(f"Error processing score for {metric}: {e}")
                                    analysis[metric] = 2.0
                        
                        # Ensure feedback exists and is meaningful
                        if 'feedback' not in analysis or not analysis['feedback'] or len(analysis['feedback'].strip()) < 20:
                            print("Invalid feedback, using default")
                            analysis['feedback'] = f"Based on your response to the question about {current_question['theme'].lower()}, consider providing more specific examples and following the STAR format. Include detailed situations, tasks, actions taken, and results achieved."
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse LLM response as JSON: {e}")
                        analysis = bei_system._generate_default_analysis()
                else:
                    print("No JSON found in LLM response")
                    analysis = bei_system._generate_default_analysis()
            else:
                print(f"LLM request failed with status {response.status_code}")
                analysis = bei_system._generate_default_analysis()
                
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to LLM server: {e}")
            analysis = bei_system._generate_default_analysis()
        except Exception as e:
            print(f"Unexpected error in LLM analysis: {e}")
            analysis = bei_system._generate_default_analysis()
        
        # Store the answer and scores in the session
        if 'answers' not in session:
            session['answers'] = []
            
        session['answers'].append({
            'question': current_question['question'],
            'answer': answer,
            'metrics': {
                'communicate_clearly': analysis['communicate_clearly'],
                'engage_discussion': analysis['engage_discussion'],
                'engage_actively': analysis['engage_actively']
            },
            'feedback': analysis['feedback'],
            'theme': current_question['theme']
        })
        
        # Update current question number
        next_question_number = current_number + 1
        session['current_question'] = next_question_number
        
        # Check if interview is complete
        if next_question_number >= total_questions:
            # Generate final report
            report = generate_report()
            
            # Save report to file
            os.makedirs('reports', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f'reports/interview_report_{timestamp}.json'
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            return jsonify({
                'complete': True,
                'message': 'Interview complete',
                'redirect_url': url_for('report')
            })
        else:
            # Get the next question
            next_question = questions[next_question_number]
            return jsonify({
                'next_question': True,
                'message': 'Moving to next question',
                'current_number': next_question_number + 1,
                'total_questions': total_questions,
                'question': next_question['question'],
                'theme': next_question['theme']
            })
            
    except Exception as e:
        print(f"Error in submit_answer: {str(e)}")
        return jsonify({'error': 'Failed to process answer'}), 500

def round_to_nearest_half(score):
    """Round a score to the nearest 0.5"""
    return round(score * 2) / 2

def get_performance_rating(score):
    """Get performance rating based on score"""
    if score >= 3.5:
        return "Excellent"
    elif score >= 2.5:
        return "Good"
    elif score >= 1.5:
        return "Fair"
    else:
        return "Needs Improvement"

def generate_report():
    try:
        if 'answers' not in session or not session['answers']:
            return None
            
        # Get session data
        candidate_name = session.get('candidate_name', 'Anonymous')
        answers = session.get('answers', [])
        start_time = session.get('start_time', time.time())
        total_time = time.time() - start_time
        
        # Calculate average scores (maintaining 1.0-4.0 scale with 0.5 increments)
        total_communicate = 0
        total_engage = 0
        total_active = 0
        
        for answer in answers:
            total_communicate += answer['metrics']['communicate_clearly']
            total_engage += answer['metrics']['engage_discussion']
            total_active += answer['metrics']['engage_actively']
        
        # Round averages to nearest 0.5
        avg_communicate = round_to_nearest_half(total_communicate / len(answers))
        avg_engage = round_to_nearest_half(total_engage / len(answers))
        avg_active = round_to_nearest_half(total_active / len(answers))
        
        # Calculate overall score (also rounded to nearest 0.5)
        overall_score = round_to_nearest_half((avg_communicate + avg_engage + avg_active) / 3)
        
        # Generate report data
        report = {
            'candidate_info': {
                'name': candidate_name,
                'interview_date': datetime.now().strftime('%B %d, %Y'),
                'total_time': f"{int(total_time // 60)} minutes {int(total_time % 60)} seconds"
            },
            'answers': answers,
            'metrics': {
                'communicate_clearly': {
                    'score': avg_communicate,
                    'rating': get_performance_rating(avg_communicate),
                    'description': 'Ability to convey information in a clear, structured, and understandable manner'
                },
                'engage_discussion': {
                    'score': avg_engage,
                    'rating': get_performance_rating(avg_engage),
                    'description': 'Ability to participate and contribute effectively in dialogues'
                },
                'engage_actively': {
                    'score': avg_active,
                    'rating': get_performance_rating(avg_active),
                    'description': 'Level of active involvement and adaptation in communication'
                }
            },
            'overall_score': overall_score,
            'overall_rating': get_performance_rating(overall_score),
            'chart_data': {
                'labels': ['Communicate clearly and concisely', 'Engage in discussions', 'Engage actively'],
                'scores': [avg_communicate, avg_engage, avg_active]
            }
        }
        
        # Save report to file
        os.makedirs('reports', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'reports/interview_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return None

# Update the video serving route
@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    try:
        return send_from_directory(os.path.join(app.static_folder, 'videos'), filename)
    except Exception as e:
        print(f"Error serving video: {e}")
        return "Video not found", 404

# Add this to check if video exists
@app.route('/check_video')
def check_video():
    video_path = os.path.join(app.static_folder, 'videos', 'intro_video.mp4')
    exists = os.path.exists(video_path)
    return jsonify({
        'exists': exists,
        'path': video_path
    })

@app.route('/introduction')
def introduction():
    if 'candidate_name' not in session:
        return redirect(url_for('index'))
    return render_template('introduction.html')

@app.route('/interview')
def interview():
    if 'candidate_name' not in session:
        return redirect(url_for('index'))
    
    # Initialize session variables if they don't exist
    if 'current_question' not in session:
        session['current_question'] = 0
        session['total_questions'] = 2
        session['answers'] = []
    
    # Get the current question
    questions = session.get('selected_questions', [])
    if not questions:
        return redirect(url_for('index'))
    
    current_number = session.get('current_question', 0)
    if current_number >= len(questions):
        return redirect(url_for('report'))
    
    current_question = questions[current_number]
    
    return render_template('interview.html', 
                         question=current_question['question'],
                         theme=current_question['theme'],
                         current_number=current_number + 1,
                         total_questions=session['total_questions'])

@app.route('/report')
def report():
    if 'answers' not in session or not session.get('answers'):
        return redirect(url_for('index'))
        
    report_data = generate_report()
    if not report_data:
        return redirect(url_for('index'))
        
    return render_template('report.html', report=report_data)

@app.route('/serve_pdf')
def serve_pdf():
    pdf_path = '/Users/shivampratapwar/Library/Mobile Documents/com~apple~CloudDocs/Desktop/bei_final/data/case_doc.pdf'
    try:
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name='case_doc.pdf'
        )
    except Exception as e:
        print(f"Error serving PDF: {e}")
        return "PDF not found", 404

@app.route('/transcribe_audio', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
    
    if audio_file and allowed_file(audio_file.filename):
        try:
            # Save the file temporarily
            filename = secure_filename(audio_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(filepath)
            
            # Use Whisper for transcription
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(filepath)
            transcription = result["text"]
            
            # Clean up the temporary file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'transcription': transcription
            })
            
        except Exception as e:
            # Clean up file if it exists
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Invalid file type'}), 400

@app.route('/download_report')
def download_report():
    if 'answers' not in session or not session.get('answers'):
        return redirect(url_for('index'))
        
    report_data = generate_report()
    if not report_data:
        return jsonify({'error': 'No report data available'}), 404
        
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'interview_report_{timestamp}.json'
    
    # Create the report file in memory
    report_json = json.dumps(report_data, indent=2)
    
    # Send file as attachment
    report_bytes = BytesIO(report_json.encode('utf-8'))
    
    return send_file(
        report_bytes,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    os.makedirs('reports', exist_ok=True)
    app.run(debug=True) 