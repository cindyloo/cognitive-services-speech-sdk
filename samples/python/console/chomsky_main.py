#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import intent_sample
import platform


from TTSChomsky import TextToSpeech

import http.client, json, time
import os
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

eofkey = 'Ctrl-Z' if "Windows" == platform.system() else 'Ctrl-D'



def listen_and_process():
    p = pyaudio.PyAudio()


    try:
        intent_recognizer = {}
        listen_mode = True

        def getVoiceAnswerFromText(answerText):
            print("getting voice response")
            app = TextToSpeech(SPEECH_KEY)
            app.get_token()
            app.fetch_and_save_audio(answerText) #write audioResponse as file for now
            # WE need to stop listening during the response b/c guess why - chomsky listens to chomsky output!


        def analyzeTextResponse(answers):
            possible_answers = []
            for a in answers['answers']:
                possible_answers.append({ 'answer': a['answer'], 'score' : a['score']}) # we need the score too
            print("\n\nTOP 3 QNA Responses")
            for p in possible_answers:
                #found it in the model we have, so ...
                print(p['answer'])
            # select top or random?
            print("\n\nTOP QNA ANSWER {}".format(possible_answers[0]))
            return possible_answers[0]['answer']

        def getQNATextResponse(text):
            # api-endpoint
            URL = '/qnamaker/knowledgebases/' + QNA_ID + '/generateAnswer'
            question = {'question': text, 'top': 3}
            # defining a params dict for the parameters to be sent to the API
            headers = {"Authorization": "EndpointKey " + QNA_ENDPOINT,
                       "Content-type": "application/json"}
            try:
                conn = http.client.HTTPSConnection(QNA_HOST)
                json_data = json.dumps(question)
                conn.request("POST", URL, json_data, headers)
                response = conn.getresponse()
                answer = json.loads(response.read().decode())
                return analyzeTextResponse(answer)

            except Exception as e:
                print(e)

            except:
                print ("Unexpected error:", sys.exc_info()[0])
                print ("Unexpected error:", sys.exc_info()[1])

        def grabIntent(evt):
            print("intent")
            #if evt.result.intent_json: #and evt.result.intent_json.top_scoring_intent.score > .50:
                #do some logic on the intent
            info = json.loads(evt.result.intent_json)['topScoringIntent']
            print("TOP LUIS INTENT {} score {}".format(info['intent'], info['score']))
            return ({"intent": info['intent'], "score": info['score']})

        def evaluateScores(luis, qna):
            print('evaluation:: ')
            if (luis['intent'] == 'identification_request'): # and score is high, maybe answer and go to dialog
                print('identification request from LUIS')
            elif (luis['score'] <= .50):
                print('low luis score')
            elif (qna['score'] <= 45):
                print('low qna score')
            print("dispatch to BERT TBD")
            #dispatch or something depending on scores

        def processText(evt):
            print("RECOGNIZED: {}\n\tText: {} (Reason: {})\n\tIntent Id: {}\n\tIntent JSON: {}".format(
                evt, evt.result.text, evt.result.reason, evt.result.intent_id, evt.result.intent_json))
            if evt.result.text in [None, '']:
                print('no text')
                return

            LUIS_score = grabIntent(evt)
            # STEP 3, send to QnA
            QNA_answer = getQNATextResponse(evt.result.text)
            # STEP 4 evaluate LUIS_score and QNA_score to determine if we send to BERT or dispatch to dialog flow
            evaluateScores(LUIS_score, QNA_answer)


            getVoiceAnswerFromText(QNA_answer)
            time.sleep(1)

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

        # STEP 1: listen and transcribe audio
        while not done:
            try:

                intent_recognizer.session_started.connect(lambda evt: print("SESSION_START: {}".format(evt)))

                intent_recognizer.speech_end_detected.connect(lambda evt: print("SPEECH_END_DETECTED: {}".format(evt)))
                # event for intermediate results
                intent_recognizer.recognizing.connect(lambda evt: print("RECOGNIZING: {}".format(evt)))
                # STEP 2: take recognized text and send it on to process
                intent_recognizer.recognized.connect(lambda evt: processText(evt))
                # make a call back to then send text to QnAMaker for response

                intent_recognizer.canceled.connect(
                    lambda evt: print("CANCELED: {} ({})".format(evt.cancellation_details, evt.reason)))

                # stop continuous recognition on session stopped, end of speech or canceled events
                intent_recognizer.session_stopped.connect(stop_cb)
                # intent_recognizer.speech_end_detected.connect(stop_cb)

                #  RUN the intent recognizer. The output of the callbacks should be printed to the console.

                print("start listening")
                intent_recognizer.start_continuous_recognition()


                print("test for done")
                test_for_user_end(done)

            except Exception as e:
                print(e)
                break


    except Exception as e:
        print('Error running sample: {}'.format(e))



while True:
    try:
        listen_and_process()
    except EOFError:
        break
