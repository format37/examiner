import pygame
import pyaudio
import wave
import openai
import os
import json
import requests
from datetime import datetime as dt
import time
import pyttsx3
import asyncio
import websockets
import wave


def record_audio(file_name):
    """
    Record audio file from PC microphone
    Until Space key not pressed
    :param file_name: name of audio file
    :return: None
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
                if event.key == pygame.K_SPACE:
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


def tts(engine, tts_text):
    try:
        engine.say(tts_text)
        engine.runAndWait()
    except Exception as e:
        print('tts error while ttsing', tts_text, e)


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


def wait_for_server_be_ready(server_address):
    print(dt.now(), 'waiting for server..')
    r = ''
    while r == '':
        try:
            r = requests.get(server_address+'/test').text
        except Exception as e:
            time.sleep(1)
    print(r)
    print(dt.now(), 'server is ready')


def accept_feature_extractor(phrases, accept):    
    if len(accept)>1 and accept['text'] != '':        
        accept_text = str(accept['text'])                
        # accept_start = str(accept['result'][0]['start'])
        # accept_end = accept['result'][-1:][0]['end']        
        conf_score = []
        for result_rec in accept['result']:
            # print('#', result_rec['conf'], result_rec['start'], result_rec['end'], result_rec['word'])
            conf_score.append(float(result_rec['conf']))
        conf_mid = str(sum(conf_score)/len(conf_score))
        print('=== middle confidence:', conf_mid, '\n')
        phrases.append(accept_text)


async def stt(uri, file_name):

    async with websockets.connect(uri) as websocket:

        phrases = []

        wf = wave.open(file_name, "rb")        
        await websocket.send('{ "config" : { "sample_rate" : %d } }' % (wf.getframerate()))
        buffer_size = int(wf.getframerate() * 0.2) # 0.2 seconds of audio
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

    # get dictionary from text file (config.txt)
    # 1. candidate name
    # 2. candidate role
    # 3. questions count
    with open('config.json', 'r') as f:
        config = json.load(f)

    # paraphrase init
    paraphrase_server = config['paraphrase_server']
    wait_for_server_be_ready(paraphrase_server)

    # textqa init
    textqa_server = config['textqa_server']
    wait_for_server_be_ready(textqa_server)

    # stt server init
    stt_server = config['stt_server']

    # Text to speech init
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-50) # slow down
    engine.setProperty('voice', 'english-us')
    
    # openai init
    prompt = config['prompt']
    stop_words = config['stop_words']

    questions = []
    answers = []
    
    # conversation
    current_question = config['questions_count_limit']
    while int(config['questions_count_limit'])==0 or current_question>0:
        examiner_text = text_davinci(prompt, stop_words)['choices'][0]['text']
        prompt += examiner_text
        questions.append(examiner_text)
        tts(engine, examiner_text)
        # record audio
        record_audio('user.wav')
        # transcribe and receive response
        user_text = asyncio.run(stt(stt_server, 'user.wav'))
        print('user:', user_text)
        answers.append(user_text)
        prompt += '\nCandidate: ' + user_text + '\nHr: '
        current_question -= 1


    # === Evaluate

    # textqa
    text = ' '.join(answers)
    texts = []
    for _ in range(len(questions)):
        texts.append(text)

    request = {'texts':texts,'questions':questions}
    request_str = json.dumps(request)
    response = requests.post(textqa_server+'/inference', json=request_str)
    response = json.loads(response.text)

    for i in range(len(response[0])):
        print(questions[i],'->',response[0][i],'\n')

    # Paraphrases
    text_a = []
    text_b = []
    for i in range(len(response[0])):
        text_a.append(answers[i])
        text_b.append(response[0][i])

    data = {'text_a':text_a,'text_b':text_b}
    request_str = json.dumps(data)
    response = requests.post(paraphrase_server+'/inference', json=request_str)
    paraphrase_eval = string_to_array(response.text)
    
    for i in range(len(paraphrase_eval)):
        print('+' if paraphrase_eval[i] else '-', questions[i], 'answer:')
        print(answers[i],'\n')

    print('Answers length: ',len(text))
    print('Words count: ',len(text.split(' ')))
    print('Unique words count: ',len(set(text.split(' '))))

    correct = int(sum(paraphrase_eval)*100/len(paraphrase_eval))
    examiner_text = 'You have '+str(correct)+' percent of correct answers. '
    print(examiner_text)
    examiner_text += 'Good job!' if correct>=70 else 'You need to improve!'
    tts(engine, examiner_text)

if __name__ == '__main__':
    main()
