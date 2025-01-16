# import anthropic #type:ignore
# import json
import time
# from pathlib import Path
from config import ANTHROPIC_CLIENT

def parse_senses_with_claude(level, lemma, meaning, number_of_sentences):
    """
    Generates AI-suggested example sentences based on the provided parameters.

    Parameters:
        level (str): The language level (e.g., "A0","A1", "A2").
        lemma (str): The word or lemma to generate examples for.
        meaning (str): The meaning of the word/lemma.
        number_of_sentences (int): The number of example sentences to generate.

    Returns:
        list: A list of AI-suggested example sentences.
    """
    time.sleep(5)  # Introduce a delay to avoid exceeding API rate limits.
    try:
        # Construct the prompt using the parameters
        prompt = f"""
        You are a person with CEFR level <{level}> in Tibetan language.
        Task:
        Write example sentences using a Tibetan word and its meaning according to your language level.
        Input: 
        number of sentences: {number_of_sentences}
        word:<{lemma}>
        meaning: <{meaning}>
        Output:
        Return only the example sentences without any explanation or additional text in python list format. do not exceed the number of sentences requested.
        """
        
        # Make a request to the Claude client
        message = ANTHROPIC_CLIENT.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt.strip()
                }
            ]
        )
        
        print("Anthropic response received")
        # print(f"Anthropic response: {message.content}") # print to understand the format of response
        response = message.content[0].text  # Assuming the response is in `text`

        # Return the response
        return response

    except Exception as e:
        print(f"Error processing: {e}")
        return []

