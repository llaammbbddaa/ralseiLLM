#!/usr/bin/env python3
from chatbox import ChatboxRenderer
import sys
import time

def main():
    # Initialize the chatbox renderer
    chatbox = ChatboxRenderer()
    
    # Welcome message
    welcome_message = "Hi! I'm Ralsei! I'm here to chat with you and be your friend! (Press Ctrl+C to exit)"
    chatbox.display(welcome_message, "happy")
    
    try:
        while True:
            # Get user input (but don't display it)
            user_input = input("\nYou: ")
            
            # For now, just echo back a simple response
            # This is where you'll integrate the LLM later
            response = "That's interesting! I'm looking forward to when I can respond more meaningfully!"
            emotion = "happy"  # This will be determined by the LLM's response later
            
            # Add a small delay to simulate thinking
            time.sleep(0.5)
            
            # Display Ralsei's response
            chatbox.display(response, emotion)
            
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        chatbox.display("Goodbye! It was nice talking to you!", "sad")
        time.sleep(1)
        sys.exit(0)

if __name__ == "__main__":
    main()