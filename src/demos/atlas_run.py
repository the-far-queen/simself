"""
atlas_run.py — Atlas Exam runner CLI (per Grok master plan Step 4).

Usage:
    python atlas_run.py [--out path/to/snapshot.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Add the repo's src/ to sys.path so 'constitutional.atlas_exam' resolves
# regardless of cwd. (The previous version hardcoded C:/Users/Admin/simself/src
# which only worked on one machine.)
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, os.pardir))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from constitutional.atlas_exam import AtlasExam


def main(argv):
    p = argparse.ArgumentParser(description="Run the 5-item Atlas Exam and publish the score.")
    p.add_argument("--out", default=None, help="Write JSON report here.")
    args = p.parse_args(argv)

    exam = AtlasExam()
    report = exam.run(snapshot_path=args.out)
    print(json.dumps(report, indent=2))
    score_line = "SCORE: " + str(report["score"]) + "/" + str(report["total"])
    print()
    print(score_line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
