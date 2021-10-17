import os 
import pydub
from termcolor import colored
import argparse
from datetime import timedelta 

parser = argparse.ArgumentParser(description = "Computes the total audio time of mp3/m4a files in a directory")
parser.add_argument("-p", "--path", type = str, help = "Path to project folder or full")
args = parser.parse_args()


def get_audio_length(path):
    """
    Computes the total time for different audio file formats (i.e mp3, m4a, ...)
    Inputs :
        path : Folder containing Audio files
    Outputs :
        Tuple consisting total audio for each file format
    """

    os.chdir(path)
    files = os.listdir()

    audio_length_mp3 = []
    audio_length_mp4 = []
    audio_length_wav = []
    audio_length_m4a = []

    for f in files:
        if f.endswith("mp3"):
            t_delta = pydub.AudioSegment.from_file(f)
            print(f"{f} : {timedelta(seconds = t_delta.duration_seconds)}")
            audio_length_mp3.append(t_delta.duration_seconds)
        elif f.endswith("mp4"):
            t_delta = pydub.AudioSegment.from_file(f)
            print(f"{f} : {timedelta(seconds = t_delta.duration_seconds)}")
            audio_length_mp4.append(t_delta.duration_seconds)
        elif f.endswith("m4a"):
            t_delta = pydub.AudioSegment.from_file(f)
            print(f"{f} : {timedelta(seconds = t_delta.duration_seconds)}")
            audio_length_m4a.append(t_delta.duration_seconds)
        elif f.endswith("wav"):
            t_delta = pydub.AudioSegment.from_file(f)
            print(f"{f} : {timedelta(seconds = t_delta.duration_seconds)}")
            audio_length_wav.append(t_delta.duration_seconds)
        else:
            print(f"{f} : Not an audio file")

        
    return (audio_length_mp3, audio_length_mp4, audio_length_m4a, audio_length_wav)

   
if __name__ == "__main__":

    audio_mp3,audio_mp4, audio_m4a, audio_wav = get_audio_length(path = args.path)
    total_mp3 = timedelta(seconds = sum(audio_mp3))
    total_mp4 = timedelta(seconds = sum(audio_mp4)) 
    total_m4a = timedelta(seconds = sum(audio_m4a)) 
    total_wav = timedelta(seconds = sum(audio_wav))

    print(f"mp3 : {colored(audio_mp3, 'cyan', attrs = ['bold'])}")
    print(f"mp4 : {colored(audio_mp4, 'cyan', attrs = ['bold'])}")
    print(f"mp4a : {colored(audio_m4a, 'cyan', attrs = ['bold'])}")
    print(f"wav : {colored(audio_wav, 'cyan', attrs = ['bold'])}")

    print(f"total time mp3 : {colored(total_mp3, 'green', attrs = ['bold'])}")
    print(f"total time mp4 : {colored(total_mp4, 'green', attrs = ['bold'])}")
    print(f"total time m4a : {colored(total_m4a, 'green', attrs = ['bold'])}")
    print(f"total time wav : {colored(total_wav, 'green', attrs = ['bold'])}")

