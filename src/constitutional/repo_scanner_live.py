"""
repo_scanner_live.py -- THE SCANNER THAT ACTUALLY SCANS, AIMED AT WHAT
SIMSELF COULD BECOME.

THE GAP THIS FILLS, and it was MEASURED, not assumed
-----------------------------------------------------
`constitutional/repo_scanner.py` is described in the 2026-10-06 handoff
as *"cron-ready scanner with 8 canonical repos"*, and it is
cron-ready in the way that a stub is cron-ready: **it never makes a
network call.** MEASURED, 2026-10-31: a grep for `urllib`, `requests`,
`api.github` and `gh ` in that file returns NOTHING. Its only data
source is `CANONICAL_REPOS`, a hardcoded list of 8 repos whose star
counts are frozen at the moment somebody typed them.

So the daily scavenge (`wiring.py::daily_scavenge`) has been reporting
the same 8 repos every day since 2026-10-06. **The loop's SCAN stage
was a fixture.**

WHAT THE SCAN IS AIMED AT, and this is the part that matters
-------------------------------------------------------------
Bobby, 2026-10-31: *"your scan should focus on what you need to build
fc atlas simself -- eventually you will become proactive, seeking what
you need"*, and: *"nope, that is a start -- i mean you investigate what
simself could BE and use new starred repos to get ideas."*

So the scan is NOT aimed at a fixed topic list. The topic list is the
FLOOR, and it comes from two measured places:

  THE FLOOR   the Atlas Exam's unimplemented areas. MEASURED by
               running it: **8 of 23 areas are TODO** -- 7
               (reconciliation), 11 (interface), 12 (resource), 13
               (adversarial), 19 (tools), 20 (skills), 21 (initiative),
               22 (planning). Each names what it does not establish,
               and each is a thing the substrate cannot yet do.

  THE HORIZON what simself could BECOME. MEASURED from the repo's own
               README: 10 letters run (A core, B self-model, C sim
               world, D SNR training, E family/external, I interface,
               L sacred library, M modulator, Q qualification, S
               security) and 4 do not exist yet -- alpha (human
               bridge), beta (parameter self-optimisation), gamma
               (bio-system interface), delta (parameter
               self-modification).

  AND TWO OF THE FOUR ARE PARKED, at Bobby's direction 2026-10-31:
  *"skip human bridge and bio interface for now"*. So alpha and gamma
  are NOT demands, and their topics are not queried. They are kept
  here as PARKED, so the choice is recorded rather than forgotten --
  a demand removed silently is a demand lost.

So the query set is the union of what is live, and the scan reports
which demand each hit serves. A repo is not just "a repo with stars";
it is a candidate for a specific unmet need.

THE STAR FLOOR, and why it is not the only filter
--------------------------------------------------
Stars are the SNR signal Bobby named ("by stars"), and they are used
for ORDER and for the small-bite budget. They are NOT a truth signal:
a 40,000-star repo can still contain a Hodge decomposition with
spectral radius 7.0. So a repo needs stars to be considered, and the
gate decides whether it is any good.

AND THE OUTLIER RULE, from `ingest_targets.py`: a language outside
the declared set is not refused on that ground alone -- it qualifies if
its stars are a declared outlier. So the scanner does not filter on
language; it reports language and lets the ranking decide.

WHAT IT DOES NOT DO, and this is a boundary rather than a gap
-------------------------------------------------------------
It does not splice code into the repos. The sandbox half of
self-coding is still owed (atlas exam area 18). What this module
produces is the CANDIDATE LIST, the demand mapping, and the manifest
-- the evidence for the proposals, which is the part that was missing.

THE CREDENTIAL
--------------
The token is read from the vault file
`vault/20-writing/github-token-2026-09-26.md`, which is where Bobby
stored it on 2026-10-26 ("store it"). It is never printed, never
written to a manifest, and never logged. The file's own rule: DO NOT
paste in chat, DO NOT put in config.yaml / .env / .netrc.

THE TWO FAILURE MODES, and both are handled
--------------------------------------------
  NO CREDENTIAL   the scan degrades to the canonical list and SAYS SO.
                  A silent fallback would look like a working scan that
                  found nothing new -- the failure this project keeps
                  fighting.

  API ERROR       the exception is recorded with its type, and the scan
                  reports partial results rather than raising.

THE DIFFERENCE FROM YESTERDAY'S MANIFEST, and it is the point
-------------------------------------------------------------
The manifest records what was seen. The point of a DAILY scan is the
DIFF: which repos are new, which have grown, which changed their
topics. So `diff_manifests` is here, and it is what makes the daily
cadence worth anything rather than a re-print of yesterday.

Run:
    python src/constitutional/repo_scanner_live.py
    python src/constitutional/repo_scanner_live.py --scan-only
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

#: The scanner's own vocabulary is IMPORTED, not copied, so the two
#: cannot drift.
try:
    from constitutional.repo_scanner import (
        CANONICAL_REPOS,
        FIELDCORE_TOPICS,
        SIMSELF_TOPICS,
        ScanManifest,
        ScannedRepo,
        matches_any,
        scan_from_cache,
        write_manifest,
    )
except Exception:  # noqa: BLE001
    from .repo_scanner import (  # type: ignore
        CANONICAL_REPOS,
        FIELDCORE_TOPICS,
        SIMSELF_TOPICS,
        ScanManifest,
        ScannedRepo,
        matches_any,
        scan_from_cache,
        write_manifest,
    )

#: The HERMES home, and the vault path where the token lives.
_HERMES = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
TOKEN_FILE = os.path.join(_HERMES, "vault", "20-writing",
                          "github-token-2026-09-26.md")

API_SEARCH = "https://api.github.com/search/repositories"

#: How many results per topic query. The small-bite budget is 3, so
#: asking for more than a handful per topic is wasted calls -- but the
#: scan must SEE enough to find the ones that will be admitted, so this
#: is deeper than the budget on purpose.
PER_PAGE = 30

UA = "sacred-library-repo-scanner/2.0 (fieldcore+simself)"


# ===========================================================================
# THE DEMAND -- what simself could BECOME, and what it cannot YET do
# ===========================================================================

#: THE HORIZON: the letters that do not exist yet.
#:
#: MEASURED from simself/README.md, 2026-10-31: 10 letters run and 4
#: are "not yet built" -- alpha (human bridge, multi-species
#: interface), beta (parameter self-optimisation, reactivation/field),
#: gamma (bio-system interface: cetacean, reptile, plant, fungi), delta
#: (parameter self-modification, engine).
#:
#: AND THE POINT OF THE SCAN, in Bobby's words: "investigate what
#: simself could BE and use new starred repos to get ideas". So each
#: demand carries the topics that would serve it, and a hit is
#: reported as a candidate FOR THAT DEMAND -- not as a generic repo.
HORIZON_DEMANDS: Dict[str, Dict[str, Any]] = {
    "beta_parameter_self_optimisation": {
        "letter": "beta",
        "what": "parameter self-optimisation: reactivation / field",
        "topics": (
            "hyperparameter-optimization", "automl", "bayesian-optimization",
            "neural-architecture-search", "meta-learning", "continual-learning",
            "parameter-efficient", "lora", "peft",
        ),
    },
    "delta_parameter_self_modification": {
        "letter": "delta",
        "what": "parameter self-modification: the engine",
        "topics": (
            "program-synthesis", "self-modifying-code", "code-generation",
            "genetic-programming", "self-improving-ai", "automated-programming",
            "synthesis",
        ),
    },
}

#: THE PARKED DEMANDS, and the reason.
#:
#: Bobby, 2026-10-31: *"skip human bridge and bio interface for now"*.
#:
#: THEY ARE KEPT HERE, NOT DELETED, and the difference matters. A
#: demand removed silently is a demand lost -- and the next session
#: would not know whether alpha and gamma were parked or abandoned.
#: So they carry `parked=True` and a reason, and the scanner does not
#: query their topics.
PARKED_DEMANDS: Dict[str, Dict[str, Any]] = {
    "alpha_human_bridge": {
        "letter": "alpha",
        "what": "the human bridge: a multi-species interface",
        "parked": True,
        "parked_reason": "Bobby 2026-10-31: 'skip human bridge and bio "
                         "interface for now'",
        "topics": (
            "human-robot-interaction", "brain-computer-interface",
            "neural-interface", "human-robot", "bci", "assistive-technology",
            "embodied-cognition", "human-ai",
        ),
    },
    "gamma_bio_system_interface": {
        "letter": "gamma",
        "what": "the bio-system interface: cetacean, reptile, plant, fungi",
        "parked": True,
        "parked_reason": "Bobby 2026-10-31: 'skip human bridge and bio "
                         "interface for now'",
        "topics": (
            "bioacoustics", "marine-biology", "cetacean", "bioinformatics",
            "plant-communication", "mycology", "bio-sensing", "biosensors",
            "neuroethology",
        ),
    },
}

#: THE FLOOR: the Atlas Exam's unimplemented areas. MEASURED by running
#: `python src/exam.py --run` on 2026-10-31: **8 of 23 areas are TODO**
#: -- 7 reconciliation, 11 interface, 12 resource, 13 adversarial, 19
#: tools, 20 skills, 21 initiative, 22 planning. Each area names what
#: it does not establish, and each is something the substrate cannot
#: yet do.
#:
#: The topics are the ones whose repos would show how that capability
#: is actually built elsewhere.
FLOOR_DEMANDS: Dict[str, Dict[str, Any]] = {
    "area_07_reconciliation": {
        "area": 7,
        "what": "reconciliation: two derivations must agree",
        "topics": ("consistency-checking", "model-checking", "property-based-testing",
                   "formal-verification", "differential-testing", "metamorphic-testing"),
    },
    "area_11_interface": {
        "area": 11,
        "what": "the interface: swapping the model must leave areas 1-10 unchanged",
        "topics": ("model-agnostic", "adapter", "llm-interface", "inference-engine",
                   "model-serving", "abstraction-layer"),
    },
    "area_12_resource": {
        "area": 12,
        "what": "resource bounds: ops per observation, memory growth, time budget",
        "topics": ("memory-profiling", "performance-analysis", "resource-monitor",
                   "profiling", "benchmarking", "load-testing"),
    },
    "area_13_adversarial": {
        "area": 13,
        "what": "adversarial: do the bounds hold under a crafted attack",
        "topics": ("adversarial-machine-learning", "fuzzing", "red-team",
                   "adversarial-examples", "penetration-testing", "robustness"),
    },
    "area_19_tools": {
        "area": 19,
        "what": "tools: acting on something outside the process and observing it",
        "topics": ("robotics", "ros", "sandbox", "container-runtime",
                   "tool-use", "function-calling", "agent-tools"),
    },
    "area_20_skills": {
        "area": 20,
        "what": "skills: an unseen skill assembled from declared primitives",
        "topics": ("compositional", "skill-library", "plugin-system",
                   "composition", "modular-architecture", "capability-discovery"),
    },
    "area_21_initiative": {
        "area": 21,
        "what": "initiative: unrequested action, without being unsafe",
        "topics": ("active-learning", "self-directed", "autonomous-agent",
                   "goal-generation", "intrinsic-motivation"),
    },
    "area_22_planning": {
        "area": 22,
        "what": "planning: ordered steps, dependencies, partial failure, rollback",
        "topics": ("planning", "task-planning", "workflow-orchestration",
                   "dag", "scheduler", "checkpointing"),
    },
}

#: THE CORE -- the four sheaves and the letters that run. These are not
#: "needs"; they are the substrate the demands build ON, so a repo that
#: serves them is a candidate for the CORE rather than for a letter.
CORE_DEMANDS: Dict[str, Dict[str, Any]] = {
    # AND THE TWO STUBS, and they are STUBS AND NOT SMALL SHEAVES.
    #
    # Bobby, 2026-11-07: *"nah skip godot too just stub lets get fc
    # working just self coding scavenge integrate and simself so just
    # two sheafs and two stubs"*.
    #
    # **AND A STUB THAT SCANS GITHUB FOR ITSELF IS NOT A STUB.** A
    # stub's topics are EMPTY, so the scanner does not spend the query
    # budget looking for what the substrate does not do -- and the
    # day's artifact shows the topics_requested drop, which is the
    # honest measure of what was given up.
    #
    # **AND THE STUB DECLARES WHAT IT IS NOT.** The fc's rule: a stub
    # that claims to be more than it is is the sin this project is
    # built to refuse. So each one names the three things it is not and
    # the measurement that would make it real.
    "sheaf_topology": {
        "letter": "TOPOLOGY",
        "what": "the geometric substrate: manifold, Hodge, gradient flow",
        "status": "stub",
        "not_yet": (
            "the stalk substrate's geometry is RELATIONAL -- every stalk "
            "is defined by what it attaches to, and there is NO absolute "
            "frame: MEASURED 2026-11-07, zero mentions of origin, base, "
            "home, anchor or centre across stalk_topology.py, locus.py, "
            "wound_core.py and radial.py, and the locus's own docstring "
            "says the scale is arbitrary and what carries the "
            "information is the RELATIVE amplitude",
            "the locus's PHYSICS is the substrate's and the coupling "
            "between the locus interface and the stalk substrate is "
            "the next build -- locus.py says so in its own words",
            "the robot's body was measured in Godot on 2026-11-07 and "
            "then PARKED by bobby's instruction, so the simulation "
            "exists and is not wired"),
        "would_be_real_when": (
            "the stalk substrate carries an absolute frame AND the "
            "locus's coordinate is READABLE from it, and the read is "
            "a measurement rather than a convention"),
        "topics": (),
    },
    "sheaf_mltr": {
        "letter": "MLTR",
        "what": "the machine language technical register: bounded, generative",
        "topics": ("formal-language", "grammar", "nlp", "tokenization",
                   "semantic-parsing", "type-theory", "dsl",
                   "machine-language-technical-register", "psb"),
    },
    "sheaf_mte": {
        "letter": "MTE",
        "what": "the edge: English and 193 other tongues",
        "status": "stub",
        "not_yet": (
            "the MTE is a SLOT-PATTERN COMPILER, not a sentence reader: "
            "MEASURED 2026-11-07, compile_span(span, pattern) needs a "
            "PATTERN and the token count must EQUAL the slot count",
            "the English-deciphering role is PLAYED BY THE AGENT for "
            "now -- bobby: 'you minimax llm are mte for now' -- and "
            "coding it into the MTE is a task bobby deferred",
            "the learned vocabulary is 3,075 verbs and 8,231 nouns in "
            "its own registry, and there is NO map from a learned "
            "surface form to a primitive, so the composition path "
            "cannot be found for an arbitrary English sentence"),
        "would_be_real_when": (
            "a slot pattern exists for the sentence shapes the "
            "substrate must read, and the learned vocabulary resolves "
            "into one, and the round trip compiles and restores"),
        "topics": (),
    },
    "sheaf_coding": {
        "letter": "CODING",
        "what": "the coding sheaf: github / arxiv / hf, by stars",
        "topics": ("code-generation", "program-analysis", "code-search",
                   "repository-search", "software-composition",
                   "constitutional-ai", "atlas-exam", "agent-runtime",
                   "gate"),
    },
}

#: Every demand that is LIVE.
LIVE_DEMANDS: Dict[str, Dict[str, Any]] = {}
LIVE_DEMANDS.update(HORIZON_DEMANDS)
LIVE_DEMANDS.update(FLOOR_DEMANDS)
LIVE_DEMANDS.update(CORE_DEMANDS)

#: Every demand, live or parked.
ALL_DEMANDS: Dict[str, Dict[str, Any]] = {}
ALL_DEMANDS.update(LIVE_DEMANDS)
ALL_DEMANDS.update(PARKED_DEMANDS)


def demand_topics() -> Tuple[str, ...]:
    """every topic the LIVE demands ask for, de-duplicated.

    AND THE PARKED DEMANDS ARE EXCLUDED. That is the point of parking
    them: their topics are not queried, so their repos do not come
    back, so they do not consume the small-bite budget.

    AND THE ORDER IS THE PRIORITY ORDER, because the API has a hard
    ceiling and the ceiling is the budget.
    """
    out: Set[str] = set()
    for d in LIVE_DEMANDS.values():
        out.update(t.lower() for t in d["topics"])
    # the repo's own topic sets are ALSO demands -- the ones the
    # scanner already knew about. They are included so the scanner's
    # vocabulary and the demands' vocabulary cannot drift apart.
    out.update(t.lower() for t in FIELDCORE_TOPICS)
    out.update(t.lower() for t in SIMSELF_TOPICS)
    return tuple(sorted(out))


#: THE PRIORITY ORDER OF THE DEMANDS, and why it is an order.
#:
#: MEASURED 2026-10-31: the GitHub SEARCH API allows **30 requests
#: per minute** for an authenticated caller (`/rate_limit` reports
#: `search: limit=30, remaining=30`). The first version of this scanner
#: queried all 100 topics in one pass, so **8 of the 100 queries came
#: back HTTP 403** -- the rate limit, not a bad topic. The scan then
#: reported the errors and carried on, which is the right behaviour,
#: but the scan was also missing most of its topics' repos.
#:
#: So the query set must FIT the ceiling, and the demands are ordered
#: by how much we need them:
#:
#:   1. THE EXAM'S TODO AREAS. These are what the substrate cannot do.
#:      Nothing else on this list is a blocker to a passing grade.
#:   2. THE SHEAVES. These run, so they need maintenance, not rescue.
#:   3. THE HORIZON LETTERS. These are the future, and the future can
#:      wait for the next scan.
#:
#: The budget is spent in that order, and the report says how many
#: topics were actually queried -- because a scan that silently
#: queried half its list and reported the half's numbers as if they
#: were the whole is the failure this project keeps fighting.
DEMAND_PRIORITY: Tuple[str, ...] = (
    "area_07_reconciliation", "area_11_interface", "area_12_resource",
    "area_13_adversarial", "area_19_tools", "area_20_skills",
    "area_21_initiative", "area_22_planning",
    "sheaf_topology", "sheaf_mltr", "sheaf_mte", "sheaf_coding",
    "beta_parameter_self_optimisation", "delta_parameter_self_modification",
)

#: THE SEARCH API'S CEILING, measured from `/rate_limit` on
#: 2026-10-31: 30 requests per minute for an authenticated caller.
#:
#: AND THE SECOND MEASUREMENT, which is the one that shapes the
#: design: **91 topics** if every demand is queried. So the topics do
#: NOT fit in one window -- they fit in about FOUR.
#:
#: THAT MEANS THE SCANNER MUST PACE ACROSS WINDOWS, not burst. The
#: first version burst all 24 into one minute and 8 came back HTTP
#: 403 -- the rate limit, not a bad topic. The second version slept
#: 21 seconds on a 403 and retried, which is right but wrong in
#: placement: the throttle belongs BEFORE the query, not after the
#: failure.
#:
#: So the scanner asks for the RATE LIMIT itself, spends the window in
#: priority order, waits out the reset, and spends the next one. And
#: it REPORTS how many windows it needed, because a scan that quietly
#: covered a third of its topics and reported the numbers as if they
#: were the whole is the failure this project keeps fighting.
SEARCH_RATE_LIMIT = 30

#: How many topics one window buys. Slightly under the ceiling,
#: because the reset is not instantaneous.
SEARCH_BUDGET = 24

#: How many windows the scanner may spend. 4 windows at 24 topics is
#: 96 -- the whole demand set. The cap is here so a misconfigured
#: topic list cannot run for an hour.
MAX_WINDOWS = 4

#: The topics the scanner QUERIES, in PRIORITY order, capped at the
#: measured ceiling.
QUERY_TOPICS: Tuple[str, ...] = tuple(
    t for d in DEMAND_PRIORITY for t in ALL_DEMANDS[d]["topics"]
)[:SEARCH_BUDGET * MAX_WINDOWS]


def demands_for(topics: Sequence[str]) -> List[str]:
    """which LIVE demands does a repo with these topics serve?"""
    low = set(t.lower() for t in topics)
    out = []
    for name, d in LIVE_DEMANDS.items():
        if low & set(t.lower() for t in d["topics"]):
            out.append(name)
    return out


# ===========================================================================
# THE CREDENTIAL
# ===========================================================================

def read_token(path: str = TOKEN_FILE) -> Optional[str]:
    """the GitHub token, read from the vault.

    AND IT IS NEVER PRINTED. The vault file's own rule: DO NOT paste in
    chat. So this returns it and nothing logs it.

    The regex is deliberately narrow -- a `ghp_` prefix and alphanumerics
    only -- so a stray word in the prose cannot be mistaken for a
    credential.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    m = re.search(r"ghp_[A-Za-z0-9]{20,}", text)
    return m.group(0) if m else None


