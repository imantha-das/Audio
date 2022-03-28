!/bin/zsh

#Author : Imantha Gunasekera
#Description : Scoring pipeline
	# 1. Copy relevent audio and transcription 
	# 2. Multi channel transcripts --> Mono channel transcripts
	# 3. Renaming transcript files 
	# 4. Preparation of kaldi data
	# 5. ASR autoscoring ?? (can we, requires changing variable name)

sess_id=$1

# 1. Copy relevent files -----------------------------------------------------------------------
# Get transcripts from downloads
trans_loc=`find ~/Downloads -name "${sess_id}*.TextGrid"`
trans_store_multi_loc="/home/imantha/speech-and-language-lab/auto-scoring-pipeline/data-for-autoscoring/transcripts/multi-tier"
audio_loc="/home/imantha/speech-and-language-lab/sgh/data/student/cases/zoom/sessions/$sess_id"
audio_store_mono_loc="/home/imantha/speech-and-language-lab/auto-scoring-pipeline/data-for-autoscoring/audio/single-tier"
trans_store_mono_loc="/home/imantha/speech-and-language-lab/auto-scoring-pipeline/data-for-autoscoring/transcripts/single-tier"

# Create folder with sess_id and store transcript from downloads
if [ -f "$trans_loc" ]
then 
	`mkdir $trans_store_multi_loc"/$sess_id"`
	`mv $trans_loc $trans_store_multi_loc"/$sess_id"`
	# Need to add a line to rename file
else
	echo "Transcript NOT available in downloads"
fi

# 1. Search for audio files in downloads
if [ -d "$audio_loc" ] && [ ! -d "$audio_store_mono_loc/$sess_id" ]
then
	#found_wav=`find $audio_loc -name "*.wav"`
	`mkdir $audio_store_mono_loc"/$sess_id"`
	`find $audio_loc -name "*.wav" -exec cp {} $audio_store_mono_loc"/$sess_id" ';'`
else
	echo "Audio mono - folder already exists"
fi

#2. Multi Channel transcription --> Mono Channel Transcripts
if [ ! -d "$trans_store_mono_loc/$sess_id" ]
then 
	`mkdir $trans_store_mono_loc/$sess_id`
	python data-desensitizing/utils/2_separate_textgrid_v1.py $trans_store_multi_loc"/$sess_id" $trans_store_mono_loc"/$sess_id"
else
	echo "Transcription mono - folder already exists"
fi

#3. Renaming transcript files

if [ -d "$trans_store_mono_loc/$sess_id" ]
then 
	
	spk1_transcript_file=`find $trans_store_mono_loc"/$sess_id" -name "*channel1.TextGrid"`
	spk1_name=`cut -d'-' -f 3 <<< ${spk1_transcript_file##*/}`
	spk1_new_name=$sess_id"-$spk1_name.TextGrid"
	

	spk2_transcript_file=`find $trans_store_mono_loc"/$sess_id" -name "*channel2.TextGrid"`
	spk2_name_with_channel=`cut -d'-' -f 4 <<< ${spk2_transcript_file##*/}`
	spk2_name=${spk2_name_with_channel%%.*}
	spk2_new_name=$sess_id"-$spk2_name.TextGrid"

	echo file new names
	echo $spk1_new_name
	echo $spk2_new_name

	`mv $spk1_transcript_file $trans_store_mono_loc"/$sess_id/$spk1_new_name"`
	`mv $spk2_transcript_file $trans_store_mono_loc"/$sess_id/$spk2_new_name"`

	`xdg-open $trans_store_mono_loc"/$sess_id"`
	`xdg-open $audio_store_mono_loc"/$sess_id"`

	echo "please confirm transcripts and audio are synced?"

	read allgood
	
else
	echo "File renaming : No transcript folder with given name"
fi

# 4. Preparation of kaldi data

if [ $allgood = "y" ]
then
	echo "Preparing kaldi data !"
	# Change directory to ASR-Auto-Scoring
	cd ../asr-auto-scoring
	echo `pwd`
	#./scripts/run-deliverables.sh --steps 1-3 <path-to-your-text-grid-dir> <path-to-your-wav-file-dir> <path-to-your-kaldi-data-output-dir> <posfix>
	./scripts/run-deliverable.sh --steps 1-3 $trans_store_mono_loc"/$sess_id" $audio_store_mono_loc"/$sess_id" "entire-test-sets/$sess_id/kaldi-formatted-8k" "sgh"
else
	echo "Please recorrect your audio and transcripts !"
fi

