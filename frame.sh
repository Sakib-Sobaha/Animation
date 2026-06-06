#!/usr/bin/env bash
frames=(
"  (•_•)      "
" \(•_•)      "
"  \(•_•)     "
"   \(•_•)    "
"    \(•_•)   "
"     \(•_•)  "
"      \(•_•) "
"       \(•_•)"
"      /(•_•) "
"     /(•_•)  "
"    /(•_•)   "
"   /(•_•)    "
"  /(•_•)     "
" /(•_•)      "
)
tput civis
trap 'tput cnorm; tput sgr0; echo; exit' INT TERM EXIT
while :; do
  for f in "${frames[@]}"; do
    printf "\r\033[1;35m%s\033[0m" "$f"
    sleep 0.05
  done
done
