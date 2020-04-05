#!/bin/bash

for roo in {{218..221},232};
do for col in {a..d};
    do for row in {1..6};
    do ping -c 1 lab$roo-${row}0$col.cs.curtin.edu.au.
    done
    done
done
cd BotFiles
python3 CurtinLabBot.py