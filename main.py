import speech_recognition as sr
import pyttsx3
import wikipedia
import pywhatkit as kit
import requests
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import schedule
import time
import smtplib
import random
import re
import yagmail
import firebase_admin
from firebase_admin import credentials, db, auth
from textblob import TextBlob
import language_tool_python
# Initialize Firebase if it hasn't been initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("C:\\Users\\Dell\\Desktop\\Ceei\\CRED.json")
    database_url = 'https://ceei-44560-default-rtdb.asia-southeast1.firebasedatabase.app'
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url
    })
from brain import get_response, learn_new_data, analyze_sentiment, store_interaction

# Initialize the recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()
# Global variables
todo_list = []
reply_preference = "both"  # Default preference
# Initialize the GUI
root = tk.Tk()
root.title("Ceei")
root.geometry("500x600")  # Set a fixed size for the window
root.configure(bg="#f0f0f0")  # Set background color
# Create a frame for the output text
frame = tk.Frame(root, bg="#f0f0f0")
frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
output_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, bg="#ffffff", fg="#000000", font=("Arial", 12))
output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
# Input field for text commands
text_input = tk.Entry(root, width=50, font=("Arial", 12), bg="#ffffff", fg="#000000")
text_input.pack(pady=10)
# Button styles
button_style = {
    'font': ("Arial", 12),
    'bg': "#4CAF50",  # Green background
    'fg': "white",  # White text
    'activebackground': "#45a049",  # Darker green when clicked
    'width': 20,
}
def set_reply_preference():
    global reply_preference
    preference = simpledialog.askstring(
        "Reply Preference",
        "How would you like to receive replies? (text, speech, or both):"
    ).strip().lower()

    if preference in ["text", "speech", "both"]:
        reply_preference = preference
    else:
        messagebox.showerror("Invalid Input", "Please enter 'text', 'speech', or 'both'.")
        set_reply_preference()  # Ask again for valid input
def show_error(message):
    messagebox.showerror("Error", message)
# User Profile Functions
def save_user_profile(user_id, name, mood, chat_history, todo_list):
    """Saves the user profile to Firebase with mood, chat history, and to-do list."""
    user_ref = db.reference(f"users/{user_id}")
    user_ref.set({
        'name': name,
        'mood': mood,
        'chat_history': chat_history,
        'todo_list': todo_list
    })
    print(f"User profile saved for {user_id}")
def load_user_profile(user_id):
    """Loads the user profile from Firebase."""
    global user_profile
    user_ref = db.reference(f"users/{user_id}")
    user_data = user_ref.get()
    if user_data:
        # Add the 'id' to the user profile so it's available in the future
        user_data['id'] = user_id  # Add the user_id to the dictionary
        user_profile = user_data  # Update the global user_profile
        chat_history = user_data.get('chat_history', [])  # Default to empty list if no history
        #print(f"User profile loaded for {user_id}: {user_profile}")
        # print(f"Chat history loaded: {chat_history}")
    else:
        print(f"No profile found for {user_id}")
def save_chat_message(user_id, message):
    """Saves chat history for the user in Firebase."""
    # Get a reference to the user's chat history in Firebase
    user_ref = db.reference(f"users/{user_id}/chat_history")
    # Get the existing chat history or initialize an empty list if it doesn't exist
    chat_history = user_ref.get() or []  # Default to empty list if no history exists
    # Append the new message (user input or AI response)
    chat_history.append(message)
    # Save the updated chat history back to Firebase
    user_ref.set(chat_history)
    print(f"Message saved to chat history for user {user_id}: {message}")
def get_chat_history(user_id):
    """Retrieves the chat history for a user from Firebase."""
    user_ref = db.reference(f"users/{user_id}/chat_history")  # Path to chat history in Firebase
    chat_history = user_ref.get() or []  # Get the chat history or return an empty list if no messages
    if chat_history:
        print(f"Chat history for {user_id}:")
        for index, message in enumerate(chat_history, start=1):
            print(f"{index}. {message}")
        return chat_history  # Return the list of messages
    else:
        print(f"No chat history found for {user_id}.")
        return []  # Return empty list if no messages are found