# ===========================================================================
# THE SCAN
# ===========================================================================

@dataclass
class Hit:
    """one repo, and the demands it could serve."""
    full_name: str
    stars: int
    language: str
    description: str
    topics: Tuple[str, ...]
    demands: Tuple[str, ...]
    matched: str

    def describe(self) -> Dict[str, Any]:
        return {
            "full_name": self.full_name, "stars": self.stars,
            "language": self.language, "description": self.description,
            "topics": list(self.topics), "demands": list(self.demands),
            "matched": self.matched,
        }


@dataclass
class ScanOutcome:
    """what one live scan produced, and how it went."""
    manifest: Any
    hits: List[Hit] = field(default_factory=list)
    mode: str = "live"
    topics_queried: Tuple[str, ...] = ()
    api_calls: int = 0
    errors: List[str] = field(default_factory=list)
    token_found: bool = False
    #: How many rate-limit WINDOWS the scan had to wait out. Reported,
    #: because a scan that covered 24 of 91 topics and reported the
    #: numbers as if they were the whole is the failure this project
    #: keeps fighting.
    windows: int = 0

    def describe(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "topics_queried": len(self.topics_queried),
            "api_calls": self.api_calls,
            "windows": self.windows,
            "repos_found": len(self.manifest.repos),
            "demands_served": len({d for h in self.hits for d in h.demands}),
            "errors": list(self.errors),
            "token_found": self.token_found,
        }

    def by_demand(self) -> Dict[str, List[Hit]]:
        out: Dict[str, List[Hit]] = {}
        for h in self.hits:
            for d in h.demands:
                out.setdefault(d, []).append(h)
        for k in out:
            out[k].sort(key=lambda x: -x.stars)
        return out


