from whisper_mic.whisper_mic import WhisperMic
import openai
from prompt_lib import PromptCollection
import time
import utils
import csv

# Load the secrets YAML file
import yaml
with open('secrets.yaml', 'r') as file:
    secrets = yaml.safe_load(file)

openai_api_key = secrets['ACCESS_TOKENS']['OPENAI']

def load_message_context(logger_context: str):
    logger_messages = [
        {"role": "system", "content": f"{logger_context}"},
    ]
    return logger_messages

def generate_response(openai_api_key, messages=None, model="gpt-3.5-turbo"):
    if messages is None:
        return ''
    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        )
    # Extract the generated completion
    completion = response.choices[0].message.content.strip()
    return completion

# def get_sentence_incomplete_classification(incomplete_sentence_classifier_messages, intermediate_result):
#     incomplete_sentence_classifier_messages.append({"role": "user", "content": intermediate_result})
#     incomplete_classification = generate_response(openai_api_key, messages=incomplete_sentence_classifier_messages)
#     incomplete_classification = incomplete_classification.strip().replace('.', '').lower()
#     print('Incomplete sentence? ', incomplete_classification)
#     try:
#         assert (incomplete_classification == 'yes') or (incomplete_classification == 'no')
#     except Exception as e:
#         print("Sorry, I'm having trouble right now, please try again")
#     return incomplete_classification

def get_message_intent(user_text_message: str):
    classes = ["log", "retrieve", "other"]
    intent_messages = load_message_context(PromptCollection.INTENT_CLASSIFICATION)
    intent_messages.append({"role": "user", "content": user_text_message})
    intent_class = generate_response(openai_api_key, messages=intent_messages)
    for intent in classes:
        if intent_class.lower().find(intent) > 0:
            return intent
    return "other"

def answer_questions_from_logs(question: str, log_file_path: str='./user_logs/logs.csv'):
    logs = utils.get_user_log_contents(log_file_path)
    qna_prompt = PromptCollection.ANSWER_QUESTION.replace("{context}", logs)
    qna_messages = load_message_context(qna_prompt)
    qna_messages.append({"role": "user", "content": question})
    return generate_response(openai_api_key, messages=qna_messages)

def main():

    # ----- Run voice dictation -----
    print("Say the word 'exit' to quit")
    print("Say the word 'proceed' to move to AI's response")
    stop_word = 'exit'
    intermediate_result = ''
    task_intent = ''

    logger_messages = load_message_context(PromptCollection.LOGGER)
    mic = WhisperMic(model='base', english=True, pause=0.8)

    while intermediate_result.strip().replace('.', '').lower() != stop_word:
        transcription = ''
        start_time = time.time()
        while time.time() - start_time < 30:
            intermediate_result = mic.listen()
            transcription += intermediate_result
            print(intermediate_result)

            # Break if proceed word is uttered
            if intermediate_result.strip().replace('.', '').lower() == "proceed":
                break
            # Break execution if stop word is uttered    
            if intermediate_result.strip().replace('.', '').lower() == stop_word:
                break   

        if intermediate_result.strip().replace('.', '').lower() == stop_word:
                break

        transcription = transcription.replace("proceed", "")
        rewrite_sentence_messages = load_message_context(PromptCollection.REWRITE_TRANSCRIPT)
        rewrite_sentence_messages.append({"role": "user", "content": transcription})
        edited_transcript = generate_response(openai_api_key, messages=rewrite_sentence_messages)
        # time.sleep(5)
        # print("Time elapsed: ", time.time() - start_time)
        print(f"Detected transcript: {transcription}")  
        print(f"Edited transcript: {edited_transcript}")
        # print("Sending request to OPENAI... ")

        # Check intent of first message
        if len(task_intent) == 0:  # no messages exchanged so far
            task_intent = get_message_intent(edited_transcript)
            print(f"~~~Intent detected: {task_intent}")

        if task_intent == "log":
            
            logger_messages.append({"role": "user", "content": edited_transcript})
            system_response = generate_response(openai_api_key, messages=logger_messages)
            logger_messages.append({"role": "assistant", "content": system_response})
            print(system_response)
            print('-------------')
        elif task_intent == "retrieve":
            system_response = answer_questions_from_logs(edited_transcript)
            print(f"Answer: {system_response}")
        else:
            # TODO: Call default chat completion
            pass

    print('done.')
    print('*******')
    # print(logger_messages)

    # ----- Log chat messages to database -----
    # Create CSV once per user
    if task_intent == "log":
        # Reset logs 
        # utils.create_csv('./user_logs/logs.csv', ['datetime', 'role', 'content'])
        logger_messages_without_system_message = logger_messages[1:]
        utils.write_rows_to_csv('./user_logs/logs.csv', logger_messages_without_system_message)




if __name__ == "__main__":
     main()