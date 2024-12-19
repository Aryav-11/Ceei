import random
import firebase_admin
from firebase_admin import firestore

# Firebase is already initialized in main.py, no need to initialize again
db = firestore.client()

# Initialize memory as a dictionary to store learned interactions
memory = {}

def store_interaction(user_input, ai_response):
    """Store user inputs and AI responses to Firebase or memory."""
    interaction_ref = db.collection('interactions').document()
    interaction_ref.set({
        'user_input': user_input,
        'ai_response': ai_response
    })
    
    # Store locally as a backup memory
    if user_input not in memory:
        memory[user_input] = []
    memory[user_input].append(ai_response)

def get_response(user_input):
    """Get a dynamic response based on past interactions."""
    if user_input in memory:
        return random.choice(memory[user_input])  # Randomly select a previous response
    else:
        return "Sorry, I didn't quite catch that."

def learn_new_data(user_input, ai_response):
    """Learn new data from the user input and response."""
    store_interaction(user_input, ai_response)

def analyze_sentiment(user_input):
    """Analyze sentiment based on keywords."""
    if "happy" in user_input:
        return "You seem happy!"
    elif "sad" in user_input:
        return "I'm sorry you're feeling sad. How can I help?"
    else:
        return "How can I assist you today?"
