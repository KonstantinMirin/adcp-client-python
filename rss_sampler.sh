#!/bin/sh
# Sample RSS of every worker process of the suite every 5 s.  A performance figure
# without a memory figure is what produced the kernel kill this issue is about.
out="$1"
: > "$out"
while :; do
  ps -eo pid,rss,args | grep '[.]venv/bin/python3' | awk -v t="$(date +%s)" '{printf "%s %s %s\n", t, $1, $2}' >> "$out"
  sleep 5
done