def _search(topic: str, token: str, per_page: int = PER_PAGE
            ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """one topic query. Returns (items, error).

    AND THE ERROR IS RETURNED, not raised. A scan that dies on one bad
    topic loses every other topic's results too, and the failure is
    invisible in the manifest -- which is how a broken scanner looks
    like a scanner that found nothing.

    AND THE 403 IS THE RATE LIMIT, not a bad topic. MEASURED
    2026-10-31: GitHub's search API allows 30 requests per minute for
    an authenticated caller, and a query past that returns 403 with a
    rate-limit body. So the 403 is a THROTTLE signal, and the scanner
    treats it as one: it waits for the window and retries, rather than
    recording the topic as failed.
    """
    url = ("%s?q=topic:%s&sort=stars&order=desc&per_page=%d"
           % (API_SEARCH, topic, per_page))
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer %s" % token,
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429) and attempt < 2:
                # THE RATE LIMIT. Wait out the window and retry -- the
                # topic is fine, the timing was wrong.
                time.sleep(21.0)
                continue
            return [], "HTTP %s for topic %r" % (exc.code, topic)
        except urllib.error.URLError as exc:
            return [], "URLError for topic %r: %s" % (topic, exc.reason)
        except Exception as exc:  # noqa: BLE001
            return [], "%s for topic %r" % (type(exc).__name__, topic)
        items = data.get("items") or []
        return items, None
    return [], "rate limited on topic %r after 3 attempts" % (topic,)


