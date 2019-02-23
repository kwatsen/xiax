#!/bin/bash

DATE=`date +%Y-%m-%d`

sed -e"s/YYYY-MM-DD/$DATE/" xiax-block-v1.yang > xiax-block-v1\@$DATE.yang

pyang -f tree --tree-line-length 71 --tree-print-yang-data xiax-block-v1\@*.yang > tree.txt

rm xiax-block-v1\@*.yang
