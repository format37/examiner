# Examiner
A robot that asks a list of questions from a file in a synthesized voice, listens to your answers through a microphone, and finally evaluates your answers.  
### Algorithm:
1. Reading questions  
2. Collecting User's answers  
3. Merging answers to single Text  
4. Collecting automatic answers for each question by the Text  
5. Paraphrase comparing between each user's and automatic answer  
6. If user answered well, speaking the greeting message. Else leave-taking  
### installation
```
git clone https://github.com/format37/examiner
cd examiner
conda create -n bert python=3.7 ipython
conda activate bert
conda install -c anaconda pyaudio
```
### Run
- Connect any microphone or web camera  
```
python examiner.py
```
- Input index of selected microphone  
- Listen the voice of examiner and answer
