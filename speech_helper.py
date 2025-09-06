import speech_recognition as sr
import pyttsx3
import threading
import time

class SpeechHelper:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.is_listening = False
        self.is_speaking = False
        self.speech_thread = None
        
        # Configure TTS engine
        self.tts_engine.setProperty('rate', 180)  # Speed of speech
        self.tts_engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
    def start_listening(self):
        """Start listening for voice input"""
        if self.is_listening:
            return None
            
        self.is_listening = True
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
            # Listen for audio
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
                
            # Convert audio to text
            text = self.recognizer.recognize_google(audio)
            self.is_listening = False
            return text
            
        except sr.RequestError:
            self.is_listening = False
            return "Error: Could not connect to speech recognition service"
        except sr.UnknownValueError:
            self.is_listening = False
            return "Error: Could not understand audio"
        except sr.WaitTimeoutError:
            self.is_listening = False
            return "Error: Listening timeout"
        except Exception as e:
            self.is_listening = False
            return f"Error: {str(e)}"
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
    
    def start_speaking(self, text):
        """Start speaking text in a separate thread"""
        if self.is_speaking:
            self.stop_speaking()
            
        self.is_speaking = True
        
        def speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                self.is_speaking = False
            except Exception as e:
                print(f"TTS Error: {e}")
                self.is_speaking = False
        
        self.speech_thread = threading.Thread(target=speak, daemon=True)
        self.speech_thread.start()
    
    def stop_speaking(self):
        """Stop speaking"""
        if self.is_speaking:
            try:
                self.tts_engine.stop()
                self.is_speaking = False
            except:
                pass
    
    def is_currently_listening(self):
        """Check if currently listening"""
        return self.is_listening
    
    def is_currently_speaking(self):
        """Check if currently speaking"""
        return self.is_speaking
