#!/bin/bash

# a2flac.sh -a artist -l album file1 file2 ...

# Converts individual lossless audio files into flac. Tracknumber and
# title tags are parsed from the filename,
# e.g. 04._Nothing_Else_Matters.ape has title="Nothing Else Matters".

# Requires mplayer, mac, or shn, depending on the source files. Can be
# straightforwardly extended for new file formats.

# http://iki.fi/teknohog/hacks/

# general config
nice=10
flacopts="--best"
target_ext="flac"

while getopts a:l: opt; do
    case "$opt" in
	a) artist="$OPTARG" ;;
	l) album="$OPTARG" ;;
	?) printf "Usage: %s -a artist -l album\n" $0 ;;
    esac
done

if [ ! -n "$album" ] || [ ! -n "$artist" ]; then
    printf "Usage: %s -a artist -l album\n" $0
    exit
fi
shift 4

for infile in "$@"; do

    tracknumber="`echo $infile | sed -e 's/\([AaBb]\?[0-9]\{1,2\}\)[\._-]\+\(.*\)\.\([a-zA-Z0-9]\+\)/\1/' | sed -e 's/_/ /g'`"
    title="`echo $infile | sed -e 's/\([AaBb]\?[0-9]\{1,2\}\)[\._-]\+\(.*\)\.\([a-zA-Z0-9]\+\)/\2/' | sed -e 's/_/ /g'`"
    ext="`echo $infile | sed -e 's/\([AaBb]\?[0-9]\{1,2\}\)[\._-]\+\(.*\)\.\([a-zA-Z0-9]\+\)/\3/' | sed -e 's/_/ /g'`"

    # in case of flac->flac repacking, change the new filename
    if [ "$target_ext" == "$ext" ]; then
	outfile=${infile//.$ext/.new.$ext}
    else
	outfile=${infile//.$ext/.$target_ext}
    fi

    # This could well work with the same pipe for all tracks
    # consecutively. However, I'm not exactly sure of things so I use
    # separate pipes. This also facilitates more parallelism if
    # desired :)
    pipe=`mktemp -u`
    mknod $pipe p

    # mplayer does most codecs well. exceptions can be dealt with here.
    case $ext in
	ape|APE)
	    nice -n$nice mac $infile $pipe -d &
	    ;;
	shn|SHN)
	    nice -n$nice shncat $infile > $pipe &
	    ;;
	wv|WV)
	    nice -n$nice wvunpack $infile -o - > $pipe &
	    ;;
	wav|WAV)
	    cat $infile > $pipe &
	    ;;
	*)
	    nice -n$nice mplayer -ao pcm:fast:file=$pipe "$infile" &
	    ;;
    esac

    nice -n$nice flac "$flacopts" -T artist="$artist" \
	-T tracknumber="$tracknumber" -T title="$title" -T album="$album" \
	-o "$outfile" $pipe && rm $pipe
done
