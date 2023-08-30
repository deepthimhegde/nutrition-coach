import streamlit as st
import openai
import speech_recognition as sr
from prompt_lib import PromptCollection
from generate_response import get_edited_transcript, generate_response, load_message_context
import utils
import yaml
import os

# Load the secrets YAML file
dir = os.path.join(os.path.dirname(__file__))
with open(dir+'/secrets.yaml', 'r') as file:
    secrets = yaml.safe_load(file)
# Set OpenAI API key from Streamlit secrets
openai.api_key = secrets['ACCESS_TOKENS']['OPENAI']

st.title("Nutrition Coach")

if "username" not in st.session_state:
    st.session_state["username"] = ''

with st.sidebar:
    # st.title(f'🤖💬 Welcome!')
    if name:= st.text_input('Enter your name here...'):
        st.session_state["username"] = name
        st.write(f'🤖💬 Welcome {st.session_state["username"]}!')

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = load_message_context(PromptCollection.LOGGER)

# if "logger_messages" not in st.session_state:
#     st.session_state.logger_messages = load_message_context(PromptCollection.LOGGER)

if "transcription" not in st.session_state:
    st.session_state["transcription"] = ""

if "mic_hold" not in st.session_state:
    st.session_state["mic_hold"] = False

for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if 'button' not in st.session_state:
    st.session_state.button = False

if st.session_state['mic_hold']: 
    st.session_state.button = True

def click_button():
    st.session_state.button = not st.session_state.button
    st.session_state["mic_hold"] = False
    st.session_state["transcription"] = ""

button_label = ''
if st.session_state.button:
    button_label = ':red[Click to turn OFF 🎤]'
else:
    button_label = ':green[Click to turn ON 🎤]'

st.button(button_label, on_click=click_button)

if st.session_state.button:
    stop_word = 'exit'
    proceed_word = 'proceed'
    last_word = ''
    intermediate_result = ''
    transcription = ''
    task_intent = ''
    recognizer = sr.Recognizer()
    with st.chat_message("user"):
        with sr.Microphone() as source:
            print("Listening...")
            message_placeholder = st.empty()
            while intermediate_result.strip().replace('.', '').lower() != stop_word:
                
                try:
                    audio = recognizer.listen(source, timeout=5)
                    intermediate_result = recognizer.recognize_google(audio)
                    transcription += ' ' + intermediate_result
                    print('Recognized raw text: ', intermediate_result)

                    message_placeholder.markdown(transcription + "▌")
                    # st.markdown(transcription)
                    last_word = intermediate_result.split()[-1].strip().replace('.', '').lower()
                    if last_word == proceed_word or last_word == stop_word:
                        break
                    if not st.session_state.button:
                        break
                except:
                    print("Restarting...")

    transcription = transcription.replace("proceed", "")
    edited_transcript = transcription # get_edited_transcript(openai.api_key, transcription)
    message_placeholder.markdown(edited_transcript)
    st.session_state["transcription"] = edited_transcript            
    
    if last_word == proceed_word:
        st.session_state["mic_hold"] = True
    if last_word == stop_word:
        st.session_state["transcription"] = ""
        st.session_state["mic_hold"] = False
        st.session_state.button = False
        print('Re-running app...')
        st.experimental_rerun()

else:
    st.session_state['run'] = False

if prompt := st.chat_input("What is up?") or len(st.session_state["transcription"]) > 1:
    if len(st.session_state["transcription"]) > 1:
        prompt = st.session_state["transcription"]
    print('Prompt going into the model: ', prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Only display user prompt if input is text based. Voice prompt is already displayed earlier.
    if len(st.session_state["transcription"]) == 0: 
        with st.chat_message("user"):
            st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        model_response = generate_response(openai.api_key, st.session_state.messages)
        print(model_response)
        # st.markdown(model_response)
        for response in model_response:
            full_response += response
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": model_response})
    # Write the latest exchange between user and system into csv file
    utils.write_rows_to_csv(f'./user_logs/{st.session_state.username}_logs.csv', st.session_state.messages[-2:])

if st.session_state['mic_hold']:
    print('Re-running app...')
    st.experimental_rerun()