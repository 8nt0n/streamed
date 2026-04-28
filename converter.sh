#!/bin/bash

shopt -s globstar nullglob

for input in **/*.mkv; do
    output="${input%.mkv}.mp4"
    ffmpeg -i "$input" -c:v libx264 -c:a aac -strict experimental "$output"
done

