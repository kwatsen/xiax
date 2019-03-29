#!/bin/sh

DATE=`date +%Y-%m-%d`
sed -e"s/YYYY-MM-DD/$DATE/" -e'/rc:yang-data/d' xiax-structures-v1.yang > xiax-structures-v1\@$DATE.yang

echo

echo "validating xiax-structures-v1.yang..."
printf "  ^ with pyang..."
response=`pyang --strict --canonical --max-line-length=69 -p ./ietf-modules/ xiax-structures-v1\@$DATE.yang 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  echo
  exit 1
fi
printf "okay.\n"
printf "  ^ with yanglint..."
response=`yanglint xiax-structures-v1\@$DATE.yang 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  echo
  exit 1
fi
printf "okay.\n\n"


# first, we need to create a version of the YANG module without the "rc:yang-data"
# extension (e.g., make it look like it defines protocol-accessible nodes)
#sed '/rc:yang-data/d' xiax-structures-v1\@$DATE.yang > tmp
#mv tmp xiax-structures-v1\@$DATE.yang

echo "validating ex-xiax-block-v1.xml..."
printf "  ^ with yanglint..."
response=`yanglint --verbose --strict xiax-structures-v1\@$DATE.yang ex-xiax-block-v1.xml 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  rm $name 
  echo
  exit 1
fi
printf "okay.\n\n"


echo "validating ex-generate-v1.xml..."
printf "  ^ with yanglint..."
response=`yanglint --verbose --strict xiax-structures-v1\@$DATE.yang ex-generate-v1.xml 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  rm $name 
  echo
  exit 1
fi
printf "okay.\n\n"


echo "validating ex-validate-yang-module-v1.xml..."
printf "  ^ with yanglint..."
response=`yanglint --verbose --strict xiax-structures-v1\@$DATE.yang ex-validate-yang-module-v1.xml 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  rm $name 
  echo
  exit 1
fi
printf "okay.\n\n"


echo "validating ex-validate-xml-document-v1.xml..."
printf "  ^ with yanglint..."
response=`yanglint --verbose --strict xiax-structures-v1\@$DATE.yang ex-validate-xml-document-v1.xml 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  rm $name 
  echo
  exit 1
fi
printf "okay.\n\n"


echo "validating ex-xiax-pis.xml..."
printf "  ^ with yanglint..."
response=`yanglint --verbose --strict xiax-structures-v1\@$DATE.yang ex-xiax-pis.xml 2>&1`
if [ $? -ne 0 ]; then
  printf "failed (error code: $?)\n"
  printf "$response\n\n"
  rm $name 
  echo
  exit 1
fi
printf "okay.\n\n"

echo "YIBA YIBA!"

rm xiax-structures-v1\@$DATE.yang
