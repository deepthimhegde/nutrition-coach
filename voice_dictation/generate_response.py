import openai
from prompt_lib import PromptCollection
import time
import utils
from datetime import datetime

def load_message_context(logger_context: str):
    logger_messages = [
        {"role": "system", "content": f"{logger_context}"},
    ]
    return logger_messages

def get_message_intent(openai_api_key, user_text_message: str):
    classes = ["log", "retrieve", "other"]
    intent_messages = load_message_context(PromptCollection.INTENT_CLASSIFICATION)
    intent_messages.append({"role": "user", "content": user_text_message})
    intent_class = generate_response(openai_api_key, messages=intent_messages)
    for intent in classes:
        if intent_class.lower().find(intent) > 0:
            return intent
    return "other"

def get_implicit_meal_type():
    current_time = datetime.now()
    # Define the time ranges for each meal type
    meal_ranges = {
        "breakfast": ((6, 0), (10, 0)),   # 6:00 AM - 10:00 AM
        "brunch" : ((11, 0), (12, 0)),   # 11:00 AM - 12:00 PM
        "lunch": ((12, 1), (14, 0)),      # 12:00 PM - 2:00 PM
        "dinner": ((17, 0), (20, 0)),     # 5:00 PM - 8:00 PM
    }

    # Parse the current time to extract the hour and minute
    hour, minute = current_time.hour, current_time.minute

    # Check the time to determine the meal type
    for meal_type, (start_time, end_time) in meal_ranges.items():
        if start_time <= (hour, minute) <= end_time:
            return meal_type
    # return snack if the meal type doesn't fall under any other time bucket
    return "snack"

def get_meal_type(conversation):
    detected_meal_types = utils.find_meal_keywords(conversation)
    if len(detected_meal_types) != 1:  # If no meal type was detected or more than 1 were detected, resort to implicit 
        return get_implicit_meal_type()
    else:
        return detected_meal_types
    
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

def answer_questions_from_logs(openai_api_key: str, question: str, log_file_path: str='./user_logs/logs.csv'):
    logs = utils.get_user_log_contents(log_file_path)
    qna_prompt = PromptCollection.ANSWER_QUESTION.replace("{context}", logs)
    qna_messages = load_message_context(qna_prompt)
    qna_messages.append({"role": "user", "content": question})
    return generate_response(openai_api_key, messages=qna_messages)

def get_edited_transcript(openai_api_key, transcription):
    rewrite_sentence_messages = load_message_context(PromptCollection.REWRITE_TRANSCRIPT)
    rewrite_sentence_messages.append({"role": "user", "content": transcription})
    edited_transcript = generate_response(openai_api_key, messages=rewrite_sentence_messages)
    return edited_transcript
