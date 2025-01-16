import csv
import json
from pathlib import Path
from sense_parser import parse_senses_with_claude
import ast
import sys

def get_sentence_count(original_example):
    """takes the original example and returns the number of sentences in it

    Args:
        original_example (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Split the string into words using space as a delimiter
    words = original_example.split(' ')
    # Filter out any empty strings (in case there are extra spaces)
    words = [word.strip() for word in words if word.strip()]
    return len(words) #count the number of words

def cleaned_output(ai_examples):
    """
    try except block is implemented because AI is giving response in string not in python list. so it is converting it to python list.

    Args:
        ai_examples (string): string of AI examples which is in format ['example1', 'example2', 'example3']

    Returns:
        list: python list according to the count which i require
    """
    try:
        ai_examples = ast.literal_eval(ai_examples)
    except Exception as e:
        print("Error:", e)

    print("Converted to list:", ai_examples) # need to comment it out later.
    return ai_examples

def extract_rows(data):
    """
    Extract rows from the input data for CSV generation.
    Fields like Word ID, Lemma, and Level will not repeat for multiple meanings of the same word.

    Parameters:
        data (dict): Dictionary entry for a single word.

    Returns:
        list: A list of rows to be written to the CSV file.
    """
    rows = []
    word_id = data.get("word_id")
    word = data.get("lemma")
    level = data.get("level")
    meanings = data.get("meanings", {})

    first_row = True
    for meaning_id, meaning_data in meanings.items():
        meaning = meaning_data.get("meaning")
        examples = meaning_data.get("examples", {})
        part_of_speech = meaning_data.get("pos")

        #handle the case where there are no examples
        if not examples:
            ai_examples = parse_senses_with_claude(level, word, meaning, 1)
            formatted_output = cleaned_output(ai_examples)
            formatted_output = ", ".join(formatted_output)  # Format the list as a comma-separated string
            rows.append([
                word_id if first_row else "",
                word if first_row else "",
                meaning_id,
                meaning,
                "",  # Placeholder for missing example
                formatted_output,  # AI-suggested example
                part_of_speech,
                level if first_row else "",
                "",  # Reviewed
                "",  # Finalized
            ])
            first_row = False
        else:
            # If multiple examples exist, create a row for each example
            for example_id, example in examples.items():

                count = get_sentence_count(example) # get the number of sentences in the example provided in json
                # call the function to generate AI examples
                ai_examples = parse_senses_with_claude(level, word, meaning, count)
                formatted_output = cleaned_output(ai_examples) # getting the python list of ai examples
                formatted_output = ", ".join(formatted_output)  # Format the list as a comma-separated string
                # Only include Word ID, Lemma, and Level for the first row in this block
                rows.append([
                    word_id if first_row else "",
                    word if first_row else "",
                    meaning_id,
                    meaning,
                    example,
                    formatted_output, 
                    part_of_speech,
                    level if first_row else "",
                    "",  # Reviewed
                    "",  # Finalized
                ])
                first_row = False  # After the first row, omit repeated fields
    return rows



def write_csv(rows, output_file, write_headers=False):
    """
    Write rows to a single CSV file.

    Parameters:
        rows (list): List of rows to write to the CSV file.
        output_file (Path): Path to the output CSV file.
        write_headers (bool): Whether to write headers to the file.

    Returns:
        None
    """
    headers = [
        "Word ID",
        "མ་ཚིག",
        "Meaning ID",
        "འགྲེལ་བ།",
        "དཔེར་བརྗོད་ཚིག་སྒྲུབ།",
        "རིག་ནུས་དཔེར་བརྗོད་ཚིག་སྒྲུབ།",
        "བརྡ་སྤྲོད་ཀྱི་དབྱེ་བ།",
        "གནས་ཚད།",
        "ཞུ་དག་པ།",
        "གཏན་འབེབས།",
    ]

    with output_file.open(mode="a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        if write_headers:
            writer.writerow(headers)
        writer.writerows(rows)

def process_json_files(folder_paths, output_folder, max_word_ids=200):
    """
    Process all JSON files from multiple folders in sorted order and write their data to multiple CSV files.

    Parameters:
        folder_paths (list): List of paths to folders containing JSON files.
        output_folder (Path): Path to the folder for output CSV files.
        max_word_ids (int): Maximum number of Word IDs per CSV file.

    Returns:
        None
    """
    output_folder.mkdir(parents=True, exist_ok=True)

    word_id_counter = 1
    file_index = 1
    output_file = output_folder / f"dictionary_entries_{file_index}.csv"
    write_headers = True

    for folder_path in folder_paths:
        # Get all JSON files from the folder and sort them by file name
        json_files = sorted(folder_path.glob("*.json"), key=lambda x: x.name)

        for json_file in json_files:
            try:
                with json_file.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                word_id = data.get("word_id")

                # Only process unique Word IDs in the current file
                if word_id and data.get("level") in ['A0', 'A1', 'A2']:
                    rows = extract_rows(data)
                    if rows:  # If the rows are not empty (meaning the level was valid)
                        write_csv(rows, output_file, write_headers=write_headers)
                        write_headers = False
                        print(f"word id counter: {word_id_counter}")
                        word_id_counter += 1
                        if word_id_counter ==50:
                            sys.exit()

                        # Check if we need to create a new file after the 200th entry
                        if word_id_counter >= max_word_ids:
                            file_index += 1
                            output_file = output_folder / f"dictionary_entries_{file_index}.csv"
                            word_id_counter = 1  # Reset counter for the new file
                            write_headers = True  # Write headers for the new file
                            print(f"*************** New file created: {output_file} ****************")
            except Exception as e:
                print(f"Error processing file {json_file}: {e}")
    
    print("********** Process completed **********")


if __name__ == "__main__":
    # Main directory containing subfolders with JSON files
    main_folder_path = Path("../data/dictionary_data/")
    # List all subdirectories (folders) and sort them in ascending order
    folder_paths = sorted(main_folder_path.glob("*/"))  # Get all subdirectories
    # Path to the output folder for CSV file
    output_file_path = Path("../data/generated dictionary/Second prompt/")

    # Process the JSON files and generate the CSV
    process_json_files(folder_paths, output_file_path)
