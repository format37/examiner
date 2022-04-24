from deeppavlov import build_model, configs
import speech_recognition as sr
import pyttsx3
import random

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
    engine.say(tts_text)
    engine.runAndWait()

qa = build_model(configs.squad.squad, download=False)
config = 'paraphraser_bert'
paraphraser = build_model(config, download=False)

# Microphone test
"""for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
if index>1:
    print('Please, input the selected microphone index: ')
    selected_mic = int(input())
else:
    selected_mic = 0"""
selected_mic = 3

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

r = sr.Recognizer()
with sr.Microphone(selected_mic) as source:

    tts(engine, "Hello Username! How you're doing?")
    username_text = stt(r, source)

    examiner_text = "Great! Let's get started. Now i will ask you several questions. First. "
    for question_id in range(len(questions)):
        examiner_text += questions[question_id]
        tts(engine, examiner_text)
        examiner_text = ''
        username_text = stt(r, source)
        answers.append(username_text)

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
