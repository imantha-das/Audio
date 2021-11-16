import os 
import shutil
import glob
from pathlib import Path
from termcolor import colored
import re
import argparse
from zipfile import ZIP_DEFLATED, ZipFile
from distutils.util import strtobool
from datetime import timedelta

from get_audio_length_v1 import get_audio_length

parser = argparse.ArgumentParser(description = "ASR input workflow")
parser.add_argument("--fname", type = str, help = "Partial File Name")
parser.add_argument("--path_d", type = str, help = "Path to downloads, options : downloads", default = os.path.join(Path.home(), "Downloads"))
parser.add_argument("--path_l", type = str, help = "path to location, option : media, location", default =  os.path.join("/media","duli","passport", "projects"))
parser.add_argument("--process", type = str, help = "move files to process", default = "False")
parser.add_argument("--from_zoom", type = str, help = "Not from zoom folder", default = "True")
parser.add_argument(
    "--edit", type = str,
    help = "[1st letter -  c:cgh, s:sgh][2nd letter : u:student, a:staff][3rd letter - s:summaries, c:cases][4th letter - o:otter, z:zoom]", default = "sucz"
)
args = parser.parse_args()

# ---------------------------------------------------------------------------------------------------------------
# To obtain non hidden files
def listdir_nohidden():
    return [f for f in os.listdir() if not f.startswith(".")]
    

# Locate files or folders 
# ---------------------------------------------------------------------------------------------------------------

def locate_files_or_folders(fname, path):
    """
    Locates a partial name of the file
    Inputs:
        fname : partial name, use * at the end
        path : path to location, set to 'downloads' to allocate downloads as the folder
    Outputs:
        list of file names
    """
    os.chdir(path)


    fname = "*" + fname + "*"

    # Check files for defined name within folder
    files_or_folders = []
    for f in glob.glob(fname):
        files_or_folders.append(f)

    return files_or_folders

# Edit file name from zoom meta data
# ----------------------------------------------------------------------------------------------------------------


def edit_filenames_from_zoom(folders,  path):
    """
    Access Audio Record folder in zoom recorded file and get relevant files,
    Only works if the number of files are less than 4, dual single channel, 
    Inputs :
        folders : List of folder names from locate_files_or_folders
        names : List of names or empty list,
        path : Path to folder, usually will be downloads
    """
    print(colored(os.listdir(), "red"))
    if "zoom-audio" not in os.listdir():
        os.mkdir("zoom-audio")

    # Obtaining session ID
    folder_dates = list(map(lambda x: x.split(" ")[0], folders))
    
    if len(set(folder_dates)) != 1:
        print(colored(set(folder_dates), "red"))
        assert len(set(folder_dates)) == 1, colored("There is NO or more than ONE unique date", "red")

    sess_date = folder_dates[0].replace('-','_')

    
    # List of folders
    folder_ls = sorted(folders)

    for idx, folder in enumerate(folder_ls):
        print(colored(folder, "green", attrs = ["bold"]))
        #folder = folders[sess_id-1]   
        os.chdir(os.path.join(folder, "Audio Record")) # Within Zoom folder -- Change Dir to Audio Record
        # Loop through the files for files in Audio Record
        # There are are only 3 or less files -- NTU_HOST, Speaker1, (Speaker2)
        if len(listdir_nohidden()) > 3:  
            print(colored(f"WARNING : More than required number of files in Audio Record folder", "red", attrs = ["bold"]))
            print(colored(listdir_nohidden(), "red", attrs = ["bold"]))

        if len(listdir_nohidden()) > 0:        
            for file in listdir_nohidden(): 

                if file.startswith("audio"):

                    # Extract name and file extension from file name             
                    split_at_ext = re.split('[.]', file)
                    ext = split_at_ext[1]
                    char_without_ext = re.split('\d+',split_at_ext[0])[0]
                    name = re.split('audio',char_without_ext)[1]
                    name2 = re.findall('[A-Z][a-z]*', name)
                    name3 = '_'.join(name2)
                    
                    if name3 != "N_T_U_Host":
                        # rename file with new name, i.e 2021_10_21-sess01-Gabriel_Yeap-audio
                        fname = sess_date + "-sess0" + str(idx + 1) + "-" + name3 + "-audio" + "." + ext
                        os.rename(file, fname)
                        print(f"{colored(file, 'green')} --> {colored(fname, 'green')}")
                        # Push file to Downloads/audio-record folder
                        shutil.move(fname, os.path.join(path, "zoom-audio"))

                else:
                    # Files you that has manually been edited
                    shutil.move(file, os.path.join(path, "zoom-audio"))

            if "Notes" in os.listdir(".."):
                os.chdir(os.path.join("..", "Notes"))

                for file in os.listdir():
                    shutil.move(file, os.path.join(path, "zoom-audio"))

        else:
            print(colored(f"No files in directory"))
                        
        
          
        os.chdir(path)

