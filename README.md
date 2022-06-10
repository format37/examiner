# Examiner
Robot, performing English conversation with user. Conversation theme is based on a prompt, defined in the file config.json
### Requirements
Transcribation requirements:  
* Microphone  
* Nvidia GPU + Builded [vosk docker image](https://github.com/format37/stt)  
Text generation requirements:  
* Openai account with Api key and Correct payment settings  
Evaluation requirements:  
* Nvidia GPU + Builded [paraphrase docker image](https://github.com/format37/nlp)  
* Nvidia GPU + Builded [textqa docker image](https://github.com/format37/nlp)  
### Installation
```
git clone https://github.com/format37/examiner
cd examiner
pip install requirements -r
```
Configure your conf.json:
* Address of Paraphrase server
* Address of Text QA server
* Address of Stt server
* Questions count limit
* Stop words. It can be any roles of speakers. For example, friend, collegue, client, etc.
* Prompt. This text is example base for GPT-3 text generator. There is can be defined any conversation start or example, wich you can imagine.
### Run
```
export OPENAI_API_KEY=your_key
python examiner.py
```
* Listen the question  
* Answer by voice to microphone. Press Space, when you finish your speech  
* After N questions, get your speech evaluation  
### Evaluation logic
* Collect Robot's questions
* Merging User's answers to single Text
* Using TextQA to collect Automatic answers for each question, based on the Text
* Using Paraphrase to compare each user's and automatic answer. If answers are paraphrase, that answer is correct.
* Finally, calculate correct part of overall answers
