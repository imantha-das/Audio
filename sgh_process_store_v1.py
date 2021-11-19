import os
import shutil
from pathlib import Path
import glob
import pandas as pd
from pydub import AudioSegment
from termcolor import colored
from difflib import SequenceMatcher
from distutils.util import strtobool
import argparse
import re
from zipfile import ZIP_DEFLATED, ZipFile
from get_audio_length_v1 import get_audio_length
from datetime import timedelta

# Parse Arguments
# -------------------------------------------------------------------------------------------------------------------

parser = argparse.ArgumentParser(description = "ASR input workflow")
parser.add_argument("--fname", type = str, help = "Partial File Name")
parser.add_argument("--path_d", type = str, help = "Path to downloads", default = os.path.join(Path.home(), "Downloads"))
parser.add_argument("--path_l", type = str, help = "Path to location", default = os.path.join("/media", "duli", "passport", "projects"))
parser.add_argument("--from_zoom", type = str, help = "Not from a zoom folder", default = "True")
parser.add_argument(
    "--edit", type = str,
    help = "[1st letter -  c:cgh, s:sgh][2nd letter : u:student, a:staff][3rd letter - s:summaries, c:cases][4th letter - o:otter, z:zoom]", default = "sucz"
)
args = parser.parse_args()

# ++++++++++++++++++++++++++++++++++++++++++++++ Functions ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Computes a similarity match between two strings
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def seq_sim(a:str, b:str):
    a = a.lower()
    b = b.lower()
    return  SequenceMatcher(None, a,b).ratio()


# Outputs the match with the highest score beased in seq_sim
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def get_top_match(name_from_file:str, speakers_from_csv:dict):
    name_similarity = {k : seq_sim(a = name_from_file, b = k) for k in speakers_from_csv.keys()}
    top_match = max(name_similarity, key = name_similarity.get)
    return top_match

# To obtain non hidden file
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def listdir_nohidden():
    return [f for f in os.listdir() if not f.startswith(".")]

# Locate files and folders
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def locate_files_or_folders(fname, path):
    """
    Locates a partial name of the file
    Inputs:
        fname : partial name use * at the end
        path : Path to location, set to 'downloads' to allocate downloads as the folder 
    Outputs:
        list of file names
    """
    os.chdir(path)
    fname = "*" + fname + "*"

    # Check files for defined name within folder
    return [f for f in  glob.glob(fname)]

# Extract filename
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def extract_name(fname):
    # Extract name and file extension from file name             
    split_at_ext = re.split('[.]', fname)
    ext = split_at_ext[1]
    char_without_ext = re.split('\d+',split_at_ext[0])[0]
    name = re.split('audio',char_without_ext)[1]
    name2 = re.findall('[A-Z][a-z]*', name)
    name3 = ' '.join(name2)

    return name3,ext

# Edit file names from zoom
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def copy_rename_from_zoom(folders, path, spk_dict, destination_folder, sess_start_val):
    """
    Access the Audio Record folder and copies files from zoom
    Only works if the files are more than 4, dual single channel
    Inputs:
        folders : List of folder names from locate_files_or_folders
        names : List of names or empty list
        path : Path to folderm usually will be downloaded
    """
    print(colored(os.listdir(), "red"))

    # Obtaining session ID
    folder_dates = list(map(lambda x: x.split(" ")[0], folders))
    if len(set(folder_dates)) != 1:
        print(colored(set(folder_dates), "red"))
        assert len(set(folder_dates)) == 1, colored("There is NO or more than ONE unique date", "red")

    #Obtain sessdate
    sess_date = folder_dates[0].replace("-","_")

    for idx, folder in enumerate(sorted(folders)):
        print(colored(folder, "green", attrs = ["bold"]))
        # Go into Audio Record Folder
        os.chdir(os.path.join(folder, "Audio Record"))
        # Check if there is only 3 files 
        assert len(listdir_nohidden()) <= 3, colored(f"Error : More than 3 files present in folder : {len(listdir_nohidden())}", "red")

        for file in listdir_nohidden():
            if file.startswith("audiospk"):
                spk_id = file[5:16]
                _, ext = file.split(".")
                sess_id = idx + sess_start_val #02
                shutil.copy(src = file, dst = destination_folder)
                f_newname = sess_date + "-sess" + f"{sess_id:02}" + "-" + spk_id + "." + ext
                os.rename(os.path.join(destination_folder, file), os.path.join(destination_folder, f_newname))

            elif file.startswith("audio"):
                spk_name_from_file,ext = extract_name(fname = file)
                if spk_name_from_file != "N T U Host":
                    spk_top_match = get_top_match(name_from_file=spk_name_from_file, speakers_from_csv=spk_dict)
                    print(f"top match : {colored(spk_name_from_file, 'blue', attrs  = ['bold'])} --> {colored(spk_top_match, 'blue', attrs = ['bold'])}")
                    spk_id = spk_dict[spk_top_match] #spk_F_C_002
                    sess_id = idx + sess_start_val #02
                    shutil.copy(src = file, dst = destination_folder)
                    f_newname = sess_date + "-sess" + f"{sess_id:02}" + "-" + spk_id + "." + ext
                    os.rename(os.path.join(destination_folder, file), os.path.join(destination_folder,f_newname))

            else:
                pass

        os.chdir(path)