def update_user_mood(user_id, mood):
    """Updates the mood for the user in Firebase."""
    user_ref = db.reference(f"users/{user_id}")  # Use the unique user ID as the reference
    user_ref.update({'mood': mood})  # Update the mood field for this user
    print(f"Mood updated for {user_id}: {mood}")
def add_or_update_todo_task(user_id):
    """Prompts the user for a task and adds or updates it in the user's to-do list in Firebase."""
    # Open the dialog box to ask for the task name
    task = simpledialog.askstring("Add or Update Task", "Enter your task to add:")
    if task:
        # Get a reference to the user's to-do list in Firebase
        user_ref = db.reference(f"users/{user_id}/todo_list")
        # Get the existing to-do list or initialize it as an empty list if it doesn't exist
        todo_list = user_ref.get() or []
        # Append the new task to the to-do list
        todo_list.append(task)
        # Save the updated to-do list back to Firebase
        user_ref.set(todo_list)
        # Output and speak the task added/updated
        print(f"Updated to-do list for {user_id}: {todo_list}")
        speak(f"Task '{task}' added/updated in your to-do list.")
    else:
        speak("Task cannot be empty.")
        print("No task entered.")


def remove_todo_task(user_id):
    """Prompts the user for a task to remove from the to-do list and updates Firebase."""
    # Open the dialog box to ask for the task to remove
    task_to_remove = simpledialog.askstring("Remove Task", "Enter the task to remove:")
    
    if task_to_remove:
        # Get a reference to the user's to-do list in Firebase
        user_ref = db.reference(f"users/{user_id}/todo_list")
        # Get the existing to-do list or initialize it as an empty list if it doesn't exist
        todo_list = user_ref.get() or []
        
        # Check if the task exists in the to-do list
        if task_to_remove in todo_list:
            # Remove the task from the list
            todo_list.remove(task_to_remove)
            # Update Firebase with the new to-do list
            user_ref.set(todo_list)
            print(f"Updated to-do list for {user_id}: {todo_list}")
            speak(f"Task '{task_to_remove}' has been removed from your to-do list.")
        else:
            # If the task is not found in the to-do list
            speak(f"Task '{task_to_remove}' not found in your to-do list.")
            print(f"Task '{task_to_remove}' not found.")
    else:
        # Handle case where no task was entered
        speak("No task entered. Please try again.")
        print("No task entered.")

# Sign Up and Sign In (Firebase Auth)
def sign_up(email, password, name):
    """Signs up a new user."""
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        user_id = user.uid
        save_user_profile(user_id, name, "neutral", [], [])  # Save initial profile with empty data
        print(f"User created successfully with UID: {user_id}")
        return user_id
    except Exception as e:
        print(f"Error during sign up: {e}")
        return None
def sign_in(email, password):
    """Signs in an existing user."""
    try:
        user = auth.get_user_by_email(email)
        print(f"User signed in successfully with UID: {user.uid}")
        return user.uid
    except Exception as e:
        print(f"Error during sign in: {e}")
        return None
def prompt_for_user_details():
    """Prompts user for email, password, and name."""
    print("Please enter your details to sign up:")
    email = input("Email: ")
    password = input("Password: ")
    name = input("Name: ")
    user_id = sign_up(email, password, name)
    if user_id:
        print(f"Welcome, {name}! Your account has been created.")
        load_user_profile(user_id)
        return user_id
    else:
        print("Sign-up failed. Please try again.")
        return None
def prompt_for_sign_in():
    """Prompts user for email and password to sign in."""
    print("Please enter your email and password to sign in:")
    email = input("Email: ")
    password = input("Password: ")
    user_id = sign_in(email, password)
    if user_id:
        print(f"Welcome back! User ID: {user_id}")
        load_user_profile(user_id)
        return user_id
    else:
        print("Sign-in failed. Please check your credentials.")
        return None
spoken_responses = set()  # This set will track responses already spoken

