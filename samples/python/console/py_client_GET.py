import socket
import pyaudio
import pickle
import websocket
#record
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10

HOST = ''    # The remote host
PORT = 3978              # The same port as used by the server
WEBSOCKET_HOST = 'ws://127.0.0.1:3978/api/messages'


s = websocket.create_connection(WEBSOCKET_HOST)

s.send('Hii')


WAVE_OUTPUT_FILENAME = "client_output.wav"
p = pyaudio.PyAudio()

for i in range(0, p.get_device_count()):
    print(i, p.get_device_info_by_index(i)['name'])


p = pyaudio.PyAudio()
print("open stream...")

frames = []

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print((RATE / CHUNK) * RECORD_SECONDS)

for i in range(0, (RATE // CHUNK * RECORD_SECONDS)):

    data = stream.read(CHUNK, exception_on_overflow=False)
    frames.append(data)
    #r = requests.get(url = WEBSOCKET_HOST, stream=True)
    s.send(pickle.dumps(frames), opcode=websocket.ABNF.OPCODE_BINARY)


print("---done recording---")

###
#waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
#waveFile.setnchannels(CHANNELS)
#waveFile.setsampwidth(p.get_sample_size(FORMAT))
#waveFile.setframerate(RATE)
#waveFile.writeframes(b''.join(frames))
#waveFile.close()

####


stream.stop_stream()
stream.close()
p.terminate()
s.close()

print("*closed")