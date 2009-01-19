#!/bin/bash

runbib=0
while getopts ":b" Option
do
    case $Option in
	b ) runbib=1; shift
    esac
done

if [ "T$1" == "T" ]
then
    echo "No argument"
    exit
fi

pdflatex "$1"
if [ $runbib -eq 1 ]
then
    bibtex "$1"
    pdflatex "$1"
    pdflatex "$1"
fi