def speak(text):
    if text is None:
        text = "No response available."
    if text not in spoken_responses:
        if reply_preference in ["speech", "both"]:
            engine.say(text)
            engine.runAndWait()
        if reply_preference in ["text", "both"]:
            output_text.insert(tk.END, text + "\n")
        spoken_responses.add(text)  # Add the text to the set to prevent repetition
    output_text.yview(tk.END)  # Scroll to the bottom of the text widget
def listen():
    with sr.Microphone() as source:
        try:
            print("Listening...")
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            show_error("Sorry, I did not understand that.")
            return None
        except sr.RequestError:
            show_error("Could not request results from Google Speech Recognition service.")
            return None
def show_error(message):
    messagebox.showerror("Error", message)
def load_todos(user_id):
    """Loads and displays the to-do list for the current user in a separate pop-up."""
    # Get a reference to the user's to-do list in Firebase
    user_ref = db.reference(f"users/{user_id}/todo_list")
    # Get the existing to-do list or initialize it as an empty list if it doesn't exist
    todo_list = user_ref.get() or []
    # If the to-do list is not empty, display it in a message box
    if todo_list:
        todo_text = "\n".join(f"- {task}" for task in todo_list)
        # Show the to-do list in a pop-up message box
        messagebox.showinfo("Your To-Do List", todo_text)
    else:
        # If the to-do list is empty, inform the user
        messagebox.showinfo("Your To-Do List", "Your to-do list is empty.")
def save_todos():
    ref = db.reference('todos')
    ref.set(todo_list)
def correct_text(text):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    corrected_text = language_tool_python.utils.correct(text, matches)
    return corrected_text
def get_fact_of_the_day():
    url = "https://uselessfacts.jsph.pl/api/v2/facts/random"
    response = requests.get(url)
    fact = response.json()
    return fact['text']
def weather_alerts(city):
    api_key = 'd83aae3239f444f3c6d2ae3c2fbb9c93'
    url = f"http://api.openweathermap.org/data/2.5/alerts?q={city}&appid={api_key}"
    response = requests.get(url)
    alerts = response.json().get('alerts', [])
    if alerts:
        alert_messages = []
        for alert in alerts:
            alert_message = f"Weather alert: {alert['event']}. {alert['description']}"
            alert_messages.append(alert_message)
        return "\n".join(alert_messages)
    else:
        return "No weather alerts for this city."
def print_board(board):
    """Function to print the Tic-Tac-Toe board"""
    for row in board:
        print(" | ".join(row))
        print("-" * 5)  # Print a separator line for rows
def check_winner(board, player):
    """Check if the player has won the game"""
    # Check rows, columns, and diagonals
    for row in board:
        if all([cell == player for cell in row]):
            return True
    for col in range(3):
        if all([board[row][col] == player for row in range(3)]):
            return True
    if all([board[i][i] == player for i in range(3)]):  # Check diagonal
        return True
    if all([board[i][2 - i] == player for i in range(3)]):  # Check reverse diagonal
        return True
    return False
def tic_tac_toe():
    """Main function to play Tic-Tac-Toe"""
    board = [[" " for _ in range(3)] for _ in range(3)]  # Initialize the board
    player_turn = True  # Player starts first
    while True:
        print_board(board)  # Print the current board state
        if player_turn:  # Player's turn
            try:
                row, col = map(int, input("Enter row and column (0-2): ").split())
                if board[row][col] != " ":
                    print("Cell already taken, try again.")
                    continue
            except (ValueError, IndexError):
                print("Invalid input! Please enter numbers between 0 and 2 for row and column.")
                continue
            board[row][col] = "X"  # Player's move
            if check_winner(board, "X"):  # Check if player wins
                print_board(board)
                print("You win!")
                break
        else:  # AI's turn
            print("AI's turn...")
            for i in range(3):
                for j in range(3):
                    if board[i][j] == " ":
                        board[i][j] = "O"  # AI's move (just takes the first available spot)
                        if check_winner(board, "O"):  # Check if AI wins
                            print_board(board)
                            print("AI wins!")
                            return
                        player_turn = True
                        break
        player_turn = not player_turn  # Switch turns
