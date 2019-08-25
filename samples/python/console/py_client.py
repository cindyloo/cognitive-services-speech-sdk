import socket
import pyaudio
import wave
import pickle

#record
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10

HOST = ''    # The remote host
PORT = 50007              # The same port as used by the server

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

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
    client_socket.sendall(data)

#client_socket.send(pickle.dumps(frames))
client_socket.send(b'STOP')
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
client_socket.close()

print("*closed")