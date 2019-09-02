#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import intent_sample
import platform

import pyaudio
from TTSChomsky import TextToSpeech

import http.client, urllib.parse, json, time, sys
import os

#record
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 20


from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

LU_APP_ID = os.getenv("LuisAppId")
LU_API_KEY = os.getenv("LuisAPIKey")
LU_SERVICE_REGION = "eastus" #os.getenv("LuisAPIHostName")


QNA_HOST = os.getenv("QnAEndpointHostName")
QNA_ID = os.getenv("QnAKnowledgebaseId")
QNA_ENDPOINT = os.getenv("QnAEndpointKey")


SPEECH_KEY = os.getenv("SpeechServiceKey")
speech_intent_service_region =os.getenv("SpeechRegion")


# Specify the path to a audio file containing speech (mono WAV / PCM with a sampling rate of 16
# kHz).


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

eofkey = 'Ctrl-Z' if "Windows" == platform.system() else 'Ctrl-D'

intent_samples = [
        intent_sample.recognize_intent_once_from_mic,
        intent_sample.recognize_intent_once_async_from_mic,
        intent_sample.recognize_intent_continuous
]


def select():
    p = pyaudio.PyAudio()

    try:
        intent_recognizer = {}

        def getVoiceAnswerFromText(answerText):
            print("get voice response")
            app = TextToSpeech(SPEECH_KEY)
            app.get_token()
            app.fetch_and_save_audio(answerText) #write audioResponse as file for now

        def analyzeResponse(answers):
            possible_answers = []
            for a in answers['answers']:
                possible_answers.append(a['answer'])
            for p in possible_answers:
                #found it in the model we have, so ...
                print(p)
            # select top or random?
            print("top answer {}".format(possible_answers[0]))
            return possible_answers[0]

        def getResponse(text):
            # api-endpoint
            URL = '/qnamaker/knowledgebases/' + QNA_ID + '/generateAnswer'
            print(QNA_ID)
            question = {'question': text, 'top': 3}
            # defining a params dict for the parameters to be sent to the API
            headers = {"Authorization": "EndpointKey " + QNA_ENDPOINT,
                       "Content-type": "application/json"}
            try:
                conn = http.client.HTTPSConnection(QNA_HOST)
                print("send request")
                json_data = json.dumps(question)
                conn.request("POST", URL, json_data, headers)
                response = conn.getresponse()
                print("got response")
                answer = json.loads(response.read().decode())
                return analyzeResponse(answer)

            except Exception as e:
                print(e)

            except:
                print ("Unexpected error:", sys.exc_info()[0])
                print ("Unexpected error:", sys.exc_info()[1])

        def analyzeIntent(evt):
            print("analyzing intent")
            if evt.result.intent_json and evt.result.intent_json.top_scoring_intent.score > .50:
                #found it in the model we have, so ...
                print("will call qnamaker")


        def processText(evt):
            print("RECOGNIZED: {}\n\tText: {} (Reason: {})\n\tIntent Id: {}\n\tIntent JSON: {}".format(
                evt, evt.result.text, evt.result.reason, evt.result.intent_id, evt.result.intent_json))
            if evt.result.text in [None, '']:
                print('no text')
                return
            #analyzeIntent(evt)
            print("text{}".format(evt.result.text))
            answer = getResponse(evt.result.text)
            #send prepareTTSpeech(answer)
            getVoiceAnswerFromText(answer)

        # make a stream from the listening port and pass as AudioConfig into recognizer
        class StreamingAudioCallback(speechsdk.audio.PullAudioInputStreamCallback):
            """Example class that implements the Pull Audio Stream interface to recognize speech from
            an audio stream"""
            def __init__(self):
                super().__init__()

                print("open audio stream from client...")
                self.audio_stream = p.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK)

                print((RATE / CHUNK) * RECORD_SECONDS)

            def read(self, buffer: memoryview) -> int:
                #frames = bytearray
                for i in range(0, (RATE // CHUNK * RECORD_SECONDS)):
                    data = self.audio_stream.read(CHUNK)
                    buffer[:len(data)] = data

                    return len(data)

            def close(self):
                """close callback function"""
                self._file_h.close()


        # setup the audio stream
        wave_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)

        callback = StreamingAudioCallback()
        push_stream = speechsdk.audio.PullAudioInputStream(callback, wave_format)
        # setup the audio stream
        #push_stream = speechsdk.audio.PushAudioInputStream()


        done = False
        def stop_cb(evt):
            """callback that stops continuous recognition upon receiving an event `evt`"""
            print('CLOSING on {}'.format(evt))
            intent_recognizer.stop_continuous_recognition()
            done = True

        def test_for_user_end(done):
            time.sleep(10)
            response = input()
            if response == 's':
                stop_cb('user end')
                done = True
            return



        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
        # step 1: transcribe audio
        print("set up speech keys")
        intent_config = speechsdk.SpeechConfig(subscription=LU_API_KEY, region="eastus")
        intent_recognizer = speechsdk.intent.IntentRecognizer(speech_config=intent_config, audio_config=audio_config)

        print("set up model")
        # set up the intents that are to be recognized. These can be a mix of simple phrases and
        # intents specified through a LanguageUnderstanding Model.
        model = speechsdk.intent.LanguageUnderstandingModel(app_id=LU_APP_ID)
        intents = [
            (model, "greeting"),
            (model, "identification"),
            (model, "identification_request"),
            (model, "location_request")
        ]
        intent_recognizer.add_intents(intents)

# cancellation event

        while not done:
            try:

                intent_recognizer.session_started.connect(lambda evt: print("SESSION_START: {}".format(evt)))

                intent_recognizer.speech_end_detected.connect(lambda evt: print("SPEECH_END_DETECTED: {}".format(evt)))
                # event for intermediate results
                intent_recognizer.recognizing.connect(lambda evt: print("RECOGNIZING: {}".format(evt)))
                # event for final result
                intent_recognizer.recognized.connect(lambda evt: processText(evt))
                # make a call back to then send text to QnAMaker for response

                intent_recognizer.canceled.connect(
                    lambda evt: print("CANCELED: {} ({})".format(evt.cancellation_details, evt.reason)))

                # stop continuous recognition on session stopped, end of speech or canceled events
                intent_recognizer.session_stopped.connect(stop_cb)
                # intent_recognizer.speech_end_detected.connect(stop_cb)

                #  RUN the intent recognizer. The output of the callbacks should be printed to the console.
                intent_recognizer.start_continuous_recognition()


                print("test for done")

                test_for_user_end(done)

            except Exception as e:
                print(e)
                break


        # STEP by STEP (step 3: receive answer, step 4: text to speech)





        # we will receive the threshold, and the text transcription
        # now run logic to send to Bot (QnAmaker or BERT)
        #dummy_response_results = question_results # TODO, change when BOT gives us a response
        #response_results = generate_response(dummy_response_results)
        #app = TextToSpeech(subscription_key, response_results.input_json)
        # send back to client in stream.write()
        #app.get_token()
        #app.save_audio()

    except Exception as e:
        print('Error running sample: {}'.format(e))



while True:
    try:
        select()
    except EOFError:
        break
