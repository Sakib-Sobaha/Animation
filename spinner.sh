#!/usr/bin/env bash
frames='|/-\'
i=0
tput civis
trap 'tput cnorm; tput sgr0; echo; exit' INT TERM EXIT
while :; do
  printf "\r\033[1;32m[%c]\033[0m Working..." "${frames:i++%${#frames}:1}"
  sleep 0.1
done
