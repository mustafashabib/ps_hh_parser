# Pokerstars Hand History Summarizer

Pokerstars home games take rake even on play money, making it hard to track.

If you record your hand history, this script will recalculate actual chips won/lost per player for every hand and for the entire game.

We have multiple hand histories for every player provided to make sure we don't miss any hands so this script also makes sure to only process hands once since they may appear multiple times in several people's hand history files. 

This also includes a file to clean up the holecard information in case you want to share your hand histories with people.

## How to use

### Clean Hand Histories 
~~~shell
> python3 ps_clean.py -i {directory_containing_games_hand_history_files} -o {outputpath}
~~~

For example, if you save all hand histories to the path `/poker/hands` and want to write everything out to `/poker/clean` then:

~~~shell
> python3 ps_clean.py -i '/poker/hands' -o '/poker/clean'
~~~

This will  combine all of your hand history files into one file without your hole card information to `/poker/clean/clean_hh.txt`

### Calc Net
~~~shell
> python3 ps_calc.py -i {directory_containing_games_hand_history_files} -o {outputpath}
~~~

For example, if you save all hand histories to the path `/poker/clean` and want to write everything out to `/poker/calc` then:

~~~shell
> python3 ps_calc.py -i '/poker/clean' -o '/poker/calc'
~~~

Two outputfiles will be created in `{outputpath}`
1. `hand_by_hand.csv`: Every hand's winners and total rake 
2. `summary.csv`: A summary of every players' totals for the entire game.

