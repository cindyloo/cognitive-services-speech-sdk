#!/usr/bin/env python
# coding: utf-8



import os
import pyaudio

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

