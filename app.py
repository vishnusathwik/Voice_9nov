import pyttsx3
import os
import requests
from flask import Flask, render_template, request, redirect, url_for
import pyttsx3
app = Flask(__name__)
app.static_folder = 'static'
from flask import request
import time
import re
import pyttsx3
from pydub import AudioSegment
import os
API_KEY_ASSEMBLYAI = '72c174b7c3ef4a41aacc90ac1a83783f'
upload_endpoint = 'https://api.assemblyai.com/v2/upload'
transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'

headers_auth_only = {'authorization': API_KEY_ASSEMBLYAI}

headers = {
    "authorization": API_KEY_ASSEMBLYAI,
    "content-type": "application/json"
}

CHUNK_SIZE = 5_242_880  # 5MB
def upload(filename):
    def read_file(filename):
        with open(filename, 'rb') as f:
            while True:
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
                yield data

    upload_response = requests.post(upload_endpoint, headers=headers_auth_only, data=read_file(filename))
    return upload_response.json()['upload_url']


def transcribe(audio_url):
    transcript_request = {
        'audio_url': audio_url
        #/transcript_id
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
    return transcript_response.json()['id']

        
def poll(transcript_id):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    polling_response = requests.get(polling_endpoint, headers=headers)
    return polling_response.json()
    
def get_transcription_result_url(url):
    transcribe_id = transcribe(url)
    while True:
        data = poll(transcribe_id)
        if data['status'] == 'completed':
            return data, None
        elif data['status'] == 'error':
            return data, data['error']
        time.sleep(5)
        
        
def save_transcript(url, title):
    data, error = get_transcription_result_url(url)
    
    if data:
        filename = title + '.txt'
        with open(filename, 'w') as f:
            f.write(data['text'])
        print('Transcript saved')
    elif error:
        print("Error!!!", error)

@app.route('/s2t')
def s2t():
    return render_template('s2t.html')

@app.route('/chats2t', methods=['GET', 'POST'])
def chats2t():
    if request.method == 'POST':
        global users
        users = extract_user_names('temp_whatsapp.txt')

        file = request.files['file']
        if file.filename != '':
            file.save('temp_audio.mp3')

            # Upload and transcribe the audio file
            audio_url = upload('temp_audio.mp3')
            save_transcript(audio_url, 'transcript')
            parse('transcript.txt')
            return redirect('/result') 
    return render_template('chats2t.html')

@app.route('/normals2t', methods=['GET', 'POST'])
def normals2t():
    if request.method == 'POST':
        # Handle file upload
        file = request.files['file']
        if file.filename != '':
            # Save uploaded audio file temporarily
            file.save('temp_audio.mp3')

            # Upload and transcribe the audio file
            audio_url = upload('temp_audio.mp3')
            save_transcript(audio_url, 'transcript')
            return redirect('/result2')  # Redirect to the result page

    return render_template('normals2t.html')

@app.route('/result')
def result():
    # Read and display the saved transcript
    with open('transcript.txt', 'r') as f:
        transcript = f.read()
    with open('formatted_transcript.txt', 'r') as f:
        formattedtxt = f.read()
    return render_template('result.html', transcript=transcript,formatted = formattedtxt)

@app.route('/result2')
def result2():
    # Read and display the saved transcript
    with open('transcript.txt', 'r') as f:
        transcript = f.read()
    return render_template('result2.html', transcript=transcript)

output_directory = 'audio'
output_audio_file = os.path.join(output_directory, 'combined_audio.mp3')
chat_file='temp_whatsapp.txt'

# Define global variables to store user data and voices
users = []
selected_voices = []
engine = pyttsx3.init()
voices = engine.getProperty('voices')
print(voices)
def extract_user_names(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    user_names = set()
    for line in lines:
        if line.startswith('User:'):
            user_name = line.split(':')[1].strip()
            user_names.add(user_name)
    
    return list(user_names)

def convert_conversation_format(filepath):
    flag_filepath = f'formatting_flag{filepath}.txt'
    '''if os.path.exists(flag_filepath):
        print("The conversation has already been formatted.")
        return'''

    # Read the content of the file
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    converted_lines = []
    for line in lines:
        parts = line.split(' - ')
        if len(parts) >= 2:
            timestamp, message = parts[0], parts[1]
            if ':' in message:
                user = message.split(': ')[0]
                message = message.split(': ')[1].strip()
                converted_line = f"User: {user}\nMessage: {message}\n"
                converted_lines.append(converted_line)

    with open(filepath, 'w', encoding='utf-8') as file:
        file.writelines(converted_lines)

    with open(flag_filepath, 'w'):
        pass

@app.route('/')
def main(): 
    return render_template('main.html')

@app.route('/t2s', methods=['GET', 'POST'])
def t2s():
    print(1)
    if request.method == 'POST':
        # Handle WhatsApp file upload
        file = request.files['file']

        if file.filename != '':
            file.save('temp_whatsapp.txt')

            # Format the uploaded file
            convert_conversation_format('temp_whatsapp.txt')

            # Extract user names from the WhatsApp file
            global users
            users = extract_user_names('temp_whatsapp.txt')
            print(users)
        return redirect('/options')  # Redirect to options page

    return render_template('t2s.html')

@app.route('/options')
def options():
    return render_template('options.html')

@app.route('/view_users')
def view_users():
    # Implement code to show users in chat (Option 1)
    return render_template('view_users.html',users=users)

@app.route('/show_voices')
def show_voices():
    # Implement code to show voices on the device (Option 2)
    return render_template('view_voices.html',voices=voices)

@app.route('/assign_voices', methods=['GET', 'POST'])
def assign_voices():
    if request.method == 'POST':
        # Handle form submission and map users to their assigned voices
        user_voice_map = {}
        for user in users:
            assigned_voice_id = request.form.get(user)
            print(assigned_voice_id)
            user_voice_map[user] = assigned_voice_id
        print(user_voice_map)
        generate_speech(chat_file,user_voice_map,'audio2')

    return render_template('select_voices.html', users=users, voices=voices)
def parse(filename):
    global users
    users = extract_user_names('temp_whatsapp.txt')
    with open(filename, 'r', encoding='utf-8') as file:
        contents = file.read()
    transcript=contents
# Define a regex pattern to detect user names
    user_pattern = re.compile(r'\b(?:' + '|'.join(users) + r')\b')

    # Find all occurrences of user names in the transcript
    user_occurrences = user_pattern.finditer(transcript)

    # Initialize variables to keep track of the last message end index and user
    last_message_end = 0
    last_user = None

    parsed_messages = []

    for match in user_occurrences:
        user = match.group(0)
        v = len(user)
        user_index = match.start()

        message = transcript[last_message_end+v:user_index].strip()

        if message:
            parsed_messages.append(f"{last_user}: {message}")

        last_message_end = user_index
        last_user = user

    # Process the last message
    last_message = transcript[last_message_end+len(user):].strip()
    if last_message:
        parsed_messages.append(f"{last_user}: {last_message}")

    # Print parsed messages
    '''for parsed_message in parsed_messages:
        print(parsed_message)'''
    with open('formatted_transcript.txt', 'w') as file:
        for parsed_message in parsed_messages:
            file.write(parsed_message + '\n')

        

def generate_speech(chat_file, voice_map, output_folder):
    # Initialize the TTS engine
    engine = pyttsx3.init()

    current_user = None
    current_message = ""
    audio_file_count = 1
    engine.setProperty('rate', 150)

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with open(chat_file, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("User:"):
            user = line.split(':')[1].strip()
            # Save the previous user's message and set the current user
            if current_user and current_message:
                voice = voice_map.get(current_user)
                if voice:
                    engine.setProperty("voice", voice)
                    audio_file_name = f"{output_folder}/{audio_file_count}.mp3"
                    engine.save_to_file(current_user+current_message, audio_file_name)
                    audio_file_count += 1
            current_message = ""
            current_user = user
        elif line.startswith("Message:"):
            current_message += line.split(": ")[1] + " "

    # Save the last user's message
    if current_user and current_message:
        voice = voice_map.get(current_user)
        if voice:
            engine.setProperty("voice", voice)
            audio_file_name = f"{output_folder}/{audio_file_count}.mp3"
            engine.save_to_file(current_message, audio_file_name)

    # Run the TTS engine to generate the audio files
    engine.runAndWait()    
    combine_audio_files(output_folder,'combined.mp3')


import wave
import os

def combine_audio_files(output_folder, output_filename):
    # Get a list of audio files in the output folder
    audio_files = [f for f in os.listdir(output_folder) if f.endswith(".mp3")]

    # Sort the audio files based on their filenames
    audio_files.sort(key=lambda x: int(os.path.splitext(x)[0]))

    # Initialize an empty Wave_write object for the combined audio
    combined_audio = wave.open(os.path.join("static", output_filename), 'wb')  # Save in templates folder

    # Initialize parameters based on the first audio file
    first_audio_file = os.path.join(output_folder, audio_files[0])
    with wave.open(first_audio_file, 'rb') as first_audio:
        combined_audio.setparams(first_audio.getparams())

    # Iterate through the sorted audio files and append their data to the combined audio
    for filename in audio_files:
        audio_file_path = os.path.join(output_folder, filename)
        with wave.open(audio_file_path, 'rb') as audio_file:
            combined_audio.writeframes(audio_file.readframes(audio_file.getnframes()))

    # Close the combined audio file
    combined_audio.close()

import pyaudio
import wave

def microphone():
    FRAMES_PER_BUFFER = 3200
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()

    # starts recording
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER
    )

    print("Start recording...")

    frames = []
    seconds = 10
    for i in range(0, int(RATE / FRAMES_PER_BUFFER * seconds)):
        data = stream.read(FRAMES_PER_BUFFER)
        frames.append(data)

    print("Recording stopped")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open("output.wav", 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

@app.route('/record_audio', methods=['GET', 'POST'])
def record_audio():
    if request.method == 'POST':
        # Call the microphone function to record audio
        microphone()
        audio_url = upload('output.wav')
        save_transcript(audio_url, 'transcript')
        return redirect('/result2')  # Redirect to the result page
    return render_template('record_audio.html')  # Create an HTML template for the recording page


if __name__ == '__main__':
    app.run(debug=True)







