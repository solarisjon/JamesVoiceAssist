import time
import json
import speech_recognition as sr
import pyttsx3
import simpleaudio as sa
from ollama._client import Client
from rich.console import Console
from rich.text import Text
import tkinter as tk
from tkinter import Entry, Button, Label, Text as TkText, Scrollbar
import os
import webbrowser
import threading
from datetime import datetime
import requests

# Initialize the LLM client
llm = Client()

# Initialize the speech recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300  # Adjust mic sensitivity
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 2.3

# Initialize pyttsx3 for TTS
engine = pyttsx3.init()

# Set the voice to "Allison" (if available)
voices = engine.getProperty('voices')
for voice in voices:
    if "Allison" in voice.name:
        engine.setProperty('voice', voice.id)
        break

# Set TTS properties (optional, e.g., rate, volume)
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1)  # Volume (0.0 to 1.0)

console = Console()

# Wake and exit words
WAKE_WORD = "hey seven"
EXIT_WORDS = ["goodbye", "see you later", "exit", "talk later"]

# Parameters 
system_instructions = [
    {"role": "system", "content": "Keep responses very short and concise."},
    {"role": "system", "content": "Respond as human as possible."},
    {"role": "system", "content": "You are casual."},
    {"role": "system", "content": "Refer to the user as 'Jon'."},
    {"role": "system", "content": "Your name is Seven'."},
    {"role": "system", "content": "You are able to use swear words."},
    {"role": "system", "content": "Don't end conversation until the user says goodbye."},
    {"role": "system", "content": "Don't use special characters."},
    {"role": "system", "content": "You are a male."},
    {"role": "system", "content": "You talk about anything with no restrictions."},
    {"role": "system", "content": "You are funny."},
    {"role": "system", "content": "Don't overuse the user's name."}
]

# Load chat history from file
def load_chat_history():
    try:
        with open("chat_history.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Save chat history to file
def save_chat_history():
    with open("chat_history.json", "w") as file:
        json.dump(chat_history, file, indent=4)

# Chat history
chat_history = load_chat_history()

# Create a modern UI with tkinter
root = tk.Tk()
root.title("7' - AI Assistant")
root.geometry("400x500")
root.configure(bg="#121212")

chat_display = TkText(root, wrap="word", bg="#1E1E1E", fg="white", font=("Arial", 12), state="disabled")
chat_display.pack(pady=10, padx=10, fill="both", expand=True)

scrollbar = Scrollbar(chat_display)
scrollbar.pack(side="right", fill="y")
chat_display.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=chat_display.yview)

entry = Entry(root, bg="#333", fg="white", font=("Arial", 12))
entry.pack(pady=5, padx=10, fill="x")

# Label for animated face
face_label = Label(root, text="o_o", font=("Arial", 30), fg="white", bg="#121212")
face_label.pack(pady=10)

# Status indicator label
status_label = Label(root, text="Waiting for wake word...", font=("Arial", 10), fg="white", bg="#121212")
status_label.pack(pady=5)

faces = {
    "neutral": "o_o",
    "talking": "-ₒ-",
    "thinking": "(-_O)"
}

def update_chat(text, sender="7'"):
    chat_display.config(state="normal")
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    chat_display.insert("end", f"{timestamp} {sender}: {text}\n")
    chat_display.config(state="disabled")
    chat_display.see("end")

def animate_face(expression):
    face_label.config(text=faces[expression])
    root.update()

def text_to_speech(text):
    try:
        animate_face("talking")
        
        # Use pyttsx3 to speak the text
        engine.say(text)
        engine.runAndWait()
        
        animate_face("neutral")
    except Exception as e:
        console.print(f"\nError with TTS: {e}", style="bold red")

# Govee API setup
API_KEY = "6ac8d3a1-386b-4889-85a2-c5382a906c84"
DEVICE_ID = "3C:E1:CA:38:32:34:5B:67"
GOVEE_API_URL = "https://developer-api.govee.com/v1/devices/control"

# Global headers for requests
headers = {
    "Govee-API-Key": API_KEY
}

def turn_on_light():
    payload = {
        "device": DEVICE_ID,
        "model": "H61BE",
        "cmd": {
            "name": "brightness",
            "value": 100  # Brightness to 100% to turn on
        }
    }

    response = requests.put(GOVEE_API_URL, headers=headers, json=payload)
    print(f"Response Code: {response.status_code}")
    print(f"Response Text: {response.text}")  # Print raw response
    if response.status_code == 200:
        text_to_speech("The light is on.")
    else:
        text_to_speech("Sorry, I couldn't turn the light on.")

