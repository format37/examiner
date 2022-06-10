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
Configure your conf.json
### Run
```
export OPENAI_API_KEY=your_key
python examiner.py
```
* Listen the question  
* Answer by voice to microphone. Press Space, when you ends  
* After N questions, get your speech evaluation  
### Evaluation logic
* Collect Robot's questions
* Collecting User's answers
* Merging answers to single Text
* Collecting automatic answers for each question by the Text
* Paraphrase comparing between each user's and automatic answer. If answers are paraphrase, that answer is correct.
* Finally, calculate correct part of overall answers
