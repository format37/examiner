import sys
from deeppavlov import build_model, configs
import speech_recognition as sr
import pyttsx3
import random
import datetime
import requests
import time
import pickle


def stt(r, source):
    try:
        print("# listening..")
        audio = r.listen(source)
        print("# ok..")
        text_input =  r.recognize_google(audio)
        print('Username:', text_input)
    except Exception as e:
        print('error:', e)
        return 'nothing to answer'
    return text_input


def tts(engine, tts_text):
    try:
        engine.say(tts_text)
        engine.runAndWait()
    except Exception as e:
        print('tts error while ttsing', tts_text, e)


def main():
    
    use_gpt = len(sys.argv)==2 and sys.argv[1]=='gpt'
    if use_gpt:
        # Connect to GPT server
        print('# To use DialoGPT feature, GPT server should be started. GPT server can be installed from:')
        print('# https://github.com/format37/DialoGPT')
        # Wait for DialoGPT service to be ready
        while True:
            try:
                answer = requests.get('http://localhost:8083/test')
                if answer.status_code == 200 and answer.text == 'ok':
                    print(datetime.datetime.now(), 'DialoGPT is ready!')
                    break
            except Exception as e:
                pass
            print(datetime.datetime.now(), 'Waiting for DialoGPT service to be ready..')
            time.sleep(1)
    else:
        print(sys.argv)
        exit()

    
    qa = build_model(configs.squad.squad, download=False)
    config = 'paraphraser_bert'
    paraphraser = build_model(config, download=False)

    # Microphone test
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
    if index>1:
        print('Please, input the selected microphone index: ')
        selected_mic = int(input())
    else:
        selected_mic = 0
    #selected_mic = 0

    # Text to speech init
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-60) # slow down
    engine.setProperty('voice', 'english-us')
    #engine.setProperty('voice', 'russian')

    """print('available voices:')
    for voiceid in engine.getProperty('voices'):
        print(voiceid)"""



    # Read questions
    with open('questions.txt') as f:
        questions = f.readlines()
    for i in range(len(questions)):
        questions[i] = questions[i].replace('\n','')
    random.shuffle(questions)

    answers = []
    chat_history = ''

    # debug ++
    #chat_history += '|0|1|' + 'How are you'
    #print('GPT: ',requests.post('http://localhost:8083/gpt', chat_history).text)
    # debug --    

    r = sr.Recognizer()
    with sr.Microphone(selected_mic) as source:
        examiner_text = "Hello Username! How are you doing?"
        tts(engine, examiner_text)
        chat_history += '|1|1|' + examiner_text
        username_text = stt(r, source)
        chat_history += '|0|1|' + username_text

        examiner_text = "Great! Lets get started. Now i will ask you several questions. First. "
        for question_id in range(len(questions)):
            examiner_text += questions[question_id]            
            tts(engine, examiner_text)
            #chat_history += '|1|1|' + examiner_text
            chat_history = '|1|1|' + examiner_text
            
            username_text = stt(r, source)
            answers.append(username_text)
            #chat_history += '|0|1|' + username_text
            if use_gpt:
                try:                
                    chat_history += '|0|1|' + username_text
                    # robot phrase                
                    result = requests.post('http://localhost:8083/gpt', chat_history.replace('’',''))
                    with open('data.pkl', 'wb') as fp:
                        pickle.dump(result, fp)
                    with open('chat_history.txt', 'w') as f:
                        f.write(chat_history.replace('’',''))
                    #examiner_text = 'test'
                    examiner_text = result.text
                    if not examiner_text=='':
                        chat_history += '|1|1|' + examiner_text
                        print('examiner:', examiner_text)
                        tts(engine, examiner_text)
                        # username phrase
                        username_text = stt(r, source)
                        chat_history += '|0|1|' + username_text
                except Exception as e:
                    print('gpt error:', e)
            examiner_text = ''

        tts(engine, "That's all")

    # Evaluate
    text = ' '.join(answers)
    texts = []
    for _ in range(len(questions)):
        texts.append(text)

    request = {'texts':texts,'questions':questions}
    response = qa(request['texts'], request['questions'])

    for i in range(len(response[0])):
        print(questions[i],'->',response[0][i],'\n')

    # Paraphrases
    text_a = []
    text_b = []
    for i in range(len(response[0])):
        text_a.append(answers[i])
        text_b.append(response[0][i])

    paraphrase_eval = paraphraser(text_a,text_b)

    for i in range(len(paraphrase_eval)):
        print('+' if paraphrase_eval[i] else '-', questions[i], 'answer:')
        print(answers[i],'\n')

    print('Answers length: ',len(text))
    print('Words count: ',len(text.split(' ')))
    print('Unique words count: ',len(set(text.split(' '))))

    correct = int((len(paraphrase_eval[paraphrase_eval==1])*100/len(paraphrase_eval)))
    examiner_text = 'You have '+str(correct)+' percent of correct answers. '
    print(examiner_text)
    examiner_text += 'Welcome aboard!' if correct>=70 else 'You spend my time. Bye!'
    tts(engine, examiner_text)


if __name__ == '__main__':
    main()
