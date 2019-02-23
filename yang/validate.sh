#!/bin/bash

DATE=`date +%Y-%m-%d`
sed -e"s/YYYY-MM-DD/$DATE/" xiax-block.yang > xiax-block\@$DATE.yang

echo

echo "validating xiax-block.yang..."
printf "  ^ with pyang..."
response=`pyang --strict --canonical --max-line-length=69 xiax-block\@*.yang 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  echo
  exit 1
fi
printf "okay.\n"
printf "  ^ with yanglint..."
response=`yanglint xiax-block\@*.yang 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  echo
  exit 1
fi
printf "okay.\n\n"


echo "validating ex-xiax-block.xml..."

# first, we need to create a version of the YANG module without the "yang-data"
# extension (e.g., make it look like it defines protocol-accessible nodes)
name="xiax-block\@*.yang"
numlines=`wc -l $name | awk '{print $1}'`
delline=`expr $numlines - 1`  # hope it doesn't move!
awk "NR%$delline" $name > $name.2
sed -e '/rc:yang-data/d' $name.2 > $name
rm $name.2 

printf "  ^ with yanglint..."
response=`yanglint --verbose --strict xiax-block\@*.yang ex-xiax-block.xml 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  rm $name 
  echo
  exit 1
fi
printf "okay.\n"


rm xiax-block\@*.yang
