import sys
import os 
import glob
import shutil
from pathlib import Path
from zipfile import ZipFile
from termcolor import colored
import argparse
from distutils.util import strtobool

from get_audio_length_v1 import get_audio_length
from datetime import timedelta 

# Argument parser
parser = argparse.ArgumentParser(description = "ASR input workflow")
parser.add_argument("--fname", type = str, help = "Partial file name")
parser.add_argument("--path_d", type = str, help = "Path to Downloads, options : downloads", default = "downloads")
parser.add_argument("--path_l", type = str, help = "path to location, option : media, location", default = "media")
parser.add_argument("--process", type = str, help = "move files to process", default = "False")
parser.add_argument(
    "--edit", type = str,
    help = "[1st letter -  c:cgh, s:sgh][2nd letter : u:student, a:staff][3rd letter - s:summaries, c:cases][4th letter - o:otter, z:zoom]", default = "sucz"
)
args = parser.parse_args()

def locate_file(fname, path = "downloads"):
    """Locates a partial name of the file
        Inputs : 
            fname : partial name, use * at end 
            path : path to the location, set to 'downloads' to allocate downloads as the folder
        Outputs :
            list of file names
    """
    fname = "*" + str(fname) + "*"

    if path == "downloads":
        os.chdir(os.path.join(Path.home(), "Downloads"))
    else:
        os.chdir(path)

    files = []
    for file in glob.glob(fname):
        files.append(file)

    return files

def edit_filename_get_partial_path(files, key):
    """
    Edits file name in format <date>-<sess>-<name>-<audio1> to <date>-<sess>-<name>-<proj>-<staff>-<summaries>-<zoom>-<name>
    Inputs:
        files : list of files
    Outputs:
        Edited file name and list of file names
        Get folder name from file
        Get partial path : sgh -> staff -> summaries -> zoom
    """
    e_files = []

    for f in files:
        e_files = []

    for i,f in enumerate(files):

        name = f.split("-") 
        print(len(name))       

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

        
        if len(name) == 4: #edit name if it contains 4 splits (1 name in fname)
                e_name = name[0] + "-" + name[1] + "-" + name[2] + "-" + project + "-" + employee + "-" + case + "-" +  record + "-" + name[3]
                os.rename(f, e_name)
        elif len(name) == 5: #edit name if it contains 5 splits (2 names in fname)
                e_name = name[0] + "-" + name[1] + "-" + name[2] + "-" + name[3] + "-" + project + "-" + employee + "-" + case + "-" +  record + "-" + name[4]
                os.rename(f, e_name)
        else:
            raise Exception(colored("More or less than reqired splits in filename", "red", attrs = ["bold"]))

        print(f"{colored(f, 'blue', attrs = ['bold'])} ---> {colored(e_name, 'yellow', attrs = ['bold'])}")
        e_files.append(e_name)

        #get partial path
    partial_path = os.path.join(project,employee, case, record)

    folder_name_ls = [f.split('-')[0] + "-" + f.split("-")[1] for f in files]
    assert len(set(folder_name_ls)) == 1, colored("More than one folder name", "red", attrs = ["bold"])
    folder_name = folder_name_ls[0]

    return e_files, partial_path, folder_name 

def get_path_to_project(loc = "media"):
    """
    Return path to project folder
    Inputs :
        loc :
            Keywords :
                media
                local 
                or define path to projects (including projects)

    Outputs :
        Path till project folder : /media/duli/passport/projects
    """

    if loc == "media":
        path_to = os.path.join("/media","duli","passport", "projects")
    elif loc == "local":
        path_to = os.path.join(Path.home(), "speech-and-language-lab", "projects")
    else:
        path_to = loc

    return path_to

if __name__ == "__main__":
    # locate files
    files = locate_file(args.fname, args.path_d)

    # edit filenames
    files, partial_path_2,folder_name = edit_filename_get_partial_path(files = files, key = args.edit)

    # path to location
    partial_path_1 = get_path_to_project(loc = args.path_l)

    path_to_loc = os.path.join(partial_path_1, partial_path_2)

    # Move to location (Downloads -> archive)
    if len(files) > 0:
        for f in files:           
            shutil.move(f, os.path.join(path_to_loc, "archive"))
            #print(f"Moved : {colored(f, 'yellow', attrs = ['bold'])} to {colored(path_to_loc, 'green', attrs = ['bold'])}")
       
        new_dir = os.path.join(path_to_loc, "archive")
        print(f"{colored(os.getcwd(), 'magenta', attrs = ['bold'])} --> {colored(new_dir, 'magenta', attrs = ['bold'])}") 
        # Change path to archive
        os.chdir(new_dir)
    
    # Zip the files 
    with ZipFile(folder_name + ".zip", 'w') as zip_obj:
        for f in files:
            zip_obj.write(f)
            
        print(colored("zip complete", "green"))

    # make directores in process and sessions
    os.mkdir("../sessions/" + folder_name)
    os.mkdir("../process/" + folder_name)
    print(colored("directories process and session created", "green"))

    # Move files from to process folder

    if bool(strtobool(args.process)):
        new_dir = os.path.join("..", "process", folder_name)
        for f in files:
            shutil.move(f, new_dir)
        
        print(f"{colored(os.getcwd(), 'magenta', attrs = ['bold'])} ---> {colored(new_dir, 'magenta', attrs = ['bold'])}")
        os.chdir(new_dir)

        # get audio length
        mp3, mp4, m4a, wav = get_audio_length(path = os.getcwd())
        print(f"total time mp3 : {colored(mp3, 'green', attrs = ['bold'])}")
        print(f"total time mp4 : {colored(mp4, 'green', attrs = ['bold'])}")
        print(f"total time m4a : {colored(m4a, 'green', attrs = ['bold'])}")
        print(f"total time wav : {colored(wav, 'green', attrs = ['bold'])}")

        # Exit to process file
        sys.exit()
    else:
        
        # Move files to session

        new_dir = os.path.join("..", "sessions", folder_name)
        for f in files:
            shutil.move(f, new_dir)
        
        print(f"{colored(os.getcwd(), 'magenta', attrs = ['bold'])} ---> {colored(new_dir, 'magenta', attrs = ['bold'])}")
        os.chdir(new_dir)

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

        print(f"mp3 : {colored(mp3_mins, 'cyan', attrs = ['bold'])}")
        print(f"mp4 : {colored(mp4_mins, 'cyan', attrs = ['bold'])}")
        print(f"mp4a : {colored(m4a_mins, 'cyan', attrs = ['bold'])}")
        print(f"wav : {colored(wav_mins, 'cyan', attrs = ['bold'])}")

        print(f"total time mp3 : {colored(total_mp3, 'green', attrs = ['bold'])}")
        print(f"total time mp4 : {colored(total_mp4, 'green', attrs = ['bold'])}")
        print(f"total time m4a : {colored(total_m4a, 'green', attrs = ['bold'])}")
        print(f"total time wav : {colored(total_wav, 'green', attrs = ['bold'])}")