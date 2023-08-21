import re
import csv
from datetime import datetime
from typing import List

def get_last_assistant_message(messages: List[dict]):
    return [msg for msg in messages if msg['role'] == 'assistant'][-1]

def get_json_from_string(text: str):
    return re.search(r"\s([{\[].*?[}\]])$", text).group(1)

def create_csv(file_name: str, columns: List[str]):
    with open(file_name, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(columns)

def write_rows_to_csv(file_name: str, rows: List[dict], datetime: datetime=datetime.now()):
    # Append new rows to the CSV file
    with open(file_name, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        for row in rows:
            csv_writer.writerow((datetime, row["role"], row["content"]))

def get_user_log_contents(file_name: str):
    contents = ''
    with open(file_name, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        header = next(csv_reader)  # Skip the header
        for row in csv_reader:
            contents += '\n' + row[1] + ': ' + row[-1]
    return contents