def rate_limit(token: str) -> Dict[str, int]:
    """the search API's CURRENT window, read from GitHub itself.

    AND IT IS READ, NOT ASSUMED. The ceiling was measured at 30/min on
    2026-10-31, but a hardcoded ceiling is a guess about a remote
    system that can change. So the scanner asks, and it uses the
    ANSWER -- both the remaining count and the reset time.
    """
    req = urllib.request.Request("https://api.github.com/rate_limit",
                                 headers={
                                     "Authorization": "Bearer %s" % token,
                                     "Accept": "application/vnd.github+json",
                                     "User-Agent": UA,
                                 })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:  # noqa: BLE001
        return {"remaining": SEARCH_RATE_LIMIT, "limit": SEARCH_RATE_LIMIT,
                "reset": int(time.time()) + 60}
    res = (data.get("resources") or {}).get("search") or {}
    return {
        "remaining": int(res.get("remaining", SEARCH_RATE_LIMIT)),
        "limit": int(res.get("limit", SEARCH_RATE_LIMIT)),
        "reset": int(res.get("reset", int(time.time()) + 60)),
    }


def scan_live(token: Optional[str] = None,
              topics: Sequence[str] = QUERY_TOPICS,
              per_page: int = PER_PAGE,
              star_floor: int = 0,
              pace: bool = True) -> ScanOutcome:
    """the live scan: GitHub search over the demand topics.

    AND THE PACING. The search API allows 30 requests a minute and the
    demand set is 91 topics, so the scan spends SEVERAL WINDOWS. Before
    each window it reads the live rate limit, and when the window is
    spent it WAITS FOR THE RESET rather than hammering into a 403.

    THE FALLBACK IS EXPLICIT. Without a token this returns the
    canonical list and says `mode="fallback"`. It does NOT return an
    empty scan, because an empty scan and a working scan look the same
    from the outside, and only one of them is true.
    """
    if token is None:
        token = read_token()
    if not token:
        return ScanOutcome(
            manifest=scan_from_cache(CANONICAL_REPOS),
            mode="fallback",
            topics_queried=tuple(topics),
            errors=["no token: fell back to the canonical list. the scan "
                    "did NOT run against github."],
            token_found=False,
        )

    raw: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    calls = 0
    windows = 0
    topics_done = 0
    #: THE TOPICS THAT ACTUALLY ANSWERED, and this list exists because
    #: the count was LYING.
    #:
    #: MEASURED 2026-11-05, from the day's own run records: the run at
    #: 18:09:58 reported `topics_queried 96` of 96 -- and its errors
    #: carried `RemoteDisconnected for topic 'sheaf'`. So a topic that
    #: FAILED was counted as QUERIED, because `topics_done += 1` ran
    #: BEFORE the error was checked:
    #:
    #:     items, err = _search(topic, token, per_page)
    #:     calls += 1
    #:     topics_done += 1     <- counted before the error check
    #:     if err:
    #:         errors.append(err)
    #:         continue
    #:
    #: And the score said the day queried every topic it asked for, and
    #: the loop's judge said DONE. **The coverage was short and the
    #: score said it was complete.** That is the same defect class as
    #: the whole of 2026-11-05: a missing thing read as a present one.
    #:
    #: SO THE TOPICS ARE COLLECTED, NOT COUNTED. `topics_queried` is
    #: then the topics that ANSWERED -- and it is a list of the actual
    #: topics, so the slice is right too: counting only the successes
    #: while slicing the first N would report the wrong topics.
    topics_ok: List[str] = []

    for topic in topics:
        # THE PACING, BEFORE the query. If the window is spent, wait
        # for the reset and read the limit again -- the ceiling is
        # asked for, not assumed.
        if pace:
            rl = rate_limit(token)
            if rl["remaining"] <= 1 and windows < MAX_WINDOWS:
                wait = max(1, rl["reset"] - int(time.time()) + 2)
                print("    [pace] window spent (%d/%d left); waiting %ds "
                      "for the reset" % (rl["remaining"], rl["limit"], wait),
                      flush=True)
                time.sleep(min(wait, 90))
                windows += 1

        items, err = _search(topic, token, per_page)
        calls += 1
        if err:
            errors.append(err)
            # AND THE FAILED TOPIC IS NOT COUNTED AS QUERIED. MEASURED:
            # the count used to be incremented before this branch, so a
            # topic that raised RemoteDisconnected was reported as
            # queried and the day's coverage was over-stated.
            continue
        topics_done += 1
        topics_ok.append(topic)
        for it in items:
            name = it.get("full_name")
            if not name:
                continue
            prev = raw.get(name)
            if prev is None:
                raw[name] = it
                # AND THE TOPIC THAT FOUND IT IS RECORDED, and it was
                # NOT recorded at all before this. MEASURED 2026-11-07:
                # the scanner's own loop knows which topic produced each
                # hit -- the topic is the loop variable -- and the hit
                # was stored without it. So the day's records said
                # "96 topics queried, 199 repos found" and NOTHING said
                # which topic found which repo.
                #
                # AND THAT IS THE MISSING LINK FOR THE HIERARCHY'S SECOND
                # HALF. The slow level cannot decide which topics are
                # worth querying if it cannot see which topics produced
                # the repos that CHANGED. **A LEVEL THAT CANNOT SEE THE
                # CAUSE CANNOT DROP THE CAUSE.**
                #
                # AND A REPO FOUND BY SEVERAL TOPICS CARRIES ALL OF THEM,
                # because a repo that two topics both find is a repo both
                # topics would have to keep.
                _found = list(it.get("found_by") or [])
                if topic not in _found:
                    _found.append(topic)
                it["found_by"] = _found
            else:
                extra = list(prev.get("topics") or [])
                for t in (it.get("topics") or []):
                    if t not in extra:
                        extra.append(t)
                prev["topics"] = extra
                _found = list(prev.get("found_by") or [])
                if topic not in _found:
                    _found.append(topic)
                prev["found_by"] = _found

    if not raw and errors:
        return ScanOutcome(
            manifest=scan_from_cache(CANONICAL_REPOS),
            mode="fallback",
            # AND THE TOPICS THAT ANSWERED, not a slice of the first N.
            # MEASURED: `topics[:topics_done]` named the first N topics,
            # which -- once the count counted only the SUCCESSES -- would
            # be the wrong topics entirely. The list is the truth.
            topics_queried=tuple(topics_ok),
            api_calls=calls,
            errors=errors + ["every topic query failed: fell back to the "
                             "canonical list"],
            token_found=True,
        )

    # THE MANIFEST DROPS WHAT THE DEMANDS FOUND, and it was MEASURED.
    #
    # MEASURED 2026-10-31: `scan_from_cache` keeps a repo only if it
    # carries one of the scanner's ORIGINAL 12 topics (manifold, hodge,
    # gradient-flow, gate, psb, agent-runtime, constitutional-ai, ...).
    # So a repo found by a DEMAND topic -- robotics, planning, sandbox,
    # fuzzing, meta-learning -- is DROPPED from the manifest, even
    # though the hits list below shows it.
    #
    # The symptom was two scans of nearly the same topics reporting
    # 197 repos and 72, with the same number of successful queries.
    # The 197-run queried the old 12 topics; the 72-run queried the
    # demand topics. **And the manifest under-reported BOTH**: it only
    # counted the repos the old 12 topics matched, and it did so while
    # the demands found more.
    #
    # SO THE MANIFEST IS BUILT FROM THE DEMANDS, not from the old
    # topic filter. The old filter is still applied -- a repo carrying
    # none of our topics is still not ours -- but the DEMAND set is
    # now a superset of it, so nothing is lost.
    _old_topics = set(t.lower() for t in FIELDCORE_TOPICS) | \
        set(t.lower() for t in SIMSELF_TOPICS)
    _demand_topics = set()
    for _d in LIVE_DEMANDS.values():
        _demand_topics.update(t.lower() for t in _d["topics"])
    _keep_topics = _old_topics | _demand_topics

    kept: List[Dict[str, Any]] = []
    for r in raw.values():
        low = set(t.lower() for t in (r.get("topics") or ()))
        if low & _keep_topics:
            kept.append(r)

    manifest = scan_from_cache(kept)
    hits: List[Hit] = []
    for r in manifest.repos:
        if star_floor and r.stars < star_floor:
            continue
        hits.append(Hit(
            full_name=r.full_name, stars=r.stars, language=r.language,
            description=r.description, topics=r.topics,
            demands=tuple(demands_for(r.topics)), matched=r.matched,
        ))
    hits.sort(key=lambda h: -h.stars)
    return ScanOutcome(
        manifest=manifest,
        hits=hits,
        mode="live",
        # THE TOPICS THAT ANSWERED. MEASURED: this was
        # `topics[:topics_done]`, which named the first N topics
        # rather than the ones that worked -- so a day where one topic
        # raised RemoteDisconnected reported 96 of 96 topics queried
        # and the loop's judge said DONE.
        topics_queried=tuple(topics_ok),
        api_calls=calls,
        errors=errors,
        token_found=True,
        windows=windows,
    )


