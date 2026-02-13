import asyncio
import threading
import edge_tts
from playsound import playsound
import pygame


class Talk:
    def __init__(self, voice="en-US-ChristopherNeural"):
        self.voice = voice
    def play_audio(self,audio_file):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print("error", e)
    async def speak_async(self, text):
        try:
            temp_file = "tts.mp3"
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(temp_file)
            #print("speech saved as mp3")
            self.play_audio(temp_file)
        except Exception as e:
            print("error in talk file", e)




    def say(self, text):
        def run():
            asyncio.run(self.speak_async(text))

        threading.Thread(target=run, daemon=True).start()


def main():
    speaker = Talk("en-US-GuyNeural")
    speaker.say("hello")
    import time
    time.sleep(5)


#main()
