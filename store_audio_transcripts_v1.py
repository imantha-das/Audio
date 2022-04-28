import os
import re
import itertools
from pathlib import Path
import shutil 
import pandas as pd
from termcolor import colored
from zipfile import ZIP_DEFLATED, ZipFile
from difflib import SequenceMatcher
import argparse
from pydub import AudioSegment

# Parse Arguments
# ----------------------------------------------------------------------------------------------------------

parser = argparse.ArgumentParser(description = "ASR input workflow")
parser.add_argument("--path", type = str, help = "path to folder", default = os.getcwd())
args = parser.parse_args()

# Number of Folders
# ---------------------------------------------------------------------------------------------------------
def create_folders(files, folder_name):
    """Doesnot work if they are no even matches"""
    pattern = re.compile(r"audio|transcript")
    matches = [[match.group() for match in pattern.finditer(f.lower())] for f in files]
    matches = list(itertools.chain.from_iterable(matches))
    # Check if any audio extension files are present
    assert ("audio" in matches), colored("audio or matches not in list", "red")

    # ++++++++++++++++++++++++++++++++++++  Will Need to be changed accordingly+++++++++++++++++++++++++++++++++++
    no_of_folders_required = int(len(files) / len(set(matches)))
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # Creating folder_name
    prefix_folder_name, suffix_folder_name = folder_name[0:15], folder_name[15:17]

    # int(suffix_folder_name) + 1 --> cause we dont wanr current folder name to be made
    # int(suffix_folder_name) + no_of_folders_required + 1 --> python range does account end value
    
    #Create current folder in process 
    if not os.path.exists(os.path.join("..", "..", "process", folder_name)):
        os.mkdir(os.path.join("..","..","process", folder_name))

    for i in range(int(suffix_folder_name) + 1, int(suffix_folder_name) + no_of_folders_required):
        new_folder_name = prefix_folder_name + "0" + str(i)
        if not os.path.exists(os.path.join("..",new_folder_name)):
            os.mkdir(os.path.join("..", new_folder_name))

        if not os.path.exists(os.path.join("..","..", "process",new_folder_name)):
            os.mkdir(os.path.join("..", "..","process",new_folder_name))

    return matches      

# Name Similarity
# ----------------------------------------------------------------------------------------------------------
# Compute similarity match between two strings
def seq_sim(a:str, b:str):
    a = a.lower()
    b = b.lower()
    return  SequenceMatcher(None, a,b).ratio()

# Outputs the match with highest score
def get_top_match(name_from_file:str, speakers_from_csv:dict):
    name_similarity = {k : seq_sim(a = name_from_file, b = k) for k in speakers_from_csv.keys()}
    top_match = max(name_similarity, key = name_similarity.get)
    return top_match

# Clean DataFrame
# ---------------------------------------------------------------------------------------------------------
def clean_df(df:pd.DataFrame):
    df = df.filter(items = ["Name", "ID"])
    df.rename(columns = {"Name" : "spk_name", "ID" : "spk_id"}, inplace = True)
    df.dropna(subset = ["spk_name"], inplace = True)
    return df

# Rename files
# --------------------------------------------------------------------------------------------------------
def get_new_file_name(folder_name, input_spk_id, ext):
    return folder_name + "-" + input_spk_id + "." + ext

#get pairs : ...-Audio1, ...-transcript1
# --------------------------------------------------------------------------------------------------------
def get_pairs(files, matches):
    file_pair_length = int(len(files) / len(set(matches)))
    audio_dict = {}
    trans_dict = {}
    for pair in range(1, file_pair_length + 1):
        for file in files:
            nm, ext = file.split(".")
            audio_transcript_suffix = nm.split("-")[7]
            
            if (bool(re.match("audio", audio_transcript_suffix))):
                if int(audio_transcript_suffix[5]) == pair: 
                    audio_dict[pair] = file
            if (bool(re.match("transcript", audio_transcript_suffix))):
                if (int(audio_transcript_suffix[10]) == pair):
                    trans_dict[pair] = file

    return audio_dict, trans_dict
        

    
# Zip and Archives files 
# ---------------------------------------------------------------------------------------------------------
def zip_and_archive(files,folder_name):
    files_to_archive = []
    
    for f in files:
        nm, ext = f.split(".")
        if ext == "mp3" or ext == "m4a" or ext == "txt" or ext == "docx" or ext == "pdf":
            files_to_archive.append(f)

    if len(files_to_archive) != 0:
        with ZipFile(folder_name + ".zip", "w") as zip_obj:
            for file in files_to_archive:
                zip_obj.write(file, compress_type=ZIP_DEFLATED)

        print(colored("Zip completed", "green"))

        shutil.move(folder_name + ".zip", os.path.join("..","..","archive"))
    else:
        print(colored("no files to archive", "magenta"))

# Audio File conversion and move to process (not just audio files others too)
# ----------------------------------------------------------------------------------------------------------
def convert_to_wav_and_move_process(files, folder_path, folder_name):

    for file in files:
        nm, ext = file.split(".")
        if ext == "mp3" or ext == "m4a":
            track = AudioSegment.from_file(file)
            track = track.set_frame_rate(16000)
            track.export(os.path.join(folder_path, nm + ".wav"))

            if folder_name not in os.listdir(os.path.join("..","..","process")):
                os.mkdir(os.path.join("..","..","process",folder_name))

            shutil.move(file, os.path.join("..","..","process", folder_name))
        else:
            pass

# Main
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

if __name__ == "__main__":

    # folder name and path
    folder_path = args.path
    folder_name = os.path.basename(folder_path) #2021_08_27-sess01

    # Get DataFrame
    df = pd.read_csv(os.path.join(Path.home(),"speech-and-language-lab","data", "sgh", "scripts","speaker-summary-sgh - speakers.csv"))
    df = clean_df(df)
    
    # Speakers in the form of a dictionary
    spks = {k:v for (k,v) in zip(df.spk_name, df.spk_id)}

    # Compute the number of folders to make
    matches = create_folders(os.listdir(), folder_name=folder_name)

    #Get pairs
    audio_dict, trans_dict = get_pairs(files = os.listdir(), matches = matches)
    print(audio_dict)
    print(trans_dict)

    """
    # Name Suggestion and renaming files
    for file in os.listdir():

        # ++++++++++++++++++++++++++++++++++++++++++ NEED TO CHANGE LINE TO CAPTURE NAME ++++++++++++++++++++++++++++++++++++
    
        nm, ext = file.split(".")
        # for format Gabriel_Yeap-audio1.mp3
        #spk_name_from_file = nm.split("-")[0]

        #for format 2021_10_09-sess03-wenlong_li-sgh-staff-summaries-otter-audio1.mp3
        spk_name_from_file = nm.split("-")[2]
        
        # Get file name and see if correct
        suggestion = get_top_match(name_from_file=spk_name_from_file, speakers_from_csv=spks)
        print(f"file name : {colored(spk_name_from_file,'blue')} --> suggestion : {colored(suggestion, 'green')}")

        
        input_name = input("is suggestion correct?")
        if input_name != "":
            suggestion = input_name

        new_file_name = get_new_file_name(folder_name=folder_name, input_spk_id=spks[suggestion], ext = ext)
        os.rename(file, new_file_name)
        
    # Zip and Archive    
    zip_and_archive(files = os.listdir(), folder_name=folder_name)
    
    # Convert mp3 --> .wav + move file to process
    convert_to_wav_and_move_process(files = os.listdir(), folder_path = folder_path, folder_name=folder_name)
    
    """
