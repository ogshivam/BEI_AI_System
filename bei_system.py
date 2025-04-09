import json
import time
from collections import defaultdict
import requests
from datetime import datetime
import random
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class BEI_System:
    def __init__(self, questions_file, metrics_file):
        self.questions = self.load_file(questions_file)
        self.metrics = self.load_file(metrics_file)
        self.session_data = {
            'start_time': None,
            'candidate_name': None,
            'answers': [],
            'scores': defaultdict(list)
        }
        
    @staticmethod
    def load_file(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    
    def start_interview(self):
        print("\n=== RBI Grade C-D Behavioral Event Interview ===")
        self.session_data['candidate_name'] = input("\nPlease enter candidate name: ")
        print("\nWelcome to the behavioral interview assessment. You'll be asked questions about specific situations.")
        print("Please provide detailed responses using the STAR format:")
        print("- Situation: Describe the context")
        print("- Task: Explain what needed to be done")
        print("- Action: Detail the steps you took")
        print("- Result: Share the outcomes achieved")
        input("\nPress Enter when ready to begin...")
        
        self.session_data['start_time'] = time.time()
        
        for theme, questions in self.questions.items():
            print(f"\n=== Theme: {theme} ===")
            for i, question in enumerate(questions, 1):
                print(f"\nQuestion {i}/{len(questions)}:")
                print(f"{question}")
                print("\nPlease provide your response (press Enter twice to finish):")
                
                # Collect multi-line answer
                lines = []
                while True:
                    line = input()
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
                answer = "\n".join(lines[:-1])  # Remove last empty line
                
                analysis = self.analyze_response(question, answer, theme)
                
                self.session_data['answers'].append({
                    'theme': theme,
                    'question': question,
                    'answer': answer,
                    'analysis': analysis
                })
                
                # Update scores
                for metric, score in analysis['scores'].items():
                    self.session_data['scores'][metric].append(score)
                
                print("\n--- Quick Feedback ---")
                print(analysis['feedback'])
                print("\nPress Enter to continue...")
                input()
    
    def analyze_response(self, question, answer, theme):
        """Analyze interview response using LLM model"""
        
        prompt = f"""Analyze this behavioral interview response for RBI Grade C-D position:

Question Theme: {theme}
Question: {question}
Candidate's Answer: {answer}

Rate the response on these three metrics (score 1-4):
1. communicate_clearly: How well did they articulate their thoughts?
2. engage_discussion: How well did they engage with the topic?
3. engage_actively: How actively did they participate in the conversation?

Provide analysis in this exact JSON format:
{{
    "communicate_clearly": <1-4>,
    "engage_discussion": <1-4>,
    "engage_actively": <1-4>,
    "feedback": "<detailed constructive feedback based on the answer>"
}}"""

        try:
            # Make request to local LLM instance
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"LLM request failed with status code: {response.status_code}")
                return self._generate_default_analysis()
            
            response_data = response.json()
            response_text = response_data.get('response', '')
            
            # Try to extract JSON from response
            try:
                # Find JSON content between first { and last }
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > 0:
                    json_str = response_text[start:end]
                    analysis = json.loads(json_str)
                    
                    # Validate and clean scores
                    for metric in ['communicate_clearly', 'engage_discussion', 'engage_actively']:
                        if metric not in analysis:
                            analysis[metric] = 2
                        else:
                            # Ensure score is between 1-4
                            score = float(analysis[metric])
                            analysis[metric] = max(1, min(4, round(score)))
                    
                    # Ensure feedback exists
                    if 'feedback' not in analysis or not analysis['feedback']:
                        analysis['feedback'] = "Thank you for your response. Consider providing more specific examples in future answers."
                        
                    return analysis
                    
            except Exception as e:
                print(f"Error parsing LLM response: {e}")
                print(f"Response text: {response_text}")
                
            return self._generate_default_analysis()
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling LLM: {e}")
            return self._generate_default_analysis()

    def _generate_default_analysis(self):
        """Generate default analysis when LLM fails"""
        return {
            'communicate_clearly': 2,
            'engage_discussion': 2,
            'engage_actively': 2,
            'feedback': "Your response has been recorded. Consider providing more specific examples and following the STAR format in future responses."
        }
    
    def calculate_scores(self):
        weighted_scores = {}
        for metric, data in self.metrics.items():
            scores = self.session_data['scores'][metric]
            if scores:
                avg_score = sum(scores) / len(scores)
                weighted_scores[metric] = avg_score * data['weight']
        return weighted_scores
    
    def generate_report(self):
        total_time = time.time() - self.session_data['start_time']
        scores = self.calculate_scores()
        total_score = sum(scores.values())
        
        report = {
            'candidate_name': self.session_data['candidate_name'],
            'interview_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'duration_minutes': round(total_time / 60, 1),
            'overall_score': round(total_score, 2),
            'competency_scores': {k: round(v, 2) for k, v in scores.items()},
            'detailed_responses': []
        }
        
        for answer in self.session_data['answers']:
            report['detailed_responses'].append({
                'theme': answer['theme'],
                'question': answer['question'],
                'answer': answer['answer'],
                'feedback': answer['analysis']['feedback'],
                'keywords': answer['analysis']['keywords']
            })
        
        # Save JSON report
        filename = f"interview_report_{self.session_data['candidate_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self._print_report_summary(report)
        
        return filename
    
    def _print_report_summary(self, report):
        print("\n=== Interview Assessment Report ===")
        print(f"Candidate: {report['candidate_name']}")
        print(f"Date: {report['interview_date']}")
        print(f"Duration: {report['duration_minutes']} minutes")
        print(f"\nOverall Score: {report['overall_score']}/5.0")
        
        print("\nCompetency Scores:")
        for comp, score in report['competency_scores'].items():
            print(f"- {comp}: {score}/5.0")
        
        print("\nDetailed feedback saved to:", filename)

    def generate_report_data(self, candidate_name, answers, total_time):
        """Generate comprehensive interview report"""
        
        # Calculate scores and analyze responses
        competency_scores = defaultdict(list)
        detailed_feedback = []
        
        for answer in answers:
            # Store detailed analysis for each question
            question_analysis = {
                'theme': answer['theme'],
                'question': answer['question'],
                'answer': answer['answer'],
                'feedback': answer['analysis']['feedback'],
                'key_competencies': answer['analysis']['keywords'],
                'scores': answer['analysis']['scores']
            }
            detailed_feedback.append(question_analysis)
            
            # Aggregate scores by competency
            for metric, score in answer['analysis']['scores'].items():
                competency_scores[metric].append(score)

        # Calculate weighted average scores
        final_scores = {}
        for metric, scores in competency_scores.items():
            avg_score = sum(scores) / len(scores)
            weight = self.metrics[metric]['weight']
            final_scores[metric] = round(avg_score * weight, 2)

        # Calculate overall score
        overall_score = round(sum(final_scores.values()), 2)

        # Generate strengths and areas for improvement
        strengths = []
        improvements = []
        for metric, score in final_scores.items():
            if score >= 4.0:
                strengths.append({
                    'competency': metric,
                    'score': score,
                    'criteria': self.metrics[metric]['criteria']
                })
            elif score <= 3.0:
                improvements.append({
                    'competency': metric,
                    'score': score,
                    'criteria': self.metrics[metric]['criteria']
                })

        # Create comprehensive report
        report = {
            'candidate_info': {
                'name': candidate_name,
                'interview_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'duration_minutes': round(total_time / 60, 1)
            },
            'overall_assessment': {
                'score': overall_score,
                'rating': self._get_rating(overall_score),
                'summary': self._generate_summary(overall_score, strengths, improvements)
            },
            'competency_scores': final_scores,
            'strengths': strengths,
            'areas_for_improvement': improvements,
            'detailed_feedback': detailed_feedback,
            'recommendations': self._generate_recommendations(improvements)
        }
        
        return report

    def _get_rating(self, score):
        """Convert score to rating"""
        if score >= 4.5: return "Outstanding"
        elif score >= 4.0: return "Excellent"
        elif score >= 3.5: return "Very Good"
        elif score >= 3.0: return "Good"
        elif score >= 2.5: return "Fair"
        else: return "Needs Improvement"

    def _generate_summary(self, score, strengths, improvements):
        """Generate overall summary"""
        rating = self._get_rating(score)
        strength_areas = ", ".join([s['competency'] for s in strengths])
        improvement_areas = ", ".join([i['competency'] for i in improvements])
        
        summary = f"The candidate demonstrated {rating.lower()} performance overall. "
        if strengths:
            summary += f"Particular strengths were shown in {strength_areas}. "
        if improvements:
            summary += f"Areas for development include {improvement_areas}."
        return summary

    def _generate_recommendations(self, improvements):
        """Generate development recommendations"""
        recommendations = []
        for area in improvements:
            competency = area['competency']
            criteria = area['criteria']
            recommendations.append({
                'competency': competency,
                'development_actions': [
                    f"Enhance {criteria[0]} through targeted training programs",
                    f"Seek mentoring opportunities in {criteria[1]}",
                    f"Take on projects that develop {criteria[2]}"
                ]
            })
        return recommendations

    def get_questions(self):
        """Return the loaded questions dictionary"""
        return self.questions

if __name__ == "__main__":
    system = BEI_System('behavioral_interview_questions.json', 'data/metrics.json')
    system.start_interview()
    system.generate_report() 