import os
import textwrap
import time
from typing import List, Tuple

class ChatboxRenderer:
    def __init__(self, width: int = 50, height: int = 15):
        self.width = width
        self.height = height
        self.emotions = self._load_emotions()

    def _load_emotions(self) -> dict:
        """Load ASCII art emotions from the emotions.txt file."""
        emotions = {
            'happy': ':)',
            'sad': ':(',
            'mad': ':<',
            'surprised': ':o'
        }  # Default fallback emotions
        
        try:
            with open(os.path.join(os.path.dirname(__file__), 'assets', 'emotions.txt'), 'r') as f:
                lines = f.readlines()
                current_emotion = None
                current_art = []
                
                for line in lines:
                    line = line.rstrip()
                    if line.startswith('### '):
                        if current_emotion and current_art:
                            emotions[current_emotion.lower()] = '\n'.join(current_art)
                            current_art = []
                        current_emotion = line.strip('#').strip()
                    elif line.strip():  # Only append non-empty lines
                        current_art.append(line)
                
                # Don't forget to add the last emotion
                if current_emotion and current_art:
                    emotions[current_emotion.lower()] = '\n'.join(current_art)
        
        except FileNotFoundError:
            print("Warning: emotions.txt not found, using fallback emotions")
        
        return emotions

    def _create_border(self, width: int, height: int) -> List[str]:
        """Create a bordered box with the specified dimensions."""
        box = []
        box.append('╔' + '═' * (width - 2) + '╗')
        for _ in range(height - 2):
            box.append('║' + ' ' * (width - 2) + '║')
        box.append('╚' + '═' * (width - 2) + '╝')
        return box

    def _wrap_text(self, text: str) -> List[str]:
        """Wrap text to fit within the chatbox width."""
        return textwrap.wrap(text, width=self.width - 4)  # -4 for borders and padding

    def _get_frame_lines(self, text: str, emotion: str, current_char_count: int) -> List[str]:
        """Generate the lines for a single frame of the animated text display."""
        # Get emotion art
        art = self.emotions.get(emotion.lower(), self.emotions['happy'])
        art_lines = art.split('\n')
        
        # Create partial text for animation
        wrapped_full_text = self._wrap_text(text)
        wrapped_partial_text = []
        chars_remaining = current_char_count
        
        for line in wrapped_full_text:
            if chars_remaining <= 0:
                break
            if chars_remaining >= len(line):
                wrapped_partial_text.append(line)
                chars_remaining -= len(line)
            else:
                wrapped_partial_text.append(line[:chars_remaining])
                chars_remaining = 0
        
        # Create the message box
        box = self._create_border(self.width, max(len(wrapped_full_text) + 4, len(art_lines)))
        
        # Insert text into box
        for i, line in enumerate(wrapped_partial_text, 1):
            box[i] = f'║ {line:<{self.width-4}} ║'
        
        # Combine box and art side by side
        max_height = max(len(box), len(art_lines))
        final_output = []
        
        for i in range(max_height):
            box_line = box[i] if i < len(box) else ' ' * self.width
            art_line = art_lines[i] if i < len(art_lines) else ' ' * len(art_lines[0])
            final_output.append(f'{box_line}  {art_line}')
            
        return final_output

    def display(self, text: str, emotion: str = 'neutral', typing_speed: float = 0.03) -> None:
        """Display the chatbox with animated text typing effect."""
        # Clear screen once at the start
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Get the initial frame to calculate height
        initial_frame = self._get_frame_lines(text, emotion, 0)
        frame_height = len(initial_frame)
        
        # Print initial empty frame
        print('\n'.join(initial_frame))
        
        total_chars = len(text)
        current_chars = 0
        
        while current_chars <= total_chars:
            # Move cursor up to the start of the frame
            print(f"\033[{frame_height}A", end='')
            
            # Generate and print the new frame
            frame = self._get_frame_lines(text, emotion, current_chars)
            print('\n'.join(frame))
            
            current_chars += 1
            if current_chars <= total_chars:
                time.sleep(typing_speed)
        
        # Add a small pause after completing the text
        time.sleep(0.5)
