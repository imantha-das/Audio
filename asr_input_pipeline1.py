import os 
import sys 
import shutil
import glob
from pathlib import Path
from termcolor import colored
import numpy as np
import datetime

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

    # Change directory to folder
    if path == "Downloads":
        os.chdir(os.path.join(Path.home(), "Downloads"))
    else:
        os.chdir(path)

    # Check files for defined name within folder
    files_or_folders = []
    for f in glob.glob(fname):
        files_or_folders.append(f)

    return files_or_folders

def edit_file_names_from_zoom(folders, names,  path):
    """
    Access Audio Record folder in zoom recorded file and get relevant files
    Inputs :
        folders : List of folder names from locate_files_or_folders
        names : List of names or empty list,
        path : Path to folder, usually will be downloads
    """

    back_to_main_path = path

    # Obtaining session ID
    folder_dates = list(map(lambda x: datetime.datetime.strptime(x.split(" ")[0], '%Y-%m-%d'), folders))
    assert len(set(folder_dates)) == 1, "There is more than one unique date"
    sess_date = folder_dates[0]

    folder_times = list(map(lambda x: datetime.datetime.strptime(x.split(" ")[1],'%H.%M.%S'), folders))
    sess_no = sorted(range(len(folder_times)), key = lambda k: folder_times[k]) # Get sorted index based on time
    sess_no = [num + 1 for num in sess_no] # Add one to make session is begin with 1

    edited_fnames = []
    # Loop through all folders in the given path
    for idx1,folder in enumerate(folders):
        folder_name_split = folder.split(" ")       
        os.chdir(os.path.join(path, folder, "Audio Record")) # Within Zoom folder -- Change Dir to Audio Record
        # Loop through the files for files in Audio Record
                  
        for idx2,file in enumerate(os.listdir()): 
            if len(names) == 0:                  
                split_file = file.split("_")
                nm = "_".join(split_file[3::])
                fname = datetime.datetime.strftime(sess_date, '%Y-%m-%d') + "-sess0" + str(sess_no[idx2]) + "-" + nm
                edited_fnames.append(fname)
                print(colored(fname, "magenta"))
                print(colored(nm, "green"))
            else:
                name = names[idx1][idx2]
                fname = datetime.datetime.strftime(sess_date, '%Y-%m-%d') + "-sess0" + str(sess_no[idx2]) + "-" + name 
                print(colored(fname, "magenta"))

                

            

                

        



if __name__ == "__main__":
    path = os.path.join(Path.home(), "speech-and-language-lab", "recordings")
    names = [["Jing_Chun", "Henry_Neo", "Imantha_Gunasekera"], ["Calvin_Chen", "Ramanthan", "Imantha_Gunasekera","Imantha_Gunasekera"], ["Maw_May_Mya_Lwin", "Zin_Mon_Khine"]]
    folders = locate_files_or_folders(fname = "2021-10-15", path = path)
    edit_file_names_from_zoom(folders = folders, names = names, path = path)
 
    
        
