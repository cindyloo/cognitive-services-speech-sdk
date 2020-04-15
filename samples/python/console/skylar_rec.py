import speech_recognition as sr
import myspsolution as mysp
from timer import Timer
import time
import json
from skylar_main import listen_and_process, get_voice_prompt

sr.__version__


state = 0
r1 = sr.Recognizer()
r2 = sr.Recognizer()


transcription = []
c=r"./" # Path to the Audio_File directory (Python 3.7)

PAUSE_THRESHOLD_SYLLABLES = 10
#AZURE_SPEECH_KEY = "1ea5ab6891654c78b6d5a40aade2864e"

#timer

def speak(text):
    print(text)
    get_voice_prompt(text)
    #just print for now


def check_volume_and_pace():
    # every 30 seconds capture audio file and analyze volume and pace
    print("not yet evaluating volume and pacing")

# this is called from the background thread
def callback(recognizer, audio):
    # received audio data, now we'll recognize it using Google Speech Recognition
    try:
        # for testing purposes, we're just using the default API key
        print("listener thinks you said " + recognizer.recognize_google(audio))
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


def getResponse(responseFilename, commands):
    got_response = False
    while not got_response:
        try:
            got_response, response, translation = listen_and_process(commands)

            if got_response:
                # store response
                print("analyzing what kind of response")
                #could use the google recognizer here...
                if response in commands:
                    print("got a command")
                    return
                else:
                    print("got a response")
                    got_response = False
                    #store responses/ diarization?
        except EOFError:
            break
    return
"""
        try:
            with my_mic as source:
                audio = r.listen(source)

            transcription = r2.recognize_google(audio)
            print("short term listener")
            print(transcription)
            for res in range(0,len(responses)):
                if responses[res] in transcription:
                    if responses[res] == "wait":
                        timer.sleep(2)
                    elif responses[res] == "repeat":
                        return "repeat"
                    else:
                        no_response_yet = False
                #return a prompt request?

            # determineIntent()
            # how fast slow/ loud/soft pauses
            # promptMode -keywords, phrases
            # per personality
            # storyMode
            mysp.myspgend(responseFilename, c) #mysp solution. what else coudl I use to analyze pauses with audio info
            mysp.mysptotal(responseFilename, c)
        except sr.RequestError:
            # API was unreachable or unresponsive
            response["success"] = False
            response["error"] = "API unavailable"
        except sr.UnknownValueError:
            # speech was unintelligible
            response["error"] = "Unable to recognize speech"

    #stop_listening_cbk(wait_for_stop=False)
"""

def set_baseline():
    #check volume
    #wait, then check again
    print("get baseline")

def introduction(text, commands):
    #text to speech intro
    for i in range(0,1): #len(text)):
        speak(text[i])
       # time.sleep(2)
        #get response?
    getResponse("introduction-response{}.wav",commands)

def instructions(text,responses):
    for i in range(0, len(text)):
        speak(text[i])
      #  time.sleep(2)
    getResponse("instruction-response{}.wav",responses)

def icebreaker(text,responses):
    for i in range(0, len(text)):
        speak(text[i])
        response = getResponse("icebreaker{}.wav".format(i),responses)
        if response == "repeat": #allow for a repeat.
            speak(text[i])
            getResponse("icebreaker{}.wav".format(i), responses)

"""number_ of_syllables      15
gi
rate_of_speech             3
articulation_rate          4
speaking_duration        3.6
original_duration        5.8
balance                  0.6
f0_mean               230.83
f0_std                 60.02
f0_median              216.4
f0_min                    76
f0_max                   422
f0_quantile25            196
f0_quan75                287"""

script = {}
with open("skylar_script.json") as f:
    script = json.load(f)


introduction(script["introduction"]["introductionPrompts"], script["commands"] )


instructions(script["introduction"]["instructionPrompts"], script["commands"])


icebreaker(script["introduction"]["icebreakerPrompts"], script["commands"])


set_baseline()


