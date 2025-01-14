import bophono
from botok import Text, WordTokenizer
import json
import re

from pathlib import Path



options_fastidious = {
  'weakAspirationChar': '3',
  'aspirateLowTones': True,
  'prefixStrategy': 'always',
  'aiAffixchar': 'ː',
  #'hightonechar':'̄',
  #'lowtonechar':'̱',
  'nasalchar': '',
  'stopSDMode': "eow",
  'eatP': False,
  'useUnreleasedStops': True,
  'eatK': False,
  'syllablesepchar': ''
}


PHON_KVP = bophono.UnicodeToApi(schema="KVP", options = {})
PHON_API = bophono.UnicodeToApi(schema="MST", options = options_fastidious)

def get_word_tokenizer():
    WT = WordTokenizer()
    return WT

def read_json_file(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data

def write_json_file(file_path, data):
    with open(file_path, "w", encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def botok_tokenizer(in_str):
    WT = get_word_tokenizer()
    return WT.tokenize(in_str)

def botok_modifier(tokens):
    op = []
    for t in tokens:
        op_token = {
            'start': t.start,
            'end': t.start + t.len,
            'type': t.chunk_type
        }
        op.append(op_token)
    return op

def postsegment(in_str):
    # combine particle with previous syllable when there is just one
    in_str = re.sub(r"(^| )([^ ]+)[\u0F0B\u0F0C] +(ཏུ|གི|ཀྱི|གིས|ཀྱིས|ཡིས|ལྡན|བྲལ|ཅན|བ|པ|བོ|ཝོ|མ|མོ|བའི|བར|བས|བའོ|པའི|པར|པས|པའོ|བོའི|བོར|བོས|བོའོ|པོའི|པོར|པོས|པོའོ|མའི|མར|མས|མའོ|མོའི|མོར|མོས|མོའོ)($|[ ་-༔])", r"\1\2་\3\4", in_str)
    in_str = re.sub(r"([\u0F40-\u0FBC]) +([\u0F40-\u0FBC])", r"\1\2", in_str) # merge affixes
    # combine ma with following syllable when there is just one
    return in_str

def segment(in_str):
    
    try:
        t = Text(in_str, tok_params={'profile': 'GMD'})
        tokens = t.custom_pipeline('dummy', botok_tokenizer, botok_modifier, 'dummy')
    except Exception as e:
        print(e)
        print("botok failed to segment "+in_str)
        return in_str
    res = ''
    first = True
    for token in tokens:
       if not first:
           res += " "
       first = False
       res += in_str[token['start']:token['end']]
    return postsegment(res)

def segmentbytwo(in_str):
    lines = in_str.split("\n")
    res = ""
    for l in lines:
        countsyls = len(re.findall("[\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]+", l))
        l = re.sub(r"([\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]+[^\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]+[\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]+[^\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]*)", r"\1 ", l)
        if countsyls % 2 == 1:
            l = re.sub(r" ([\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]+[^\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]*)$", r"\1", l)
        res += l+"\n"
    return res

def segmentbyone(in_str):
    lines = in_str.split("\n")
    res = ""
    for l in lines:
        countsyls = len(re.findall("[\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]+", l))
        l = re.sub(r"([\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]+[^\u0F35\u0F37ཀ-\u0f7e\u0F80-\u0FBC]*)", r"\1 ", l)
        res += l+"\n"
    return res

def add_phono(in_str, res):
    lines = in_str.split("\n")
    res_kvp = ""
    res_ipa = ""
    for l in lines:
        words = l.split()
        for word in words:
            res_kvp += PHON_KVP.get_api(word)+'  '
            res_ipa += PHON_API.get_api(word)+'  '
        res_kvp += "\n"
        res_ipa += "\n"
    res["kvp"] = res_kvp
    res["ipa"] = res_ipa

def segment_and_phon(in_str):
  seg = segment(in_str)
  res = { "segmented" : seg }
  add_phono(seg, res)
  return res

def segmentbyone_and_phon(in_str):
  seg = segmentbyone(in_str)
  res = { "segmented" : seg }
  add_phono(seg, res)
  return res

def segmentbytwo_and_phon(in_str):
  seg = segmentbytwo(in_str)
  res = { "segmented" : seg }
  add_phono(seg, res)
  return res

def phon(in_str):
  res = {}
  add_phono(in_str, res)
  return res

def ipa_to_phon(ipa, level):
    # Replace line breaks with <br/>
    res = re.sub(r'(?:\r\n|\r|\n)', '<br/>', ipa)

    # Basic replacements
    res = res.replace('y', 'ü')
    res = res.replace('c', 'ky')

    if level == "advanced":
        # Advanced level replacements
        res = re.sub(r'ɔ([\u0304\u0331])?', r"<span class='gray'>o\1</span>", res)
        res = re.sub(r'ə([\u0304\u0331])?', r"<span class='gray'>a\1</span>", res)
        res = res.replace('3', "<span class='gray'>ʰ</span>")
        res = re.sub(r'ʔ([kp])\u031A', r"<sub>\1</sub>", res)
        res = res.replace('ʔ', '<sub>ʔ</sub>')
        res = res.replace('n\u031A', 'n')

    elif level == "intermediate":
        # Intermediate level replacements
        res = re.sub(r'[̱̄3˥˦˧˨˩]', '', res)
        res = re.sub(r'ʔ([kp])\u031A', r"<sub>\1</sub>", res)
        res = res.replace('ʔ', '<sub>ʔ</sub>')
        res = res.replace('ɔ', 'o')
        res = res.replace('ə', "<span class='gray'>a</span>")
        res = res.replace('n\u031A', 'n')

    else:
        # Basic level replacements
        res = re.sub(r'[̱̄3ʰʔ\u031Aː˥˦˧˨˩]', '', res)
        res = res.replace('ɔ', 'o')
        res = res.replace('ə', 'a')
        res = res.replace('n\u031A', 'n')

    # Common replacements
    res = res.replace('ɣ', 'g')
    res = re.sub(r'[̥̊]', '', res)  # half-voicing, not displayed
    res = res.replace('ɖ', 'ḍ')
    res = res.replace('ʈ', 'ṭ')
    res = res.replace('ɲ', 'ny')
    res = res.replace('ø', 'ö')
    res = res.replace('ɟ', 'gy')
    res = res.replace('j', 'y')
    res = res.replace('ɛ', 'è')
    res = res.replace('e', 'é')
    res = re.sub(r'ŋ(\s)', r'ng\1', res)
    res = res.replace('ŋ', 'ṅ')
    res = res.replace('tɕ', 'ch')
    res = res.replace('ɕ', 'sh')
    res = res.replace('dʑ', 'j')
    res = res.replace('dz', 'z')

    return res

def text2phon(text, segment_mode="byone", level="simple"):
    levels = ["simple", "intermediate", "advanced"]
    if level not in levels:
        raise ValueError(f"Level invalid, valid level are {levels}")

    if segment_mode == "byone":
        result = segmentbyone_and_phon(text)
    elif segment_mode == "bytwo":
        result = segmentbytwo_and_phon(text)
    elif segment_mode == "word":
        result = segment_and_phon(text)
    else:
        raise ValueError(f"Segment mode '{segment_mode}' is invalid. Valid mode are word, byone, bytwo")

    phon = ipa_to_phon(result["ipa"], level=level)
    phon = phon.replace("<br/>", "")
    phon = phon.replace(" . ", " ")
    phon = phon.strip()
    return phon

def get_dictionary_phonotics(dictionary_dir):
    batch_dirs = list(dictionary_dir.iterdir())
    batch_dirs.sort()
    word_with_phon = {}
    for batch_dir in batch_dirs:
        word_files = list(batch_dir.iterdir())
        word_files.sort()
        for word_file in word_files:
            word_data = read_json_file(word_file)
            word_id = word_data["word_id"]
            tib_word = word_data["lemma"]
            phon = text2phon(tib_word)
            if phon:
                word_with_phon[word_id] = {
                    "tib_word": tib_word,
                    "phon": phon
                    }
            else:
                word_with_phon[word_id] = {
                    "tib_word": tib_word,
                    "phon": ''
                    }
    return word_with_phon



if __name__ == "__main__":
    dictionary_dir = Path("./data/dictionary_data")
    word_with_phon = get_dictionary_phonotics(dictionary_dir)
    write_json_file("./data/word_with_phon.json", word_with_phon)
