#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import intent_sample
import platform
import asyncio
import wave
import numpy

from TTSChomsky import TextToSpeech

import http.client, json, time
import os
from settings import *

from google.cloud import speech_v1p1beta1 as speech
import speech_recognition as sr
    # If you don't specify credentials when constructing the client, the
    # client library will look for credentials in the environment.



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


def get_voice_prompt(prompt): #using MS Azure
    print("getting skylar voice prompt")
    app = TextToSpeech(SPEECH_KEY)
    app.get_token()
    app.save_audio(prompt)  # write audioResponse as file for now
    # WE need to stop listening during the response b/c guess why - chomsky listens to chomsky output!
    # return something like True, "speaking", audioFile

def speaker_diarization_setup(frame_data): #using Google speech
    print("diarization")
    bytes_from_stream = []

    r = sr.Recognizer()
    #what form works?
    audio = bytes(b''.join(frame_data))

    client = speech.SpeechClient()

    if audio not in [None]:
        audio = speech.types.RecognitionAudio(content=audio)
        config = speech.types.RecognitionConfig(
            encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code='en-US',
            enable_speaker_diarization=True,
            enable_automatic_punctuation=True,
            diarization_speaker_count=4)
        print('Waiting for DIARIZation operation to complete…')
        response = client.recognize(config, audio)
        # The transcript within each result is separate and sequential per result.
        # However, the words list within an alternative includes all the words
        # from all the results thus far. Thus, to get all the words with speaker
        # tags, you only have to take the words list from the last result:
        if len(response.results) > 0:
            result = response.results[-1]
            words_info = result.alternatives[0].words
            speaker1_transcript = ""
            speaker2_transcript = ""
            speaker3_transcript = ""
            speaker4_transcript = ""
            # Printing out the output:
            for word_info in words_info:
                if (word_info.speaker_tag == 1): speaker1_transcript = speaker1_transcript + word_info.word + ' '
                if (word_info.speaker_tag == 2): speaker2_transcript = speaker2_transcript + word_info.word + ' '
                if (word_info.speaker_tag == 3): speaker3_transcript = speaker3_transcript + word_info.word + ' '
                if (word_info.speaker_tag == 4): speaker4_transcript = speaker4_transcript + word_info.word + ' '

            print("speaker1: '{}'".format(speaker1_transcript))
            print("speaker2: '{}'".format(speaker2_transcript))
            print("speaker3: '{}'".format(speaker3_transcript))
            print("speaker4: '{}'".format(speaker4_transcript))