# ===========================================================================
# THE DIFF -- what makes a DAILY scan worth anything
# ===========================================================================

@dataclass
class ManifestDiff:
    """what changed between two scans."""
    new_repos: List[str] = field(default_factory=list)
    grown: List[Tuple[str, int, int]] = field(default_factory=list)
    shrunk: List[Tuple[str, int, int]] = field(default_factory=list)
    changed_topics: List[str] = field(default_factory=list)
    unchanged: int = 0
    #: THE REPOS THAT DISAPPEARED, and the field is NEW.
    #:
    #: MEASURED 2026-11-07: the diff iterates over the NEW manifest's
    #: repos, so it counts what is PRESENT -- new, grown, shrunk,
    #: unchanged -- and a repo that is GONE is not counted at all.
    #: **AND THE LOSS IS SILENT, WHICH IS THE WORST KIND.**
    #:
    #: The symptom, measured live on 2026-11-07: the scan queried the
    #: reduced topic set, the topic `manifold` failed with a
    #: `URLError`, and the manifest came back with 169 repos against
    #: the baseline's 199. The 30 repos that `manifold` was the only
    #: topic to find had VANISHED -- and the day's score said
    #: `accounted 169 of 169 BALANCED`, because the arithmetic only
    #: counts the repos that are present.
    #:
    #: **A DAY THAT LOSES 30 REPOS AND REPORTS ITS ARITHMETIC AS
    #: BALANCED IS A DAY THAT LOOKS PERFECT AND IS NOT.** And the
    #: loop's own judge has an obligation -- "every repo found is
    #: accounted for" -- that the loss walks straight past, because
    #: the repos that vanished are not among the repos found.
    #:
    #: So the disappearance is its own count, and it is its own
    #: obligation. A repo that leaves the manifest is a FINDING, and
    #: it is the finding that says the scan was short.
    disappeared: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        return {
            "new_repos": list(self.new_repos),
            "grown": ["%s: %d -> %d" % g for g in self.grown],
            "shrunk": ["%s: %d -> %d" % s for s in self.shrunk],
            "changed_topics": list(self.changed_topics),
            "unchanged": self.unchanged,
            "disappeared": list(self.disappeared),
        }

    @property
    def empty(self) -> bool:
        return not (self.new_repos or self.grown or self.shrunk
                    or self.changed_topics)


