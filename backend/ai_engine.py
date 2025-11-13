import speech_recognition as sr
import openai
import os

def transcribe_voice(use_online=False):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("\n🎙️ Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        if use_online:
            print("🔗 Using OpenAI Whisper API...")
            with open("temp_audio.wav", "wb") as f:
                f.write(audio.get_wav_data())

            with open("temp_audio.wav", "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
            return transcript["text"]

        else:
            print("🎧 Using offline Google SpeechRecognition...")
            return recognizer.recognize_google(audio)

    except sr.UnknownValueError:
        return "Could not understand your voice."
    except sr.RequestError as e:
        return f"Speech recognition error: {e}"
