import openai
import pyttsx3
import speech_recognition as sr
import time
import datetime
import sys
import os
import boto3
from translate import Translator
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from pydub import AudioSegment
from pydub.playback import play
from pygame import mixer

# API key
openai.api_key = "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"

# TTS engine
engine = pyttsx3.init()

def transcribe_audio_to_text(filename):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="de-DE")
    except sr.UnknownValueError:
        print("Spracherkennung konnte den Text nicht verstehen.")
    except sr.RequestError as e:
        print(f"Fehler bei der Spracherkennung: {str(e)}")
    return ""

def generate_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You: {prompt}"},
            {
                "role": "system",
                "content": f"You: translate to=de text={prompt}",
            },
        ],
        max_tokens=400,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response['choices'][0]['message']['content']

def translate_to_german(text):
    translator = Translator(to_lang="de")
    return translator.translate(text)

def speak_text(text):
    engine.setProperty('voice', 'german')  # Set the voice to a German language voice
    engine.say(text)
    engine.runAndWait()

def main():
    while True:
        # Wait for the user to say "The wake word"
        print("Sage 'Test', um die Aufnahme deiner Frage zu starten...")
        with sr.Microphone() as source:
            recognizer = sr.Recognizer()
            audio = recognizer.listen(source)
            try:
                transcription = recognizer.recognize_google(audio, language="de-DE")
                if transcription.lower() == "test":
                    # Record audio
                    filename = "input.wav"
                    print("Stelle deine Frage...")
                    with sr.Microphone() as source:
                        recognizer = sr.Recognizer()
                        source.pause_threshold = 1
                        audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)
                        with open(filename, "wb") as f:
                            f.write(audio.get_wav_data())

                    # Convert audio to text
                    text = transcribe_audio_to_text(filename)
                    if text:
                        print(f"You said: {text}")

                    # Translate response to German
                    german_response = translate_to_german(text)

                    # Generate response
                    antwort = generate_response(german_response)
                    print(f"{antwort}")

                    session = Session(profile_name="default")
                    polly = session.client("polly")

                    try:
                        # Request speech synthesis
                        response = polly.synthesize_speech(Text=antwort, OutputFormat="mp3", VoiceId="Hans")
                    except (BotoCoreError, ClientError) as error:
                        # The service returned an error, exit gracefully
                        print(error)
                        sys.exit(-1)

                    date_string = time.strftime("%H%M%S")

                    with open(f'speech{date_string}.mp3', 'wb') as f:
                        f.write(response['AudioStream'].read())
                        f = open(f'speech{date_string}.mp3')

                    mixer.init()
                    mixer.music.load(f)
                    mixer.music.play()
                    while mixer.music.get_busy():
                        time.sleep(1)
                    mixer.music.stop
                    mixer.music.unload

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)

if __name__ == "__main__":
    main()