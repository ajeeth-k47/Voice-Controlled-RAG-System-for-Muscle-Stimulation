import speech_recognition as sr

def listen_and_transcribe(duration=5):
    """
    Listens to the default microphone and transcribes as soon as the user stops speaking,
    rather than waiting a fixed amount of time.
    """
    recognizer = sr.Recognizer()
    
    try:
        # sr.Microphone() relies on PyAudio to stream from your mic
        with sr.Microphone() as source:
            print("Adjusting for ambient noise... Please wait (0.5s).")
            # Automatically calibrates the energy threshold for silence vs speaking
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            print("Listening... (Speak now!)")
            # timeout: How long to wait for speech to START before giving up
            # phrase_time_limit: Maximum length of speech before cutting off
            audio_data = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            
            print("Audio captured! Sending to SpeechRecognition (Google API) for transcription...")
            # recognize_google is the easiest free backend included in the package
            text = recognizer.recognize_google(audio_data)
            return text
            
    except sr.WaitTimeoutError:
        print("Listening timed out while waiting for you to start speaking.")
        return ""
    except sr.UnknownValueError:
        print("Speech Recognition could not understand the audio.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Speech Recognition service; {e}")
        return ""
    except Exception as e:
        print(f"Error in voice service: {e}")
        return ""
