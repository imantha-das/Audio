import os
import shutil
import argparse
from termcolor import colored
from datetime import datetime

parser = argparse.ArgumentParser(description = "collate all notes in folders")
parser.add_argument("-p","--path", type = str, help = "enter path to directory")
parser.add_argument("-d", "--destination", type = str, help = "enter path to store directory")
args = parser.parse_args()

def collate_notes():
    """Collates all notes from sgh students"""
    os.chdir(args.path)
    print(f"Current Director : {colored(os.getcwd(), 'green')}")
    print(colored(os.listdir(), "red"))
    for folder in os.listdir():
        print(colored(folder, 'red'))
        dt = datetime.strptime(folder.split("-")[0], "%Y_%m_%d")
        
        if dt >= datetime(2021,10,13) and dt <= datetime(2021,11,11):
            for f in os.listdir(folder):
                if f.endswith("docx") or f.endswith("pdf"):
                    shutil.copy(src = os.path.join(folder,f), dst = args.destination)

if __name__ == "__main__":
    collate_notes()
