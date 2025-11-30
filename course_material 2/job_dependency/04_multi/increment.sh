# This scripts stores a sequence of N numbers in a text file with name numbers_ID.txt.
# If the file numbers_ID.txt doesn't exist, then it is created and the sequence of N numbers starts from 1.
# If the file numbers_ID.txt exists, then the sequence of N numbers starts from the last number stored in numbers_ID.txt.

# The scripts requires 2 arguments:
# 1- ID the identification number of the file (for simultaneus running)
# 2- N number elements on the sequence

# Example: bash increment.sh 0 30
# This will store a sequence of 30 numbers in a file with name numbers_0.txt

if [ "$#" -ne 2 ]; then
    echo " This scripts stores a sequence of N numbers in a text file with name numbers_ID.txt.
If the file numbers_ID.txt doesn't exist, then it is created and the sequence of N numbers starts from 1.
If the file numbers_ID.txt exists, then the sequence of N numbers starts from the last number stored in numbers_ID.txt.

The scripts requires 2 arguments:
1- ID the identification number of the file (for simultaneus running)
2- N number elements on the sequence

Example: bash increment.sh 0 30
This will store a sequence of 30 numbers in a file with name numbers_0.txt." 1>&2
exit
fi
ID=$1
N=$2
filename=numbers_${ID}.txt
current_number=0
if [ -f "$filename" ]; then
    current_number=$(tail -n 1 $filename)
fi

for i in $(seq 1 $N)
do
    current_number=$((current_number + 1))
    echo $current_number | tee -a $filename
    sleep 1
done
