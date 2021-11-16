import os
import shutil
import pandas as pd
from termcolor import ATTRIBUTES, colored
from difflib import SequenceMatcher
import numpy as np

speakers = pd.read_csv("speaker-summary-sgh - speakers.csv", usecols = ["Name", "ID"])
speakers.dropna(inplace = True)
speakers.rename(columns = {"Name" : "spk_name", "ID" : "spk_id"}, inplace = True)

spks = {k:v for (k,v) in zip(speakers.spk_name, speakers.spk_id)}


assert speakers.spk_name.is_unique, colored("Repeated name in speaker summary csv file", "red", attrs = ["bold"])
assert speakers.spk_id.is_unique, colored("Repeated id in speakers summary scv file", "red", attrs=["bold"])

def seq_sim(a:str, b:str):
    a = a.lower()
    b = b.lower()
    return  SequenceMatcher(None, a,b).ratio()

def get_top_match(name_from_file):
    name_similarity = {k : seq_sim(a = name_from_file, b = k) for k in spks.keys()}
    top_match = max(name_similarity, key = name_similarity.get)
    return top_match