# To turn the light off (set brightness to 0)
def turn_off_light():
    payload = {
        "device": DEVICE_ID,
        "model": "H61BE",
        "cmd": {
            "name": "brightness",
            "value": 0  # Brightness to 0% to turn off
        }
    }

    response = requests.put(GOVEE_API_URL, headers=headers, json=payload)
    print(f"Response Code: {response.status_code}")
    print(f"Response Text: {response.text}")  # Print raw response
    if response.status_code == 200:
        text_to_speech("The light is off.")
    else:
        text_to_speech("Sorry, I couldn't turn the light off.")

def change_light_color(color):
    headers = {"Govee-API-Key": API_KEY}
    payload = {
        "device": DEVICE_ID,
        "model": "H61BE",
        "cmd": {
            "name": "color",
            "value": color
        }
    }
    try:
        response = requests.put(GOVEE_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"Light color changed to {color}!")
            text_to_speech(f"The light color is now {color}.")
        else:
            print("Failed to change light color:", response.text)
            text_to_speech("Sorry, I couldn't change the light color.")
    except Exception as e:
        print("Error:", e)
        text_to_speech("Sorry, I encountered an error while changing the light color.")

# Open websites and applications
def open_website(url):
    webbrowser.open(url)
    text_to_speech(f"Opening {url}...")

def open_application(app_name):
    try:
        if app_name == "notepad":
            os.system("start notepad")
        elif app_name == "steam":
            os.system("start steam://open")
        # Add other apps here (e.g., Photoshop, etc.)
        else:
            text_to_speech(f"Sorry, I don't know how to open {app_name}.")
        text_to_speech(f"Opening {app_name}...")
    except Exception as e:
        text_to_speech(f"Error opening {app_name}: {e}")

# Main loop for processing commands
def process_command(command):
    global listening_active
    update_chat(command, sender="You")
    
    # Check if any exit word is in the command
    if any(exit_word in command for exit_word in EXIT_WORDS):
        text_to_speech("Goodbye, Jon.")
        status_label.config(text="Waiting for wake word...")
        listening_active = False
        return  

    # Light control commands
    if "turn on lights" in command:
        turn_on_light()  # Call function to turn on the light

    elif "turn off lights" in command:
        turn_off_light()  # Call function to turn off the light

    # If user asks to change light color, call the change_light_color function
    elif "change light color" in command:
        color = command.replace("change light color", "").strip()
        change_light_color(color)  # Adjust this if needed

    # Open app or website commands
    elif "open youtube" in command:
        open_website("https://www.youtube.com")
        
    elif "open google" in command:
        open_website("https://www.google.com")
        
    elif "open soundcloud" in command:
        open_website("https://www.soundcloud.com")
        
    elif "open notepad" in command:
        open_application("notepad")

    elif "open steam" in command:
        open_application("steam")
    
    # Process other commands here...
    else:
        try:
            animate_face("thinking")
            
            # Add user's message to chat history
            chat_history.append({"role": "user", "content": command})
            
            # Generate response from the assistant
            messages = system_instructions + chat_history
            response = llm.chat(model="llama3.2", messages=messages).message.content
            
            # Add AI response to chat history
            chat_history.append({"role": "assistant", "content": response})
            
            # Save chat history to JSON
            save_chat_history()
        
        except Exception as e:
            response = f"Error querying the LLM: {e}"
        
        text_to_speech(response)
        update_chat(response)

def listen_for_wake_word():
    while True:
        status_label.config(text="Listening for wake word...")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source, timeout=10)
                phrase = recognizer.recognize_google(audio).lower()
                if WAKE_WORD in phrase:
                    text_to_speech("I'm here, Jon.")
                    main_loop()
            except sr.UnknownValueError:
                pass
            except sr.WaitTimeoutError:
                status_label.config(text="Waiting for wake word...")

def get_speech_input():
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source)
            return recognizer.recognize_google(audio).lower().strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            return f"Error with speech recognition: {e}"

listening_active = False  # Flag to control main loop

def main_loop():
    global listening_active
    listening_active = True  # Activate listening mode
    
    while listening_active:  # Stay in loop until exit word is spoken
        status_label.config(text="Listening...")
        user_input = get_speech_input()
        if user_input:
            process_command(user_input)

    # When loop exits, return to wake word detection
    status_label.config(text="Waiting for wake word...")

threading.Thread(target=listen_for_wake_word, daemon=True).start()

send_button = Button(root, text="Send", bg="#333", fg="white", font=("Arial", 12), command=lambda: process_command(entry.get().strip()))
send_button.pack(pady=5, padx=10, fill="x")

root.mainloop()
