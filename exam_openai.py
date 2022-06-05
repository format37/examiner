import os
from deeppavlov import build_model, configs
import speech_recognition as sr
import pyttsx3
import json
import openai


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


def main():

    if (os.getenv("OPENAI_API_KEY") is None):
        print("# error: OPENAI_API_KEY is not set")
        return

    question_count_limit = 3
    
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

    # Text to speech init
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-60) # slow down
    engine.setProperty('voice', 'english-us')
    #engine.setProperty('voice', 'russian')   

    questions = []
    answers = []

    r = sr.Recognizer()
    with sr.Microphone(selected_mic) as source:
        #examiner_text = "Hello Username! How are you doing?"
        prompt = "There is dialogue of Hr with Candidate for Machine learning engineer position:\n\n"
        prompt += "Hr: Hello, how you doing?\n"
        prompt += "Candidate: I am fine thanks!\n"
        prompt += "Hr:"
        stop_words = ["Hr:", "Candidate:"]

        for _ in range(question_count_limit):
            examiner_text = text_davinci(prompt, stop_words)['choices'][0]['text']
            prompt += examiner_text
            questions.append(examiner_text)
            tts(engine, examiner_text)
            username_text = stt(r, source)
            answers.append(username_text)
            prompt += '\nCandidate: ' + username_text + '\nHr: '
        

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