# Rename files in zoom audio folder
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def rename_files_in_zoom_audio(fname, spk_dict):
    """
    Rechecks files in zoom-audio folder to see if name has been replaced by spk_id
    Renaming files of the following format, 2021_10_30-sess01-Amaranta_Lin-notes.docx
    """
    fname_split = re.split("[-.]",fname)

    if fname_split[2].startswith("spk"): # Check only spk_name1 since in audio files spk_name
        pass
    else:
        if len(fname_split) == 5:
            spk_top_match_1 = get_top_match(name_from_file=fname_split[2], speakers_from_csv=spk_dict) # 1st name
            spk_top_match_2 = get_top_match(name_from_file=fname_split[3], speakers_from_csv=spk_dict)
            print(f"top match : {colored(fname_split[2], 'blue', attrs  = ['bold'])} --> {colored(spk_top_match_1, 'blue', attrs = ['bold'])}")
            print(f"top match : {colored(fname_split[3], 'blue', attrs  = ['bold'])} --> {colored(spk_top_match_2, 'blue', attrs = ['bold'])}")
            spk_id1 = spk_dict[spk_top_match_1] #spk_F_C_002
            spk_id2 = spk_dict[spk_top_match_2]

            f_new_name = fname_split[0] + "-" + fname_split[1] + "-" + spk_id1 + "-" + spk_id2 + "." + fname_split[-1]
            os.rename(src=fname, dst=f_new_name)
        elif len(fname_split) == 4:
            spk_top_match_1 = get_top_match(name_from_file=fname_split[2], speakers_from_csv=spk_dict) # 1st name
            print(f"top match : {colored(fname_split[2], 'blue', attrs  = ['bold'])} --> {colored(spk_top_match_1, 'blue', attrs = ['bold'])}")
            spk_id1 = spk_dict[spk_top_match_1] #spk_F_C_002
            f_new_name = fname_split[0] + "-" + fname_split[1] + "-" + spk_id1 + "." + fname_split[-1]
            os.rename(src=fname, dst=f_new_name)
        else:
            print(colored("Warning : filename in zoom-audio contains more than components than the reqiured","red", attrs = ["bold"]))

# Obtain partial path from key value
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def get_project_location_from_key(key):
    """
    Constuctus the path to stay audio
    Inputs:
        key : string value
    Outputs
        Partial path
    """
    if key[0] == 'c':
        project = "cgh"
    if key[0] == "s":
        project = "sgh"
    if key[1] == "u":
        employee = "student"
    if key[1] == "a":
        employee = "staff"
    if key[2] == "s":
        case = "summaries"
    if key[2] == "c":
        case = "cases"
    if key[3] == "z":
        record = "zoom"
    if key[3] == "o":
        record = "otter" 
    
    return os.path.join(project,employee,case,record)

# Move file to destination
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def move_to_destination(folder_name, path):
    """
    Moves a single folderto the destination folder, Create a Zip object, moves to process, moves to sessions
    """
    shutil.move(folder_name, os.path.join(path,"archive"))
    print("Moved : {} --> {}".format(colored(os.getcwd(), "cyan"), colored(path, "cyan")))
    os.chdir(os.path.join(os.path.join(path, "archive"),folder_name))

    files_in_folder = [f for f in os.listdir()]
    with ZipFile(folder_name + ".zip", "w") as zip_obj:
        for file in files_in_folder:
            zip_obj.write(file, compress_type=ZIP_DEFLATED)

    print(colored("zip complete", "cyan"))
    shutil.move(folder_name + ".zip", "..")
    os.chdir("..")
    shutil.move(folder_name, "../process")
    os.mkdir(os.path.join(path,"sessions", folder_name))    
    os.chdir(os.path.join("..","process", folder_name))

    is_vtt_present = any([f.endswith(".vtt") for f in os.listdir()])

    for f in os.listdir():
        if f.endswith(".pdf") or f.endswith(".docx") or f.endswith(".txt"):
            shutil.move(src = f, dst = os.path.join("..","..","sessions",folder_name))
        elif is_vtt_present:
            print(colored("Vtt Present manual preprosessing required !", "red", attrs = ["bold"]))
        elif f.endswith(".m4a") or f.endswith(".mp4") or f.endswith(".mp3"):
            # vtt file not present 
            nm,ext = f.split(".")
            track = AudioSegment.from_file(f)
            track = track.set_frame_rate(16000)
            track.export(os.path.join("..","..","sessions",folder_name,nm + "." + "wav"), format = "wav")
        elif not f.endswith("vtt"):
            print(colored("Warning : Please check file type", "red", attrs = ["bold"]))

