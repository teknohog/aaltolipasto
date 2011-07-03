aaltolipasto -- a collection of scripts for lossless audio files,
primarily flac, for unix command line

by Risto A. Paju / teknohog

aalto = wave, lipasto = drawer (the kind where you store things).
The name is also a pun in Finnish.

See the scripts themselves for detailed documentation and
requirements.


flacsplit.py
------------

Splits a single-file album into songs, according to a cue file. The
files are named according to song titles, and tagged appropriately.

The default is to output best-quality flac, but it should be simple to
change this.


a2flac.sh
---------

Converts any audio files to flac, though it mainly makes sense when
the source files are lossless. The output files are tagged
appropriately: the title is parsed from the filename, and the artist
and album must be specified on the command line.
