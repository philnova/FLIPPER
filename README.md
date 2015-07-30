# FLIPPER
Simple command line and GUI-based utility to process fluorescent plate reader data (e.g. FlexStation)

Fluorescent plate readers (FLIPR), such as the FlexStation3, measure the fluorescence value on a microplate at one or more time points. This can be used to quantify fluorescent samples or, with the aid of a fluorescent indicator, measure changes in cells grown on a plastic matrix.
https://en.wikipedia.org/wiki/Plate_reader

FLIPR is a medium-throughput technology with capacity to generate large amounts of data per day, typically exported to a txt file. In order to perform statistics on FLIPR data, typically one wants to: 
1) compare a baseline of readings taken before a treatment to a response set of readings after the treatment
2) combine multiple wells into replicates in order to analyze statistically
However, existing software packaged with the plate reader typically does not perform these functions, and doing so is tedious in Excel.

To facilitate these tasks, I have developed two tools:
1) simple_flipr: a command-line tool
2) flipr_tdt_gui: a GUI-based tool

SIMPLE FLIPR

simple_flipr.py has no dependencies and can be run directly from the command line. The purpose of simple_flipr is to organize plate read data into a convenient format for further analysis, i.e. with a spreadsheet or other script. See the file itself for detailed documentation.

FLIPR_TDT_GUI

flipr_tdt_gui requires Tkinter and my script flipr_tdt as dependencies. It is compatible with Python 3 or 2.7.

The purpose of flipr_tdt_gui is to fully automate the statistical analysis of plate read data. The user can combine wells into replicates, either manually or following some predetermined pattern (e.g. combine each well with the well below), and export a text file of statistics (mean, SEM), and plots for fluorescence changes across the entire plate and for each replicate.
