#!/bin/bash

DATE=`date +%Y-%m-%d`

sed -e"s/YYYY-MM-DD/$DATE/" xiax-block.yang > xiax-block\@$DATE.yang

pyang -f tree --tree-line-length 71 --tree-print-yang-data xiax-block\@*.yang > xiax-block-tree.txt

rm xiax-block\@*.yang
