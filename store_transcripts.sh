#!/bin/zsh

# Author : Imantha

# Description : Moves automatic transcript + manual transcripts to respective locations in sgh dataset
# 				Automatic-transcriptions will be renamed as <sess_id>-<spk1_id>-<spk2_id>-v1.TextGrid
#				Manual-transcriptions will be renamed as <sess_id>-<spk1_id>-<spk2_id>-v2.TextGrid

# Running Instructions : ./store_transcripts.sh 2021_11_13-sess04 2021_11_13-sess05 (Any number of sessions can be indicated)


# Locations
path_to_auto_transcript="/home/imantha/speech-and-language-lab/sgh/transcripts/auto-transcripts"
path_to_manual_transcript="/home/imantha/speech-and-language-lab/auto-scoring-pipeline/data-for-autoscoring/transcripts/multi-tier"

# Create Temperory folder
if [ ! -d "tmp" ]
then 
	`mkdir tmp`
else
	echo tmp folder exists!
fi

for sess_id in "$@"
do 
	# Create folder to store manual and automatic transcripts
	if [ ! -d "tmp/$sess_id" ]
	then
		`mkdir tmp/$sess_id`
	else
		echo "tmp/$sess_id exists!"
	fi

	# Copy Automatic transcripts Manual transcripts from respective locations
	textgrid_file_path=`find $path_to_auto_transcript -name "$sess_id*_16k.TextGrid"`
	textgrid_file_name="$(basename -- $textgrid_file_path)"

	if [ ! -f "tmp/$textgrid_file_name" ]
	then
		`cp $textgrid_file_path "tmp/$sess_id"`
	else
		echo "file exists in tmp/$sess_id" 
	fi
	
	# Rename files according to convnstion, i.e 2021_11_13-sess04-spk_M_C_012-spk_M_C_014.TextGrid
	spk1_name=`cut -d'-' -f 3 <<< ${textgrid_file_name##*/}`
	spk2_name_with_suffix=`cut -d'-' -f 4 <<< ${textgrid_file_name##*/}`
	spk2_name=${spk2_name_with_suffix%%.*}
	file_new_name=$sess_id"-$spk1_name-$spk2_name-v1.TextGrid"
	`mv "tmp/$sess_id/$textgrid_file_name" "tmp/$sess_id/$file_new_name"`

	# Copy files manual transcripts into folder
	textgrid2_file_path=`find "$path_to_manual_transcript/$sess_id" -name "*.textGrid"`
	echo $textgrid2_file_path