# Edit file names from args
# ------------------------------------------------------------------------------------------------------------------------------

def edit_filename_from_key(fname, key):
    """
    Edits a single file name in format <date>-<sess>-<name>-<audio1> to <date>-<sess>-<name>-<proj>-<staff>-<summaries>-<zoom>-<name>
    Inputs:
        keys = single key from a list of keys
    Outputs:
        Edited file name and list of file names
        Get folder name from file
        Get partial path : sgh -> staff -> summaries -> zoom
    """
    fname_split = fname.split("-")

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

    if len(fname_split) == 4: #edit name if it contains 4 splits (1 name in fname)
        edited_name = fname_split[0] + "-" + fname_split[1] + "-" + fname_split[2] + "-" + project + "-" + employee + "-" + case + "-" +  record + "-" + fname_split[3]
        os.rename(fname, edited_name)
    elif len(fname_split) == 5: #edit name if it contains 5 splits (2 names in fname)
        edited_name = fname_split[0] + "-" + fname_split[1] + "-" + fname_split[2] + "-" + fname_split[3] + "-" + project + "-" + employee + "-" + case + "-" +  record + "-" + fname_split[4]
        os.rename(fname, edited_name)
    else:
        raise Exception(colored("More or less than reqired splits in filename", "red", attrs = ["bold"])) 

    return os.path.join(project,employee, case, record), edited_name 

# -----------------------------------------------------------------------------------------------------------------------------------

def move_to_destination(folder_name, path, process):
    """
    Moves a single folder to the destination folder, creates a Zip Object
    Inputs:
        folder_name : Name of folder you wish to move
        path : Destination location (/media/duli/passport/projects/sgh/student/cases/zoom/archive)
    """
    shutil.move(folder_name, path)
    print(f"Moved : {colored(os.getcwd(), 'cyan')} --> {colored(path, 'cyan')}")
    os.chdir(os.path.join(path, folder_name))

    files_in_folder = [f for f in os.listdir()]
    with ZipFile(folder_name + ".zip", 'w') as zip_obj:
        for file in files_in_folder:
            zip_obj.write(file, compress_type=ZIP_DEFLATED)

    print(colored("Zip Completed", "cyan"))
    shutil.move(folder_name + ".zip", "..")
    os.chdir("..")

    if process:
        shutil.move(folder_name, "../process")
        process_dir = os.path.join("..", "process", folder_name)
        print(f"{colored(os.getcwd(), 'cyan')} --> {colored(process_dir, 'cyan')}")      
        os.chdir(process_dir)
        
    else:
        shutil.move(folder_name, "../sessions")
        sessions_dir = os.path.join("..", "sessions", folder_name)
        print(f"{colored(os.getcwd(), 'cyan')} --> {colored(sessions_dir, 'cyan')}")     
        os.chdir(sessions_dir)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

if __name__ == "__main__":
    folders = locate_files_or_folders(fname = args.fname, path = args.path_d) #Path --> Downloads

    if bool(strtobool(args.from_zoom)):
        # Edits the file names from zoom and pushes the files to folder zoom audio
        edit_filenames_from_zoom(folders = folders, path = args.path_d)

    # Change directory to downloads/zoom-audio 
    os.chdir(os.path.join(args.path_d, "zoom-audio"))

    foldername_and_path_cache = {}
    edits = [str(item) for item in args.edit.split(",")]
    process = [bool(strtobool(item.capitalize())) for item in args.process.split(",")]

    for f in sorted(os.listdir()):
        print(colored(f, "red"))
        folder_name = f.split("-")[0] + "-" + f.split("-")[1]

        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        shutil.move(f, folder_name)
        
    for folder_idx,folder in enumerate(sorted(os.listdir())):
        os.chdir(folder)

        for file in sorted(os.listdir()):
            if len(edits) == 1:
                path_to_zoom, f_new = edit_filename_from_key(fname = file, key = edits[0])
                process_val = process[0]
            else:
                path_to_zoom, f_new = edit_filename_from_key(fname = file, key = edits[folder_idx])
                process_val = process[folder_idx]

        foldername_and_path_cache[folder] = [os.path.join(args.path_l, path_to_zoom, "archive"),process_val]
        os.chdir("..")

    
    zoom_audio_path = os.getcwd()
    for k,v in foldername_and_path_cache.items():
        move_to_destination(folder_name = k, path = v[0], process = v[1])

        # get audio length
        # get audio length
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

        # CHange back to zoom folder
        os.chdir(zoom_audio_path)
    
    


