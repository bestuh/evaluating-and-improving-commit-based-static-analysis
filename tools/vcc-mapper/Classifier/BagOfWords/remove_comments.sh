#!/bin/bash

FILE1=$1
gcc -fpreprocessed -dD -E BagOfWords/$1.c > BagOfWords/$1.txt
