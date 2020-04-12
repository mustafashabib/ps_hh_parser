#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import getopt
import csv
import re
import os
from itertools import groupby

# helper to get command line args for input file path and destination output file
def get_inputfiles_path_and_outputfile_path(argv):
    inputfile_path = ''
    outputfile_path = ''
    expected_format = 'ps_calc.py -i "<inputfile_path>" -o "<outputfile_path>"'
    try:
        opts, _ = getopt.getopt(argv, "hi:o:", ["ifilepath=", "ofilepath="])
    except getopt.GetoptError:
        print(expected_format)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(expected_format)
            sys.exit()
        elif opt in ("-i", "--ifilepath"):
            inputfile_path = arg
        elif opt in ("-o", "--ofilepath"):
            outputfile_path = arg
    if inputfile_path == '' or outputfile_path == '':
        print(expected_format)
        sys.exit(2)
    return (inputfile_path, outputfile_path)

# clean a hand
# remove the pocket card information

def get_clean_hand_log(hand_log):
    return [line for line in hand_log if not line.startswith("Dealt ")]


def process_log(argv):
    (inputfile_path, outputfile_path) = get_inputfiles_path_and_outputfile_path(argv)
    all_hands = []

    for _, _, inputfiles in os.walk(inputfile_path):
        for inputfile in inputfiles:
            with open(os.path.join(inputfile_path, inputfile), 'r', encoding='utf-8') as ps_summary:
                try:
                    all_lines = ps_summary.readlines()
                    all_hands.extend(all_lines)
                except Exception as e:
                    print(f"ERROR: Skipping file {inputfile}", e)

    # divide list grouping on non empty/new lines
    # this effectively creates a list of lists where each element
    # of the parent list is a list of all the details for each hand
    each_hand = [list(sub) for ele, sub in groupby(
        all_hands, key=lambda x: x != '\n') if ele]
    final_hands = []
    # process each hand in the history
    for current_hand in each_hand:
        clean_hand_log = get_clean_hand_log(current_hand)
        final_hands.extend(clean_hand_log)
        final_hands.append('\n\n')
        

    # write out the cleaned hand logs
    clean_hand_history = os.path.join(outputfile_path, f'clean_hh.txt')
    with open(clean_hand_history, 'w') as output:
       output.writelines(final_hands)
    print(f"Removed pocket card information and wrote to clean_hh.txt in {outputfile_path}")


"""main function
"""
if __name__ == "__main__":
    # kick off the script and parse args
    process_log(sys.argv[1:])
