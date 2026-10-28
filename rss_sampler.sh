#!/bin/sh
# Sample RSS of ONE suite run's own processes every 5 s.  A performance figure without a
# memory figure is what produced the kernel kill this issue is about.
#
# Takes the pytest MASTER's pid and samples it and every descendant, so two lanes running
# at once do not sample into each other's file.  The earlier form grepped every
# ``.venv/bin/python3`` on the box, which during an epic is this run's workers plus the
# other lane's plus any stray child -- so its process count and its total belonged to no
# one run, and the epic is exactly when the figure is read.  Measured at
# ``adcp-client-python-10l.31``: a second lane's suite started 32 minutes into the run
# being sampled, and under the old pattern its ten workers would have entered this file
# as if they were the eleventh through twentieth of the run's own.
#
#     ./rss_sampler.sh /tmp/rss.txt "$pytest_pid" &
#
# One line per process per sample: ``<unix seconds> <pid> <rss kB>``.  ``suite_report.py``
# reads it and reports both figures the ceiling question needs -- the per-process peak and
# the peak CONCURRENT total, which is the one the kernel sees.
out="$1"
root="$2"
: > "$out"
while :; do
  ps -eo pid=,ppid=,rss= | awk -v root="$root" -v t="$(date +%s)" '
    { pid[NR]=$1; ppid[$1]=$2; rss[$1]=$3; n=NR }
    END {
      mine[root]=1
      changed=1
      while (changed) {
        changed=0
        for (i = 1; i <= n; i++) {
          p = pid[i]
          if (!(p in mine) && ((ppid[p]) in mine)) { mine[p]=1; changed=1 }
        }
      }
      for (p in mine) printf "%s %s %s\n", t, p, rss[p]
    }' >> "$out"
  sleep 5
done
