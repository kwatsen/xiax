#!/bin/bash

cp -r ../../../automation/* ./
rm Makefile
rm -rf hide tmp

git status ./*

