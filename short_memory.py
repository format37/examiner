from dataclasses import replace
from multiprocessing.connection import wait
import pygame
import pyaudio
import wave
import openai
import os
import json
import requests
from datetime import datetime as dt
import time
#import pyttsx3
import asyncio
import websockets
import wave


def wait_for_server(definition, address):
    print('Wait for '+definition+' server..')
    while True:
        try:
            answer = requests.get(address)
            if answer.status_code == 200 and answer.text == 'ok':
                print(dt.now(), definition+' is ready!')
                break
        except Exception as e:
            pass
        time.sleep(1)

def record_audio(file_name):    
    """
    Record audio file from PC microphone
    Until Space key not pressed
    :param file_name: name of audio file
    :return: Escape key pressed
    """
    pygame.init()
    pygame.display.set_mode((100, 100))
    pygame.display.set_caption('Recording')

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


def tts(tts_server, tts_text):
    data={'text': tts_text}
    request_str = json.dumps(data)
    response = requests.post(tts_server+'/inference', json=request_str)
    # Save response as audio file
    with open("audio.wav", "wb") as f:
        f.write(response.content)
    # Play audio file
    pygame.mixer.init()
    pygame.mixer.music.load("audio.wav")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def text_davinci(prompt, stop_words):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    return json.loads(str(openai.Completion.create(
      engine="text-davinci-002",
      prompt=prompt,
      temperature=0.9,
      max_tokens=150,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0.6,
      stop=stop_words
    )))


def wait_for_server_be_ready(server_address, name):
    print(dt.now(), 'waiting for '+name+' server..')
    r = ''
    while r == '':
        try:
            r = requests.get(server_address+'/test').text
        except Exception as e:
            time.sleep(1)
    print(r)
    print(dt.now(), 'server is ready')


def accept_feature_extractor(phrases, accept):
    if len(accept) > 1 and accept['text'] != '':
        accept_text = str(accept['text'])
        conf_score = []
        for result_rec in accept['result']:
            """print(
                '#',
                result_rec['conf'],
                result_rec['start'],
                result_rec['end'],
                result_rec['word']
                )"""
            conf_score.append(float(result_rec['conf']))
        conf_mid = str(sum(conf_score)/len(conf_score))
        print('=== middle confidence:', conf_mid, '\n')
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
    if (os.getenv("OPENAI_API_KEY") is None):
        print("# error: OPENAI_API_KEY is not set")
        return

    with open('config.json', 'r') as f:
        config = json.load(f)

    tts_server = config['tts_server']
    wait_for_server_be_ready(tts_server, 'tts')

    # stt server init
    stt_server = config['stt_server']   

    # openai init
    stop_words = config['stop_words']
    prompt = config['prompt']
    # print(prompt)
    prompt_len = len(prompt.split('\n'))

    while True:
        print('=== ===', dt.now(), 'prompt:\n', prompt)
        # record audio
        escape = record_audio('user.wav')
        # convert ogg to wav
        # os.system('ffmpeg -i user.ogg -ac 1 -ar 16000 user.wav -y')        
        # transcribe and receive response
        user_text = asyncio.run(stt(stt_server, 'user.wav'))        
        prompt += '\n'+stop_words[0]+' ' + user_text + '\n'+stop_words[1]+' '
        if escape:
            print('Escape pressed')
            break
        # split prompt by strings
        prompt_array = prompt.split('\n')
        #print('array:', prompt_array)        
        if len(prompt_array) > prompt_len+3:
            # remove all elements from prompt, except first element and last 3 elements
            prompt_array = [prompt_array[0]] + prompt_array[-(prompt_len+3-1):]
        # restore promt from prompt_array
        prompt = '\n'.join(prompt_array)        
        examiner_text = text_davinci(str(prompt), stop_words)['choices'][0]['text']
        # replace \n to ''
        prompt += examiner_text.replace('\n', '')
        tts(tts_server, examiner_text)
        
    print('=== ===', dt.now(), 'prompt:\n', prompt)
    

if __name__ == '__main__':
    main()
