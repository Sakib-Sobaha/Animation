#!/usr/bin/env bash
tput civis
trap 'tput cnorm; tput sgr0; clear; exit' INT TERM EXIT

# Playfield size (leave one row for your shell prompt)
W=$(tput cols); H=$(( $(tput lines) - 1 ))

x=2; y=2; dx=1; dy=1
prev_x=$x; prev_y=$y

clear
while :; do
  # Erase previous dot
  tput cup "$prev_y" "$prev_x"; printf " "

  # Update pos
  x=$(( x + dx )); y=$(( y + dy ))

  # Bounce on edges
  (( x <= 1 || x >= W-1 )) && dx=$(( -dx ))
  (( y <= 1 || y >= H-1 )) && dy=$(( -dy ))

  # Draw new dot
  tput cup "$y" "$x"; printf "\033[1;36m●\033[0m"

  prev_x=$x; prev_y=$y
  sleep 0.01
done
