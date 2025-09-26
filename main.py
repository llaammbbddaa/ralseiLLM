#!/usr/bin/env python3

# ideally this script allows for a connection to be made from custom ollama model to the ralsei cli tool

from chatbox import ChatboxRenderer
import subprocess
from time import sleep

# takes in string prompt, converts it to usable list, and sends it as command to save output
def stringToCmd(command):
	command = "ollama run ralseiModel '" + command + "'"
	cmd = command.split()
	res = subprocess.run(cmd, capture_output=True, text=True)
	return res.stdout

# finds the earliest occurence of one of the emotions and returns that emotion value
def grabEmotion(response):
	emotions = ["happy", "sad", "surprised", "mad"]
	minIndex = len(response)      # start with a big index

	for i in emotions:
		idx = response.find(i)
		if idx != -1 and idx < minIndex:
			minIndex = idx
			foundEmotion = i

	# removes the emotion text, doesnt need to be there, cringe enough as it is
	response = response[4 + len(foundEmotion):]

	# returning as list because both response and emotion are needed as inputs or the chatbox
	return [response, emotions[minIndex]]

ralsei = ChatboxRenderer()
command = input("enter phrase >> ")
prompt = grabEmotion(stringToCmd(command))

print(prompt[1])
sleep(5)

ralsei.display(prompt[0], prompt[1])
