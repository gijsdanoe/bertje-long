#!/bin/bash
FILES=./results/tmp/*
for f in $FILES
do
  cut -f1,2,7,8 $f > $f.clean
  mv $f.clean $f
  # take action on each file. $f store current file name
done
