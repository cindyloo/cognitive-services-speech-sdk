'''
After you've set your subscription key, run this application from your working
directory with this command: python TTSSample.py
'''

import os, requests, time
from settings import *
from xml.etree import ElementTree
import wave
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 28000
WAVE_OUTPUT_FILENAME = "server_output.wav"
frames = []



try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print("""
    Importing the Speech SDK for Python failed.
    Refer to
    https://docs.microsoft.com/azure/cognitive-services/speech-service/quickstart-python for
    installation instructions.
    """)
    import sys
    sys.exit(1)

SPEECH_DEP_ID =os.getenv("SpeechDeploymentId")
SPEECH_DEP_ID ="f01a58b31ac74b2d882801a61836a1af" #os.getenv("SpeechDeploymentId")

class TextToSpeech(object):
    def __init__(self, subscription_key):
        self.subscription_key = SPEECH_DEP_ID
        self.timestr = time.strftime("%Y%m%d-%H%M")
        self.access_token = None
        self.response ={}

    '''
    The TTS endpoint requires an access token. This method exchanges your
    subscription key for an access token that is valid for ten minutes.
    '''
    def get_token(self):
        fetch_token_url = "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        response = requests.post(fetch_token_url, headers=headers)
        self.access_token = str(response.text)

    def play_audio(self, content):
        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK)

        # write data (based on the chunk size)
        stream.write(content)


        # cleanup stuff.
        stream.close()
        p.terminate()

    def save_audio(self, prompt):
        self.tts = prompt
        base_url = 'https://eastus.tts.speech.microsoft.com/'
        path = 'cognitiveservices/v1'
        constructed_url = base_url + path
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
            'User-Agent': 'Chomsky'
        }
        xml_body = ElementTree.Element('speak', version='1.0')
        xml_body.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-us')
        voice = ElementTree.SubElement(xml_body, 'voice')
        voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-US')
        voice.set(
            'name', 'Microsoft Server Speech Text to Speech Voice (en-US, Guy24kRUS)')
        voice.text = self.tts
        body = ElementTree.tostring(xml_body)

        response = requests.post(constructed_url, headers=headers, data=body)
        if response.status_code == 200:
            with open('skylar-' + self.timestr + '.wav', 'wb') as audio:
                audio.write(response.content)

                print("\nStatus code: " + str(response.status_code) +
                      "\nYour TTS is ready for playback.\n")
            self.play_audio(response.content)
            return True
        else:
            print("\nStatus code: " + str(response.status_code) +
                  "\nSomething went wrong. Check your subscription key and headers.\n")