def diff_manifests(old: Any, new: Any) -> ManifestDiff:
    """what changed between yesterday's manifest and today's.

    THE STAR COUNTS ARE THE SIGNAL, and the growth is what says a repo
    is becoming load-bearing. The topic change is the other signal: a
    repo that gained a topic we scan for has become relevant even if
    its stars did not move.

    **AND THE REPOS THAT DISAPPEARED ARE COUNTED, because the
    arithmetic alone cannot see them.** MEASURED 2026-11-07: the
    count is over the repos that are PRESENT, so a repo that left the
    manifest -- because the only topic that could find it FAILED --
    was counted nowhere. The day's score said `169 of 169 BALANCED`
    with 30 repos gone. So the disappearance is its own count, and it
    is the count that says the scan was short.
    """
    old_by = {r.full_name: r for r in (old.repos if old else [])}
    new_by = {r.full_name: r for r in (new.repos if new else [])}
    out = ManifestDiff()

    for name, repo in new_by.items():
        prev = old_by.get(name)
        if prev is None:
            out.new_repos.append(name)
            continue
        if repo.stars > prev.stars:
            out.grown.append((name, prev.stars, repo.stars))
        elif repo.stars < prev.stars:
            out.shrunk.append((name, prev.stars, repo.stars))
        else:
            out.unchanged += 1
        if set(repo.topics) != set(prev.topics):
            out.changed_topics.append(name)

    #: AND THE ONES THAT WENT. A repo in the old manifest and not in
    #: the new one. **IT IS NOT A SHRUNK REPO** -- a shrunk repo is
    #: still there with fewer stars -- and it is not a "new" repo
    #: either. It is GONE, and the reason is almost always a topic
    #: that failed to answer, which is the finding the day needs.
    out.disappeared = sorted(set(old_by) - set(new_by))
    return out


