import json
import re
import random

class QuestionHumanizer:
    def __init__(self):
        self.conversation_starters = [
            "I'd like to understand",
            "Could you walk me through",
            "I'm curious about",
            "Tell me about",
            "I'd love to hear about",
            "Let's discuss",
            "Could you share",
            "Help me understand"
        ]
        
        self.follow_up_phrases = [
            "What approach did you take?",
            "How did you handle that?",
            "What was your thought process?",
            "What steps did you take?",
            "How did you manage the situation?"
        ]
        
        self.context_phrases = {
            "customer_service": [
                "given our recent customer satisfaction challenges",
                "considering our focus on service quality",
                "with our commitment to customer experience"
            ],
            "team_management": [
                "with our current team dynamics",
                "given the training completion rates",
                "considering our staff retention goals"
            ],
            "leadership": [
                "as a leader in our organization",
                "in your role as Regional Manager",
                "with your team responsibilities"
            ]
        }

    def humanize_question(self, question, theme):
        """Convert formal questions into conversational format"""
        
        # Remove any existing numbering
        question = re.sub(r'^\d+[\.\)]\s*', '', question.strip())
        
        # Extract key metrics if present
        metrics_pattern = r'(\d+(?:\.\d+)?%|\d+\.\d+)'
        metrics = re.findall(metrics_pattern, question)
        
        # Choose appropriate context phrase based on theme
        context = ""
        for key, phrases in self.context_phrases.items():
            if key in theme.lower():
                context = f", {random.choice(phrases)}, "
                break
        
        # Build conversational question
        starter = random.choice(self.conversation_starters)
        follow_up = random.choice(self.follow_up_phrases)
        
        # Create base conversational question
        conversational = f"{starter}{context}a situation where {question.lower()}"
        
        # Add metrics if they existed in original question
        if metrics:
            conversational = conversational.replace("a situation", f"a specific situation")
            for metric in metrics:
                if metric not in conversational:
                    conversational += f" The target was {metric}."
        
        # Add follow-up if question doesn't already have one
        if not any(phrase.lower() in conversational.lower() for phrase in self.follow_up_phrases):
            conversational += f" {follow_up}"
        
        return conversational

    def process_questions_file(self, input_file, output_file):
        """Process entire questions file and humanize all questions"""
        
        try:
            # Read existing questions
            with open(input_file, 'r') as f:
                questions_data = json.load(f)
            
            # Process each theme and its questions
            humanized_data = {}
            for theme, questions in questions_data.items():
                humanized_questions = []
                for question in questions:
                    humanized = self.humanize_question(question, theme)
                    humanized_questions.append(humanized)
                humanized_data[theme] = humanized_questions
            
            # Save humanized questions
            with open(output_file, 'w') as f:
                json.dump(humanized_data, f, indent=2)
            
            print(f"Successfully humanized questions and saved to {output_file}")
            
        except Exception as e:
            print(f"Error processing questions: {e}")

# Example usage
if __name__ == "__main__":
    humanizer = QuestionHumanizer()
    
    # Example transformations
    examples = [
        {
            "theme": "Customer Service Excellence",
            "original": "Describe a situation where customer satisfaction dropped from 4.00 to 2.75. What actions did you take?",
            "humanized": humanizer.humanize_question(
                "Describe a situation where customer satisfaction dropped from 4.00 to 2.75. What actions did you take?",
                "Customer Service Excellence"
            )
        },
        {
            "theme": "Team Management",
            "original": "How did you handle training completion rate of 58%?",
            "humanized": humanizer.humanize_question(
                "How did you handle training completion rate of 58%?",
                "Team Management"
            )
        }
    ]
    
    print("\nExample Transformations:")
    for example in examples:
        print(f"\nTheme: {example['theme']}")
        print(f"Original: {example['original']}")
        print(f"Humanized: {example['humanized']}")
    
    # Process actual questions file
    humanizer.process_questions_file(
        'behavioral_interview_questions.json',
        'humanized_interview_questions.json'
    ) 