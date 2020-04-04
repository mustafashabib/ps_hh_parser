# Pokerstars Hand History Summarizer

Pokerstars home games take rake even on play money, making it hard to track.

If you record your hand history, this script will recalculate actual chips won/lost per player for every hand and for the entire game.

## How to use

~~~shell
> python3 ps_calc.py -i {games_hand_history_file} -o {outputfile}
~~~

Two outputfiles will be created. 
1. `{outputfile}` will contain every hand's winners and total rake
2. `summary_{outputfile}` will contain a summary of every players totals for the entire game.

