import pygame
import pyaudio
import wave
#import openai
#import os
import json
#import requests
#from datetime import datetime as dt
#import time
#import pyttsx3
import asyncio
import websockets
import wave


def record_audio(file_name, current_question):
    """
    Record audio file from PC microphone
    Until Space key not pressed
    :param file_name: name of audio file
    :return: Escape key pressed
    """

    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    fs = 16000

    p = pyaudio.PyAudio()

    print('Recording')

    escape = False

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []

    recording = True
    while recording:
        data = stream.read(chunk)
        frames.append(data)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    print('Finished recording')

                    stream.stop_stream()
                    stream.close()
                    p.terminate()

                    wf = wave.open(file_name, 'wb')
                    wf.setnchannels(channels)
                    wf.setsampwidth(p.get_sample_size(sample_format))
                    wf.setframerate(fs)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                    recording = False

                    if event.key == pygame.K_ESCAPE:
                        escape = True

                    break

    print('Finished recording')

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(file_name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()

    return escape


def accept_feature_extractor(phrases, accept):
    if len(accept) > 1 and accept['text'] != '':
        accept_text = str(accept['text'])
        """conf_score = []
        for result_rec in accept['result']:
            print(
                '#',
                result_rec['conf'],
                result_rec['start'],
                result_rec['end'],
                result_rec['word']
                )
            conf_score.append(float(result_rec['conf']))"""
        #conf_mid = str(sum(conf_score)/len(conf_score))
        #print('=== middle confidence:', conf_mid, '\n')
        phrases.append(accept_text)


async def stt(uri, file_name):

    async with websockets.connect(uri) as websocket:

        phrases = []

        wf = wave.open(file_name, "rb")
        await websocket.send(
            '{ "config" : { "sample_rate" : %d } }' % (wf.getframerate())
            )
        buffer_size = int(wf.getframerate() * 0.2)  # 0.2 seconds of audio
        while True:
            data = wf.readframes(buffer_size)

            if len(data) == 0:
                break

            await websocket.send(data)
            accept = json.loads(await websocket.recv())
            accept_feature_extractor(phrases, accept)

        await websocket.send('{"eof" : 1}')
        accept = json.loads(await websocket.recv())
        accept_feature_extractor(phrases, accept)

        return ' '.join(phrases)


def string_to_array(result):
    return [int(x) for x in result.split(",")]


def main():
    with open('config.json', 'r') as f:
        config = json.load(f)

    # stt server init
    stt_server = config['stt_server']    

    pygame.init()
    pygame.display.set_mode((100, 100))
    pygame.display.set_caption('Recording')

    # conversation
    while True:
        # record audio
        escape = record_audio('user.wav', 0)
        # transcribe and receive response
        user_text = asyncio.run(stt(stt_server, 'user.wav'))
        print('=== user:', user_text)

        if escape:
            print('Escape pressed')
            break

if __name__ == '__main__':
    main()