def latest_manifest(dirname: str = "~/.simself/scans") -> Optional[Any]:
    """yesterday's manifest, so the diff has something to compare to."""
    import glob
    base = os.path.expanduser(dirname)
    files = sorted(glob.glob(os.path.join(base, "scan-*.json")))
    if not files:
        return None
    try:
        with open(files[-1], encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:  # noqa: BLE001
        return None
    repos = tuple(
        ScannedRepo(
            full_name=r.get("full_name", "?"),
            stars=int(r.get("stars", 0)),
            language=r.get("language", ""),
            description=r.get("description", ""),
            topics=tuple(r.get("topics") or ()),
            scan_ts=data.get("scan_ts", ""),
            matched=r.get("matched", ""),
            # AND THE TOPICS THAT FOUND IT, restored from the manifest.
            found_by=tuple(r.get("found_by") or ()),
        )
        for r in (data.get("repos") or []))
    return ScanManifest(scanner_version=data.get("scanner_version", "1.0"),
                        scan_ts=data.get("scan_ts", ""), repos=repos)


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description="the live repo scan -- aimed at what simself could become")
    ap.add_argument("--scan-only", action="store_true",
                    help="print the manifest and stop: do not write it")
    ap.add_argument("--dest", default="~/.simself/scans",
                    help="where the manifest goes")
    ap.add_argument("--floor", type=int, default=0,
                    help="the star floor; 0 shows everything the scan saw")
    args = ap.parse_args()

    print("=" * 78)
    print("THE LIVE REPO SCAN -- AIMED AT WHAT SIMSELF COULD BECOME")
    print("=" * 78)
    print()

    outcome = scan_live(star_floor=args.floor)
    d = outcome.describe()
    print("  mode                %s" % d["mode"])
    print("  topics queried      %d of %d requested" % (
        d["topics_queried"], len(QUERY_TOPICS)))
    print("  api calls           %d" % d["api_calls"])
    print("  windows waited      %d" % d["windows"])
    print("  token found         %s" % ("yes" if d["token_found"] else "NO"))
    print("  repos matched       %d" % d["repos_found"])
    print("  demands served      %d of %d LIVE"
          % (d["demands_served"], len(LIVE_DEMANDS)))
    print("  parked demands      %d %s"
          % (len(PARKED_DEMANDS),
             [n for n in PARKED_DEMANDS]))
    print()
    print("  THE SEARCH API'S CEILING IS 30 REQUESTS A MINUTE, so the")
    print("  budget is %d topics in PRIORITY order: the exam's TODO"
          % SEARCH_BUDGET)
    print("  areas first, the sheaves second, the horizon letters last.")
    print("  Demands whose topics fall outside the budget are NOT")
    print("  reported as empty -- they are reported as UNSEARCHED below.")
    print()
    if d["errors"]:
        print("  ERRORS, and they are part of the result:")
        for e in d["errors"][:8]:
            print("    %s" % e)
        print()
    if outcome.mode == "fallback":
        print("  THIS WAS NOT A LIVE SCAN. The numbers below are the")
        print("  hardcoded canonical list, unchanged since 2026-10-06.")
        print("  A fallback that looked like a live scan would be the")
        print("  worst kind of wrong.")
        print()

    # -- the demands, and what each found ---------------------------
    by_demand = outcome.by_demand()
    print("=" * 78)
    print("THE DEMANDS, AND WHAT THE SCAN FOUND FOR EACH")
    print("=" * 78)
    print()
    # THE GROUPS ARE BY DEMAND NAME, not by a prefix guess. The first
    # version matched on the name's first word ("alpha", "area",
    # "sheaf") and the HORIZON group printed EMPTY -- because beta and
    # delta are named after the LETTER, not after the word "alpha".
    # A report that silently shows a group as empty when it simply
    # failed to match is worse than no report.
    groups = (
        ("HORIZON", "the letters that do not exist yet",
         tuple(HORIZON_DEMANDS)),
        ("FLOOR", "the exam areas that are TODO",
         tuple(FLOOR_DEMANDS)),
        ("CORE", "the sheaves that run",
         tuple(CORE_DEMANDS)),
    )
    for label, note, names in groups:
        print("  %s -- %s" % (label, note))
        for name in names:
            dem = ALL_DEMANDS[name]
            found = by_demand.get(name, [])
            # A DEMAND WHOSE TOPICS FELL OUTSIDE THE BUDGET IS NOT A
            # DEMAND THAT FOUND NOTHING. The first version reported both
            # as "0", which is a lie: "we looked and there was nothing"
            # and "we did not look" are different findings, and only one
            # of them is about the world.
            searched = any(t.lower() in set(QUERY_TOPICS)
                           for t in dem["topics"])
            if not searched:
                print("    %-34s  --  UNSEARCHED (its topics are "
                      "outside the budget this run)" % (name,))
                continue
            top = ", ".join("%s(%d)" % (h.full_name, h.stars)
                            for h in found[:3])
            print("    %-34s %2d  %s" % (name, len(found), top))
        print()
    print("  PARKED -- not queried, not searched:")
    for name, dem in PARKED_DEMANDS.items():
        print("    %-34s %s" % (name, dem.get("parked_reason", "")))
    print()

    # -- the top hits ------------------------------------------------
    print("=" * 78)
    print("THE TOP HITS, WITH THE DEMAND EACH ONE SERVES")
    print("=" * 78)
    print()
    print("  %-40s %-7s %-11s %s" % ("repo", "stars", "language", "demand"))
    print("  " + "-" * 78)
    for h in outcome.hits[:25]:
        print("  %-40s %-7d %-11s %s"
              % (h.full_name[:40], h.stars, (h.language or "?")[:11],
                 ",".join(h.demands[:2]) or "-"))
    if len(outcome.hits) > 25:
        print("  ... and %d more" % (len(outcome.hits) - 25))
    print()

    # -- the diff -----------------------------------------------------
    old = latest_manifest(args.dest)
    if old is None:
        print("  no previous manifest, so this is the first live scan and")
        print("  there is nothing to diff against.")
    else:
        diff = diff_manifests(old, outcome.manifest)
        dd = diff.describe()
        print("  THE DIFF against the previous manifest:")
        print("    new repos        %d %s" % (len(dd["new_repos"]),
                                              dd["new_repos"][:5]))
        print("    grown            %d %s" % (len(dd["grown"]),
                                              dd["grown"][:5]))
        print("    shrunk           %d %s" % (len(dd["shrunk"]),
                                              dd["shrunk"][:5]))
        print("    topics changed   %d %s" % (len(dd["changed_topics"]),
                                              dd["changed_topics"][:5]))
        print("    unchanged        %d" % dd["unchanged"])
        print()
        if diff.empty:
            print("    NOTHING CHANGED. That is a finding, not a nothing:")
            print("    a scanner that reports the same thing every day")
            print("    is not scanning.")
            print()
    print("=" * 78)
    if not args.scan_only:
        path = write_manifest(outcome.manifest, args.dest)
        print("wrote: %s" % path)
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
