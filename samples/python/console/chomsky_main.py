#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import intent_sample
import platform

import pyaudio
import wave
import pickle

#record
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10


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

    try:
        # make a stream from the listening port and pass as AudioConfig into recognizer

        # setup the audio stream
        wave_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16,
                                                        channels=1)
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig.fromStreamInput(stream=push_stream)

        p = pyaudio.PyAudio()
        print("open audio stream from client...")

        frames = []
        audio_stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

        print((RATE / CHUNK) * RECORD_SECONDS)

        for i in range(0, (RATE // CHUNK * RECORD_SECONDS)):

            data = audio_stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            # push audio frames into speechSDK stream, something like this
            #push_stream.write(frames);

        #STEP by STEP (step 1: transcribe audio, step 2: send text to bot, step 3: receive answer, step 4: text to speech)

        question_results = intent_sample.recognize_intent_continuous(audio_config)
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

    print()


while True:
    try:
        select()
    except EOFError:
        break
