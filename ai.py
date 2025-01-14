'''AI model configuration'''

from openai import OpenAI
import os

from dotenv import load_dotenv, find_dotenv


_ = load_dotenv(find_dotenv())

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


conversation_history = {}

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(model=model,
                                              messages=messages,
                                              temperature=0.3,
                                              max_tokens=256)
    
    return response.choices[0].message.content


def build_prompt(messages, learning_language):
    system_prompt = f"You are a helpful and encouraging language learning partner. User is learning {learning_language}. Engage the user in a simple conversation in the learning language using beginner-friendly level vocabulary."
    prompt = f"{system_prompt}\n"
    for turn in messages:
        prompt += f"{turn['role']}: {turn['content']}\n" 
    return prompt
