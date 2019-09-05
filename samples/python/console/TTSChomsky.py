'''
After you've set your subscription key, run this application from your working
directory with this command: python TTSSample.py
'''

import os, requests, time
from settings import *



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

class TextToSpeech(object):
    def __init__(self, subscription_key):
        self.subscription_key = subscription_key
        self.tts = ""
        self.timestr = time.strftime("%Y%m%d-%H%M")
        self.access_token = None
        self.response ={}
        self.p = pyaudio.PyAudio()

    '''
    The TTS endpoint requires an access token. This method exchanges your
    subscription key for an access token that is valid for ten minutes.
    '''
    def get_token(self):
        fetch_token_url = "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        self.response = requests.post(fetch_token_url, headers=headers)
        self.access_token = str(self.response.text)


    def fetch_and_save_audio(self, audioText):
        self.tts = audioText
        constructed_url = "https://eastus.voice.speech.microsoft.com/cognitiveservices/v1?deploymentId=" + SPEECH_DEP_ID
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
            'User-Agent': 'Chomsky'
        }

        body = "<speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" xmlns:mstts=\"http://www.w3.org/2001/mstts\" xml:lang=\"en-US\"><voice name=\"test1\">" + self.tts + "</voice></speak>"

        response = requests.post(constructed_url, headers=headers, data=body)
        '''
        If a success response is returned, then the binary audio is written
        to file in your working directory. It is prefaced by sample and
        includes the date.
        '''

        frames = bytearray

        # define callback (2)



        print("now streaming response in Chomsky voice")
        if response.status_code == 200:
            stream = self.p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=28000,
                        output=True,
                        frames_per_buffer=CHUNK)

            stream.write(response.content)
            stream.stop_stream()
            stream.close()
            time(2)

                #client_socket.sendall(data)