def convert_currency(amount, from_currency, to_currency):
    api_key = "YOUR_API_KEY"  # Add your API key here
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{from_currency}"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        rate = data['conversion_rates'].get(to_currency.upper())
        if rate:
            return f"{amount} {from_currency} = {amount * rate} {to_currency}"
        else:
            return "Invalid target currency."
    return "Error fetching exchange rates."
def analyze_sentiment(text):
    user_input = simpledialog.askstring("How are you?", "How are you feeling today?")
    if user_input:
        blob = TextBlob(user_input)
        sentiment_score = blob.sentiment.polarity
        if sentiment_score > 0.5: mood, response = "happy", "You seem really happy today! I'm glad to hear that!"
        elif sentiment_score > 0: mood, response = "good", "You seem in a good mood! Keep it up!"
        elif sentiment_score < -0.5: mood, response = "sad", "You sound a little down today. Is everything okay?"
        elif sentiment_score < 0: mood, response = "down", "It sounds like you're not feeling your best today. Can I help?"
        else: mood, response = "neutral", "You seem neutral today. Let me know how I can assist you."
        speak(response)
        output_text.insert(tk.END, response + "\n")
        return mood
    return "neutral"
def search_wikipedia(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        speak(summary)
    except wikipedia.exceptions.DisambiguationError:
        show_error("There are multiple results for that. Please be more specific.")
    except wikipedia.exceptions.PageError:
        show_error("I couldn't find anything on that topic.")
def get_weather(city):
    """Fetch weather information based on city name."""
    if not city.isalpha():
        output_text.insert(tk.END, "Invalid city name. Please enter a valid city.\n")
        speak("Invalid city name. Please enter a valid city.")
        return
    api_key = 'd83aae3239f444f3c6d2ae3c2fbb9c93'  # Replace with your actual API key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city}&appid={api_key}&units=metric"
    response = requests.get(complete_url)
    if response.status_code == 200:
        data = response.json()
        # Check if the city exists in the data returned
        if data.get('cod') == 200:
            main_data = data['main']
            weather_data = data['weather'][0]
            wind_data = data['wind']
            # Extracting weather details
            temperature = main_data['temp']
            humidity = main_data['humidity']
            pressure = main_data['pressure']
            description = weather_data['description']
            wind_speed = wind_data['speed']
            speak(f"Weather in {city}:")
            speak(f"Temperature: {temperature}°C")
            speak(f"Humidity: {humidity}%")
            speak(f"Pressure: {pressure} hPa")
            speak(f"Description: {description.capitalize()}")
            speak(f"Wind Speed: {wind_speed} m/s")
        else:
            print(f"City '{city}' not found.")
    else:
        print("Error: Unable to retrieve weather data.")
def announce_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    speak(f"The current time is {current_time}.")
def view_todo(user_id):
    """Retrieves and displays the to-do list for the current user."""
    # Get a reference to the user's to-do list in Firebase
    user_ref = db.reference(f"users/{user_id}/todo_list")
    # Get the existing to-do list or initialize it as an empty list if it doesn't exist
    todo_list = user_ref.get() or []
    # Check if there are any tasks in the to-do list
    if todo_list:
        # Display the to-do list in the GUI or console
        output_text.insert(tk.END, "Your To-Do List:\n")
        for task in todo_list:
            output_text.insert(tk.END, f"- {task}\n")
        speak("Here is your to-do list.")
    else:
        output_text.insert(tk.END, "Your to-do list is empty.\n")
        speak("Your to-do list is empty.")
def set_reminder():
    reminder_time = simpledialog.askstring("Set Reminder", "Enter time in HH:MM format:")
    if reminder_time:
        try:
            schedule.every().day.at(reminder_time).do(lambda: speak("Reminder!"))
            output_text.insert(tk.END, f"Reminder set for {reminder_time}\n")
            speak(f"Reminder set for {reminder_time}.")
            threading.Thread(target=run_reminders).start()
        except ValueError:
            output_text.insert(tk.END, "Invalid time format. Please enter in HH:MM format.\n")
            speak("Invalid time format. Please enter in HH:MM format.")
    else:
        output_text.insert(tk.END, "Please provide a valid time.\n")
        speak("Please provide a valid time.")
def run_reminders():
    while True:
        schedule.run_pending()
        time.sleep(1)
import smtplib
import tkinter as tk
from tkinter import simpledialog, messagebox

def send_email():
    email = simpledialog.askstring("Email", "Enter your email address:")
    password = simpledialog.askstring("Password", "Enter your app password:", show='*')
    
    recipient = simpledialog.askstring("Send Email", "Enter recipient's email:")
    subject = simpledialog.askstring("Email Subject", "Enter email subject:")
    body = simpledialog.askstring("Email Body", "Enter email body:")
    
    if email and password and recipient and subject and body:
        try:
            yag = yagmail.SMTP(user=email, password=password)  # Use Gmail SMTP by default
            yag.send(to=recipient, subject=subject, contents=body)
            output_text.insert(tk.END, f"Email sent to {recipient}\n")
            speak("Email sent successfully.")
        except Exception as e:
            show_error(f"Failed to send email. Error: {e}")
            print(e)  # Debugging

def tell_joke():
    jokes = [
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "I'm reading a book on anti-gravity. It's impossible to put down!",
        "Why don't skeletons fight each other? They don't have the guts.",
        "What do you call fake spaghetti? An impasta!"
    ]
    joke = random.choice(jokes)
    speak(joke)
def fetch_news():
    api_key = "454ea36d7c334e75b13075976f27a231"  # News API key
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        articles = response.json().get('articles', [])
        if articles:
            news_summary = "Top news headlines:\n" + "\n".join([f"- {article['title']}" for article in articles[:5]])
            speak(news_summary)
        else:
            show_error("No news articles found.")
    except requests.exceptions.HTTPError as http_err:
        show_error("News service unavailable. Please check the API key or the service status.")
        print(f"HTTP error occurred: {http_err}")  # Debugging
    except requests.exceptions.RequestException as req_err:
        show_error("Network error. Please check your internet connection.")
        print(f"Request error occurred: {req_err}")  # Debugging
    except Exception as e:
        show_error("An unexpected error occurred while fetching news.")
        print(f"Unexpected error: {e}")  # Debugging
def set_voice():
    print("Setting voice...")  # Debugging line
    voices = engine.getProperty('voices')
    voice_id = simpledialog.askinteger("Select Voice", "Enter 0 for Male, 1 for Female:")
    if 0 <= voice_id < len(voices):
        engine.setProperty('voice', voices[voice_id].id)
        output_text.insert(tk.END, f"Voice changed to {'Male' if voice_id == 0 else 'Female'}\n")
    else:
        show_error("Invalid voice selection.")
def set_speed():
    speed = simpledialog.askinteger("Set Speech Speed", "Enter speech rate (default is 200 wpm):", minvalue=50, maxvalue=300)
    if speed is not None:
        engine.setProperty('rate', speed)
        output_text.insert(tk.END, f"Speech speed set to: {speed} words per minute\n")
    else:
        show_error("Invalid speed value.")
def greet():
    if "name" in user_profile:
        response = f"Hello {user_profile['name']}!"
        speak(response)
        output_text.insert(tk.END, response + "\n")
    else:
        name = simpledialog.askstring("Name", "What is your name?")
        if name:
            user_profile["name"] = name
            user_profile["user_id"] = name.lower()  # Use name as the user_id (You can change this logic)
            # save_user_profile_to_firebase(user_profile["user_id"], name, "both")  # Default preference is 'both'
            response = f"Hello {name}!"
            speak(response)
            output_text.insert(tk.END, response + "\n")
def process_command(command):
    command = command.lower()
    user_id = user_profile["id"]
    # Save the user's input message to Firebase
    user_message = f"User: {command}"
    save_chat_message(user_id, user_message)  # Save user message

    # Get dynamic response from brain.py
    ai_response = get_response(command)  # Get unique response from the brain module

    # Check for specific commands and handle them
    if any(keyword in command for keyword in ["weather", "temperature", "forecast"]):
        city = extract_city(command)  # Use the new dynamic city extraction
        if city:
            ai_response = f"AI: Retrieving weather for {city.capitalize()}."
            get_weather(city.capitalize())  # Call the weather function
            store_interaction(command, ai_response)
        else:
            ai_response = "AI: Please specify a city."
    elif "time" in command:
        announce_time()
        ai_response = "AI: Announcing current time."
    elif any(keyword in command for keyword in ["add", "update", "change", "to-do", "todo", "task"]) and not any(keyword in command for keyword in ["remove", "delete", "clear"]):
        add_or_update_todo_task(user_id)  # Open the dialog for task input
        ai_response = "AI: Please enter the task you want to add or update in your to-do list."

    # Handle view to-do list command (just view, no add or update)
    elif any(keyword in command for keyword in ["view todo","view todos","view my todos"]):
        view_todo(user_id)  # Just view the to-do list without adding/updating
        ai_response = "AI: Showing your to-do list."

    # Handle remove/delete task command (only removal)
    elif any(keyword in command for keyword in ["remove todo", "delete task", "delete todo", "clear todo", "remove task"]):
        remove_todo_task(user_id)  # Open the dialog for task removal
        ai_response = "AI: Please enter the task you want to remove from your to-do list."

    elif "set mood" in command:
        mood = extract_mood(command)  # Extract mood dynamically
        if user_profile and "id" in user_profile:
            update_user_mood(user_profile["id"], mood)
            ai_response = f"AI: Mood set to {mood}."
        else:
            ai_response = "AI: Error, user profile is missing 'id'."
    elif any(keyword in command for keyword in ["chat history"]):
        speak("Retrieving your chat history.")
        chat_history = get_chat_history(user_profile["id"])  # Pass the user ID to the function
        ai_response = f"AI: Retrieving your chat history."
    elif "load todos" in command:
        load_todos(user_id)
        ai_response = "AI: Loading your to-do list."
    elif any(keyword in command for keyword in ["set reminder"]):
        set_reminder()
        ai_response = "AI: Reminder has been set."
    elif "send email" in command:
        send_email()
        ai_response = "AI: Sending email."
    elif any(keyword in command for keyword in ["joke","tell me a joke"]):
        tell_joke()
        ai_response = "AI: Here's a joke for you!"
    elif any(keyword in command for keyword in ["news","current news"]):
        fetch_news()
        ai_response = "AI: Fetching latest news."
    elif "search" in command:
        query = simpledialog.askstring("Search Wikipedia", "What would you like to search for?")
        if query:
            ai_response = f"AI: Searching Wikipedia for {query}."
            search_wikipedia(query)
    elif any(keyword in command for keyword in ["hi","hello"]):
        greet()
        ai_response = "AI: Hello!"
    elif any(keyword in command for keyword in ["convert","change"]):
        parts = command.split()
        amount = float(parts[1])
        from_currency = parts[2].upper()
        to_currency = parts[3].upper()
        result = convert_currency(amount, from_currency, to_currency)
        ai_response = f"AI: Conversion result: {result}"
    elif any(keyword in command for keyword in ["game","games"]):
        tic_tac_toe()
        ai_response = "AI: Starting the game."
    elif any(keyword in command for keyword in ["alert","alerts"]):
        city = extract_city(command)  # Use the new dynamic city extraction
        if city:
            # If city is found, check for weather alerts
            ai_response = f"AI: Checking weather alerts for {city}."
            speak(weather_alerts(city))  # Function call to check alerts
        else:
            ai_response = "AI: Please specify a city for weather alerts."
    elif any(keyword in command for keyword in ["fact","facts"]):
        fact = get_fact_of_the_day()
        speak(fact)
        ai_response = f"AI: Fact of the day: {fact}"
    elif any(keyword in command for keyword in ["check","correct"]):
        corrected = correct_text(command)
        speak(corrected)
        ai_response = f"AI: Corrected text: {corrected}"
    elif any(keyword in command for keyword in ["developer", "creator", "about you", "who made you", "who are you", "about the developer"]):
        developer_description = """
                I was created by Aryav Chaudhary, an AI enthusiast and developer who is passionate about improving technology.
                He specialize in building AI systems and tools that can adapt to user needs and provide personalized assistance,
                do backend and frontend coding, make lives easier and robotics. "Just a 15 year old kid with a laptop, mouse, headphones,
                and a goal in his mind to create something new": by my Developer. Ways to contact my developer
                Email: chaudharyaryav@gmail.com
                Github: https://github.com/Aryav-11
                """

        speak(developer_description)
        output_text.insert(tk.END, "AI: Here's some information about the developer:\n" + developer_description + "\n")
        ai_response = "AI: Here's some information about the developer."
    elif "how are you" in command or "mood" in command:
        sentiment_response = analyze_sentiment(command)
        if sentiment_response:
            ai_response = f"AI: Sentiment analysis result: {sentiment_response}"
            speak(sentiment_response)
        else:
            ai_response = "AI: I didn't catch that, can you tell me how you're feeling?"
    elif any(keyword in command for keyword in ["bye","cya"]):
        speak("Goodbye!")
        ai_response = "AI: Goodbye!"
        root.quit()
    else:
        speak("Sorry, I didn't understand that command.")
        ai_response = "AI: Sorry, I didn't understand that command."
    
    # Save the AI's response to Firebase chat history
    save_chat_message(user_id, ai_response)  # Save AI response
    
    # After getting AI response, let's store the interaction in Firebase
    learn_new_data(command, ai_response)
##########################START OF DYNAMIC EXTRACTION####################################
def extract_search_query(command):
    """Extract the query from the search command."""
    return command.replace("wikipedia", "").strip()
def extract_city(command):
    """Dynamically extract city names from the user's command."""
    # Look for the word after 'in' or 'from' to get the city name
    match = re.search(r'(?:in|from)\s+([a-zA-Z\s]+)', command)
    if match:
        # Return the city name
        return match.group(1).strip()
    return None
def extract_mood(command):
    """Extract mood from command."""
    return command.replace("set mood", "").strip()
def extract_task(command):
    """Extract task description from the 'add to-do' command."""
    return command.replace("add todo", "").strip()

#########################END OF DYNAMIC EXTRACTION#######################################

def on_listen():
    command = listen()
    if command:
        print(f"Recognized command: {command}")  # Debugging line
        output_text.insert(tk.END, f"You: {command}\n")
        process_command(command)
def on_submit():
    command = text_input.get()
    output_text.insert(tk.END, f"You: {command}\n")
    process_command(command)
    text_input.delete(0, tk.END)  # Clear input field after submitting
# Initial Setup: Sign up or Sign In
def initial_setup():
    """Prompts user for sign-up or sign-in"""
    choice = input("Do you want to sign up or sign in? (sign up/sign in): ").strip().lower()
    if choice == "sign up":
        user_id = prompt_for_user_details()
    elif choice == "sign in":
        user_id = prompt_for_sign_in()
    else:
        print("Invalid choice. Exiting.")
        return None
    # Validating user ID
    if user_id:
        return user_id
    else:
        print("Something went wrong.")
        return None
# Start Initial Setup for the AI
user_id = initial_setup()


if user_id:
    # Call to set reply preference at the start
    set_reply_preference()

    # Now continue with your regular AI functions (e.g., weather, jokes, etc.)
    # Adding buttons to start listening and submit typed command
    listen_button = tk.Button(root, text="Start Listening", command=on_listen, **button_style)
    listen_button.pack(pady=5)

    submit_button = tk.Button(root, text="Submit Command", command=on_submit, **button_style)
    submit_button.pack(pady=5)

    manual_test_button = tk.Button(root, text="Test Set Voice", command=set_voice, **button_style)
    manual_test_button.pack(pady=5)

    speed_button = tk.Button(root, text="Set Speed", command=set_speed, **button_style)
    speed_button.pack(pady=5)

    # Start the GUI loop
    root.mainloop()