#main process
#start Azure STT recognizer and analyze responses
def listen_and_process(command_responses):
    p = pyaudio.PyAudio()
    global done
    global translation
    translation = None
    done = False
    global user_intent_response
    global user_command_response
    user_command_response = ''
    user_intent_response = ''


    try:
        intent_recognizer = {}
        listen_mode = True
        loop = asyncio.get_event_loop()

        def analyzeTextResponse(answers):
            print("no voice analysis yet")
            # audience said something (not a command)
             # analyze intent
            # do something with intent?


        #parse command and send back command
        def checkForCommands(res):
            if "wait" in res.lower():
                timer.sleep(2)
            elif "next" in res.lower():
                return True, "next"
            elif "proceed" in res.lower():
                return True, "next"
            elif "repeat" in res.lower():
                return True, "repeat"
            elif "quit" in res.lower():
                return True, "quit"
            elif "stop" in res.lower():
                return True, "quit"
            else:
                return False, ""


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

            #dispatch or something depending on scores
        def processCommand():
            # handle script
            print("script is responding to command")
            return

        #callback for Recognized text #MS Azure
        def processText(evt):
            print("RECOGNIZED: {}\n\tText: {} (Reason: {})\n\tIntent Id: {}\n\tIntent JSON: {}".format(
                evt, evt.result.text, evt.result.reason, evt.result.intent_id, evt.result.intent_json))
            if evt.result.text in [None, '']:
                print('no text')
                return

            global command
            global user_command_response
            has_command, user_command_response = checkForCommands(evt.result.text)
            global translation
            translation = evt.result.text
            if has_command:
                print("has command, stopping")
                global done
                done = True
            else:
                LUIS_score = grabIntent(evt)
                global user_intent_response
                user_intent_response = LUIS_score['intent']
                # STEP 3, send to QnA
                analyzed_answer = analyzeTextResponse(evt.result.text, LUIS_score)
                # STEP 4 evaluate LUIS_score and QNA_score to determine if we send to BERT or dispatch to dialog flow
                evaluateScores(LUIS_score, analyzed_answer)
            return

        # make a stream from the listening port and pass as AudioConfig into recognizer  #MS Azure
        class StreamingAudioCallback(speechsdk.audio.PullAudioInputStreamCallback):
            """Example class that implements the Pull Audio Stream interface to recognize speech from
            an audio stream"""
            def __init__(self):
                super().__init__()

                self.pa = pyaudio.PyAudio()
                print("open pyaudio stream from client...")
                self.audio_stream = self.pa.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK)

                print((RATE / CHUNK) * RECORD_SECONDS)

                self.frames = []
                self.numpydata = []

            def read(self, buffer: memoryview) -> int:
                    for i in range(0, RATE // CHUNK * RECORD_SECONDS):
                        data = self.audio_stream.read(CHUNK)
                        self.frames.append(data)
                        buffer[:len(data)] = data
                        return len(data)


            def close(self):
                """close callback function"""
                self._file_h.close()


        # setup the audio stream
        wave_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
        callback = StreamingAudioCallback()
        push_stream = speechsdk.audio.PullAudioInputStream(callback, wave_format)

        def cancelled_cb(evt):
            """callback that stops continuous recognition upon receiving an event `evt`"""
            print('CANCELLING on {}'.format(evt))

        def stop_cb(evt):
            """callback that signals to stop continuous recognition upon receiving an event `evt`"""
            print('CLOSING-evt{}'.format(evt))
            return False

        def test_for_command_done(done):
            return done


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
            (model, "instructionCommand")
        ]
        intent_recognizer.add_intents(intents)

        # STEP 1: listen and transcribe audio

        try:

            intent_recognizer.session_started.connect(lambda evt: print("SESSION_START: {}".format(evt)))

            intent_recognizer.speech_end_detected.connect(lambda evt: print("SPEECH_END_DETECTED: {}".format(evt)))
            # event for intermediate results
            intent_recognizer.recognizing.connect(lambda evt: print("RECOGNIZING: {}".format(evt)))
            # STEP 2: take recognized text and send it on to process
            intent_recognizer.recognized.connect(lambda evt: processText(evt))
            # make a call back to analyze text

            intent_recognizer.canceled.connect(cancelled_cb)

            # stop continuous recognition on session stopped, end of speech or canceled events
            intent_recognizer.session_stopped.connect(stop_cb)

            #  RUN the intent recognizer. The output of the callbacks should be printed to the console.
            print("start listening")

            intent_recognizer.recognize_once()
           # response = input()
            print("test for command or intent")

            retval = user_command_response or user_intent_response
            saved_recording_filename = 'audience-' + time.strftime("%Y%m%d-%H%M") + '.wav'
            #don't save if a command.. append file?
            if retval != user_command_response:
                speaker_diarization_setup(callback.frames)
            #save audio file for diarization
                wf = wave.open(saved_recording_filename, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(callback.frames))




            #return these values for additional processing. TODO somehting with user_intent_response
            return retval, user_command_response or user_intent_response, translation, saved_recording_filename

        except Exception as e:
            print("Error ")
            print(e)

        print("END")
        return
    except Exception as e:
        print('Error running sample: {}'.format(e))

    return
"""
while True:
    try:
        listen_and_process()
    except EOFError:
        break
"""