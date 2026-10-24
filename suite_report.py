"""Per-worker totals and peak RSS for one xdist run.

Wall clock comes from pytest's own summary line.  The slowest-WORKER total is the
figure the exit condition asks for, and it needs two inputs xdist splits across two
artifacts: the junit XML carries a duration per nodeid and the verbose stdout carries
the ``[gwN]`` that ran it.
"""
import collections, re, sys, xml.etree.ElementTree as ET

log, junit, rss = sys.argv[1], sys.argv[2], sys.argv[3]

dur = {}
for tc in ET.parse(junit).getroot().iter("testcase"):
    nodeid = f"{tc.get('classname','').replace('.','/')}.py::{tc.get('name')}"
    dur[tc.get("name")] = float(tc.get("time", 0))

worker = {}
pat = re.compile(r"^\[(gw\d+)\] \[\s*\d+%\] \w+ (\S+)")
for line in open(log, errors="replace"):
    m = pat.match(line.strip())
    if m:
        worker[m.group(2)] = m.group(1)

per = collections.Counter()
unattributed = 0.0
for nodeid, gw in worker.items():
    name = nodeid.split("::", 1)[-1]
    per[gw] += dur.get(name, 0.0)
for name, d in dur.items():
    pass
print("tests with a worker:", len(worker), "of", len(dur), "junit testcases")
for gw, total in per.most_common():
    print(f"  {gw:6s} {total:9.1f} s  {sum(1 for n,w in worker.items() if w==gw):5d} tests")
if per:
    print(f"SLOWEST WORKER: {per.most_common(1)[0][0]} at {per.most_common(1)[0][1]:.1f} s")
    print(f"SUM OF ALL WORKERS: {sum(per.values()):.1f} s")

peak = collections.defaultdict(float)
for line in open(rss, errors="replace"):
    parts = line.split()
    if len(parts) == 3:
        peak[parts[1]] = max(peak[parts[1]], float(parts[2]) / 1024)
if peak:
    vals = sorted(peak.values(), reverse=True)
    print(f"PEAK RSS per process, MB: max {vals[0]:.0f}, median {vals[len(vals)//2]:.0f}, "
          f"min {vals[-1]:.0f}, over {len(vals)} processes")
    print("  top:", ", ".join(f"{v:.0f}" for v in vals[:12]))
