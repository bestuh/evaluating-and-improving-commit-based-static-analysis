#!/bin/bash

FILE1=$1
gcc -fpreprocessed -dD -E $1.c > $1.txt
