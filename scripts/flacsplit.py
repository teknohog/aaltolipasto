#!/usr/bin/env python
# -*- python -*-

"""
flacsplit.py by TeknoHog aaattt iki dddooottt fi

Release 20090608

#############################################################
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
##############################################################

flacsplit.py takes a compressed audio file that contains multiple
tracks, and splits it according to a cue file. The output files are
renamed and tagged according to information in the cue file.

This is a wrapper for shnsplit (part of shntool) and also requires
software specific for the file types. For example Monkeys Audio
(ape) files require mac, and FLAC requires the flac suite.

For mp3 files, there exists a program named mp3cue, part of a
package called poc. It does splitting and tagging by itself, and you
won't need this wrapper.

My default settings are for flac output, and the input can be anything
that shntool understands (as long as you have the software for reading
it). Output should be easily convertible for other formats, if you
change the settings below accordingly.

Note: shntool version 3 changed some option syntaxes, and this script
uses the new ones. Namely:
* Prefix option is '-a' instead of '-n'
* Track number is NN instead of NNN. Makes sense as CD tracks are < 100.
"""

#####################################################################
# Settings
#####################################################################

# output type (with possible options) for shnsplit
outtype = "flac flac --best - -o %f"

# output filename extension
ext = "flac"

# audiofiles to search in case of autofind
# (case-insensitive regular expression)
autofind_audio_ext = "ape|flac|wav|wv"

# This can be changed for other file formats. Check the 'tags'
# variable below for the available tags.
metadata_cmdline_template = 'metaflac --set-tag=TRACKNUMBER="%trackno" --set-tag=TITLE="%title" --set-tag=ARTIST="%artist" --set-tag=ALBUM="%album"'

# dummy temporaries
temp_prefix = "track"

# final output
filename_template = "%trackno.%title.%ext"

# unix priority
nice = "10"

######################################################################
# Code -- should not be changed for the usual settings
######################################################################

# required format for shnsplit
tempoutfile_template = "%temp_prefix%trackno.%ext"

tags = ["artist", \
        "album", \
        "title", \
        "trackno", \
        "ext", \
        "temp_prefix", \
        ]

import os, re, sys, tempfile, shutil
from optparse import OptionParser

def ReadLines(file):
    File = open(file, "r")
    contents = File.readlines()
    File.close()
    return contents

def WriteFile(filename, content):
    File = open(filename, "w")
    File.write(content)
    File.close()

def CueFind(cuelist, pattern, showkey = False):
    output = []
    for line in cuelist:
        if re.search(pattern, line):
            if not showkey:
                line = re.sub(pattern, "", line)
                
            # remove leading spaces in any case, for shntools compatibility
            line = re.sub("^ +", "", line)

            # linebreaks are also bad. they can be put back upon
            # joining to string, if needed. (using string = "\n".join(list))
            line = re.sub(r"\r?\n$", "", line)

            # remove quotes from around the value (assuming there are
            # no quotes as part of the value... :)
            line = re.sub(r'"', "", line)
            
            output.append(line)
    return output

def FindFirst(ext):
    # Case insensitive search for the first file with the given
    # extension. This should also work with multiple possible
    # extensions, such as ape|flac|wav.
    pattern = ".*\.(" + ext + ")$"
    for item in os.listdir("."):
        if re.match(pattern, item, re.I):
            return item

    # A sensible fallback is needed for the os.path.isfile test; null
    # does not work
    return ""


# new, flexible cmdline input :)
parser = OptionParser()

parser.usage = """%prog -c CUEFILE ( AUDIOFILE | -n ) | -a

Splits a lossless audio file into individual tracks according to the
cue file. The track files are tagged and renamed accordingly."""

parser.add_option("-a", "--auto", dest="autofind", action="store_true", default=False, help="Try to find cue and audio files in the current dir, and use the first ones")

# A sensible default is needed for the os.path.isfile test; null does not work
parser.add_option("-c", "--cuefile", dest="cuefile", default="", help="Cue file")

parser.add_option("-n", "--nosplit", dest="nosplit", action="store_true", default=False, help="Do not perform the audio split. Useful if the cuefile has missing tags and you end up with " + temp_prefix + "NN." + ext + " files. You can fix the cuefile and run this again with nosplit, to tag and rename these files (which is much faster than a complete split).")

(options, args) = parser.parse_args()

# Perhaps autofind could apply to either the cuefile or the audiofile,
# if the other is given. But this is pretty much useless. Once you
# start defining filenames by hand, it shouldn't be hard to define
# them both.

# The audiofile is not needed in case of nosplit
if options.autofind:
    cuefile = FindFirst("cue")
    if not options.nosplit:
        inputfile = FindFirst(autofind_audio_ext)
elif os.path.isfile(options.cuefile):
    cuefile = options.cuefile
    if not options.nosplit:
        inputfile = args[0]
else:
    parser.error("argument error")
    sys.exit()

if not os.path.isfile(cuefile):
    print("Cuefile not found, exiting")
    sys.exit()

cue = ReadLines(cuefile)

# default operation: do the shnsplit, but first prepare a new
# temporary cue file

if not options.nosplit:
    if not os.path.isfile(inputfile):
        print("Audiofile not found, exiting")
        sys.exit()
    
    cuetimes = CueFind(cue, "INDEX 01", True)

    # First INDEX 01 must have the time 00:00:00, otherwise shnsplit screws up!
    cuetimes[0] = "INDEX 01 00:00:00"
    
    cuetimestring = "\n".join(cuetimes) + "\n"
    
    cuetempfile = tempfile.mktemp(".txt")
    
    splitter_args = ["nice", "-n", nice, "shnsplit", "-f", cuetempfile, "-a", temp_prefix, "-o", outtype, inputfile]
    
    WriteFile(cuetempfile, cuetimestring)
    os.spawnvp(os.P_WAIT, splitter_args[0], splitter_args)
    os.remove(cuetempfile)

# The indexing of TITLEs in a cue file is a little strange, since the
# first TITLE is album name, and the rest are song titles. But it's
# actually quite handy when taken as a list whose index begins with
# zero: then Nth track == titles[N]. Same goes for PERFORMER.

artists = CueFind(cue, "PERFORMER", False)

titles = CueFind(cue, "TITLE", False)

album = titles[0]

# characters changed/removed in filename
transtable = { \
    "[": "", \
    "]": "", \
    "(": "", \
    ")": "", \
    "<": "", \
    ">": "", \
    "/": "", \
    " ": "_", \
    }

# metadata tagging

for trackno in range(1, len(titles)):
    title = titles[trackno]

    # this should work for multi-artist as well as single artist discs
    artist = artists[trackno]

    # convert to constant length string
    if trackno < 10:
        trackno = "0" + `trackno`
    else:
        trackno = `trackno`

    # copy template into variable, then replace %tags by their
    # contents one at a time
    
    for variable in ["filename", "metadata_cmdline", "tempoutfile"]:
        exec variable + " = " + variable + "_template"
        
        for tag in tags:
            tag_content = eval(tag)
            tag_marker = "%" + tag
            exec variable + " = " + variable + ".replace(tag_marker, tag_content)"

    # clean up filename
    for key in transtable.keys():
        filename = filename.replace(key, transtable[key])

    os.system(metadata_cmdline + " \"" + tempoutfile + "\"")

    shutil.move(tempoutfile, filename)