# ------------------------------------------------ Main -------------------------------------------------

if __name__ == "__main__":
    # Load speakers table from get storted name and speaker ID
    speakers = pd.read_csv("speaker-summary-sgh - speakers.csv", usecols = ["Name", "ID"])
    speakers.dropna(inplace = True)
    speakers.rename(columns = {"Name" : "spk_name", "ID" : "spk_id"}, inplace = True)

    # Check if speakers have unique values
    assert speakers.spk_name.is_unique, colored("Repeated name in speaker summary csv file", "red", attrs = ["bold"])
    assert speakers.spk_id.is_unique, colored("Repeated id in speakers summary scv file", "red", attrs=["bold"])

    # Speakers in the form of a dictionary
    spks = {k:v for (k,v) in zip(speakers.spk_name, speakers.spk_id)}

    folders = locate_files_or_folders(fname = args.fname, path = args.path_d)

    if "zoom-audio" not in os.listdir():
        os.mkdir("zoom-audio")

    if bool(strtobool(args.from_zoom.capitalize())):
        #Edits the file names from zoom
        zoom_audio_folder = os.path.join(Path.home(),"Downloads","zoom-audio")
        copy_rename_from_zoom(folders = folders, path = args.path_d, spk_dict=spks, destination_folder=zoom_audio_folder, sess_start_val = 1)
        print(colored("changing directory to zoom audio", "magenta", attrs = ["bold"]))
    # Change directory to zoom-audio
    os.chdir(os.path.join(Path.home(), "Downloads", "zoom-audio"))
    
    print(colored("Renaming any unedited files in zoom audio", "magenta", attrs = ["bold"]))
    # Rename any files in zoom audio folder
    for f in sorted(os.listdir()):
        rename_files_in_zoom_audio(fname= f, spk_dict=spks)

    print(colored("Creating session folders", "magenta", attrs = ["bold"]))
    # Create folders with Date and session number #2021-11-12-sess02
    for f in sorted(os.listdir()):
        folder_name = f.split("-")[0] + "-" + f.split("-")[1]

        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        shutil.move(f, folder_name)

    # Store the folder name and path its suppose to be moved in cache
    edits = [str(item) for item in args.edit.split(",")]
    # If a single string make enough edits for all folders
    if len(edits) == 1:
        edits = edits * len(os.listdir()) 

    folder_loc_cache = {f:os.path.join(args.path_l,get_project_location_from_key(key = os.path.join(l))) for f,l in zip(sorted(os.listdir()), edits)}

    # Move folders to destination
    for folder in sorted(os.listdir()):
        move_to_destination(folder_name=folder, path = folder_loc_cache[folder])

        # Compute audio length
        mp3, mp4, m4a, wav = get_audio_length(path = os.getcwd())

        total_mp3 = timedelta(seconds = sum(mp3))
        total_mp4 = timedelta(seconds = sum(mp4)) 
        total_m4a = timedelta(seconds = sum(m4a)) 
        total_wav = timedelta(seconds = sum(wav))

        mp3_mins = [str(timedelta(seconds = t)) for t in mp3]
        mp4_mins = [str(timedelta(seconds = t)) for t in mp4]
        m4a_mins = [str(timedelta(seconds = t)) for t in m4a]
        wav_mins = [str(timedelta(seconds = t)) for t in wav]

        print(f"mp3 : {colored(mp3_mins, 'yellow', attrs = ['bold'])}")
        print(f"mp4 : {colored(mp4_mins, 'yellow', attrs = ['bold'])}")
        print(f"mp4a : {colored(m4a_mins, 'yellow', attrs = ['bold'])}")
        print(f"wav : {colored(wav_mins, 'yellow', attrs = ['bold'])}")

        print(f"total time mp3 : {colored(total_mp3, 'yellow', attrs = ['bold'])}")
        print(f"total time mp4 : {colored(total_mp4, 'yellow', attrs = ['bold'])}")
        print(f"total time m4a : {colored(total_m4a, 'yellow', attrs = ['bold'])}")
        print(f"total time wav : {colored(total_wav, 'yellow', attrs = ['bold'])}")

        # Change path back to zoom-audio folder
        os.chdir(os.path.join(args.path_d,"zoom-audio"))


    
    

    


    
