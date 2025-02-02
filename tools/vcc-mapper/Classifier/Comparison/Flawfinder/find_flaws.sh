#!/bin/bash

for path in $(git diff --name-only $1~ $1)
do
	install -D /dev/null $path
	git diff --output=recent.patch $1~:$path $1:$path
	git show $1:$path > $path
	flawfinder -D -P recent.patch $path || flawfinder -D $path
	rm $path
	rm recent.patch
done