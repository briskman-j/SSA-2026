#!/usr/bin/env python3
"""Static site generator for The Alliance Dispatch (Super Smash Alliance 10.0).

Builds:
  - index.html (Newsstand & Featured Latest Issue)
  - recaps/midseason/index.html (Midseason State of the Alliance Roast)
  - recaps/week-1/index.html .. recaps/week-7/index.html (Per-week archive with custom OpenGraph cards)
  - super-smash-alliance-site.zip (Ready for 5-second Netlify Drop / Cloudflare Pages / GitHub Pages)
"""

import argparse
from collections import defaultdict
import html
from html.parser import HTMLParser
import json
import os
import shutil
import urllib.request
import zipfile

LEAGUE_ID = 1000567
SEASON_ID = 2026
PUBLIC_SITE_URL = "https://briskman-j.github.io/SSA-2026/"
ESPN_URL = (
    f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}"
    f"/segments/0/leagues/{LEAGUE_ID}?view=mTeam&view=mRoster&view=mMatchupScore"
    f"&view=mStandings&view=mSettings"
)

ARTIFACT_DIR = "/usr/local/google/home/briskman/.gemini/jetski/brain/99ae4121-ebdb-4c04-898d-23a8e531f491"
SCRATCH_DIR = os.path.join(ARTIFACT_DIR, "scratch")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_OUT_DIR = (
    os.path.join(SCRATCH_DIR, "SSA-2026")
    if os.path.normpath(SCRIPT_DIR) == os.path.normpath(SCRATCH_DIR)
    else SCRIPT_DIR
)

MANAGER_SHORT = {
    1: "Kyle Feeney",
    2: "Josh Briskman",
    3: "Kyle O'Keefe",
    4: "D B (feeneysucksthebigone)",
    5: "Chase Bailey",
    12: "Ronjohn Dadd",
    13: "Billy Mattimore",
    15: "Wills Miller",
    17: "Ryan Gutowski",
    18: "Owen Bennett",
    19: "Jackson Place",
    20: "Michael Huffner",
}

TEAM_ROASTS = {
    12: {
        "epithet": "The Horseshoe Throne",
        "crime": "Draft Proj #12 -> #1 Seed • 6-game win streak after an 88.22-pt Week 1",
        "roast": (
            "ESPN projected Ronjohn 12th out of 12 on Draft Night, and in Week 1 he validated every hater "
            "by putting up an 88.22-point wet fart and losing by 63. Naturally, he has won SIX STRAIGHT GAMES "
            "since. He sits 4th in scoring (933.48 PF) riding +1.73 wins of pure schedule sorcery—winning Week 2 "
            "with 109.16 points and escaping Week 7 by 3.34 points (139.70–136.36). This man currently has "
            "Roschon Johnson (28.10 pts) slotted at RB2 while James Cook III (116.60 pts) sits on his bench, "
            "and you idiots still let him go 6-1 with 91.8% playoff odds."
        ),
    },
    1: {
        "epithet": "The AFK Schedule Merchant",
        "crime": "ONE (1) waiver move all season • 9th in PF (856.42) • #1 Luck (+1.91)",
        "roast": (
            "Kyle Feeney is 5-2 in 2nd place despite ranking 9th in Points For (856.42), owning a losing "
            "All-Play record (34-43, .442), and leading the entire league in Luck (+1.91 extra wins). Better yet: "
            "Kyle has made ONE (1) waiver move the entire season. Did you delete the ESPN app after Labor Day, Kyle? "
            "Reality finally tapped him on the shoulder in Week 7 when he put up a rancid 73.66 points and got "
            "boat-raced by 74.26 points to hand the 0-6 Ottawa Redblacks their first win of the year."
        ),
    },
    15: {
        "epithet": "The Ferrari Stuck in School-Zone Traffic",
        "crime": "1,099.82 PF (#1 by 131.6 pts) • 61-16 (.792) All-Play • Still tied at 4-3",
        "roast": (
            "Wills has scored 1,099.82 points (157.12 PPG)—outscoring 2nd place by 131.58 points, leading the entire "
            "league in weekly scoring in 4 of 7 weeks (including that 207.86-point Week 2 war crime), and posting a "
            "61-16 (.792) All-Play record. His reward? Tied at 4-3 with five other dudes, sitting a full game behind "
            "1-waiver-move Feeney after losing twice while scoring 145.60 and 137.98. Maybe if you weren't rostering "
            "two kickers while your Eagles D/ST sits at 6.00 season points, the fantasy gods would respect you."
        ),
    },
    4: {
        "epithet": "Rent-Free in 4th Place",
        "crime": "Named account 'feeneysucksthebigone' • Outscoring Feeney by 111.8 pts • Still behind him",
        "roast": (
            "Imagine dedicating your entire ESPN username (feeneysucksthebigone) to hating Kyle Feeney, scoring "
            "111.82 more points than him (#2 in PF at 968.24), grinding 15 waiver moves, and STILL looking up at "
            "Feeney in the standings after losing Week 7 by 3.34 points (136.36 to Dadd's 139.70). Also, drafting "
            "Ja'Marr Chase #9 overall only to banish him to the FLEX spot behind Christian Watson while Kirk Cousins "
            "anchors your Superflex is nasty work."
        ),
    },
    17: {
        "epithet": "Two Ferraris Pulling a Shopping Cart",
        "crime": "Exact 4.00 Expected Wins (+0.00 Luck) • Bijan & CMC carrying Shough + Bryce Young",
        "roast": (
            "The most mathematically ethical team in the alliance: 4.00 expected All-Play wins, 4 actual wins "
            "(+0.00 Luck). Ryan turned the 12/13 draft turn into Bijan Robinson (147.70) and Christian McCaffrey "
            "(144.00), which is fortunate because his Superflex QB room is currently Tyler Shough and Bryce Young "
            "standing on each other's shoulders in a trench coat. Just survived Week 7's ugliest rock fight "
            "(105.24 over Huffner's 87.40)."
        ),
    },
    20: {
        "epithet": "First-Team All-Defense",
        "crime": "759.04 PA (108.4 PPG against — easiest schedule) • Starting TWO Tight Ends in Superflex",
        "roast": (
            "Draft Day's #1 projected juggernaut leads the entire league in Point Differential (+159.28) exclusively "
            "because nobody is allowed to score against him: opponents average a polite 108.43 PPG (255.76 fewer "
            "points faced than Bad Mother Tucker's!). Michael has made 2 waiver moves all year, won Week 6 scoring "
            "100.48, faceplanted for 87.40 in Week 7, is unironically starting TWO Tight Ends (George Kittle + "
            "Isaiah Likely in the Superflex OP slot), and clings to the #6 final playoff chair by 2.30 points."
        ),
    },
    5: {
        "epithet": "Cardio King on the Wrong Side of 2.30 Points",
        "crime": "27 waiver moves (more than 7 managers COMBINED) • Missing playoffs by 2.30 total pts",
        "roast": (
            "Chase has made 27 waiver acquisitions in seven weeks—nearly four moves a week, and more than Feeney (1), "
            "Huffner (2), O'Keefe (2), Jackson (3), Owen (4), Ronjohn (5), and Billy (5) COMBINED (22). All that "
            "frantic button-mashing has earned him 7th place on the outside of the playoffs by 2.30 points with a "
            "-65.70 differential (981.72 PA). Jahmyr Gibbs (174.00 pts) needs lower-back surgery from carrying "
            "J.J. McCarthy (26.70 pts in OP) and Jordan Mason (18.70 pts), and Chase barely escaped 1-6 Bad Mother "
            "Tucker's by 7.16 points last week."
        ),
    },
    3: {
        "epithet": "Duct Tape, Prayer, and 2.38 Points",
        "crime": "-14.24 Diff • 36-41 All-Play • 2 moves • Pierre Strong Jr. starting at FLEX",
        "roast": (
            "Negative point differential (-14.24), sub-.500 All-Play record (36-41), 2 total waiver moves, #4 overall "
            "pick Jayden Daniels riding the bench behind Jacoby Brissett, #21 overall pick Jaxson Dart evaporated onto "
            "IR, Davante Adams parked in the OP slot with an IR tag, and Pierre Strong Jr. (16.50 pts) starting at "
            "FLEX... yet somehow STILL 4-3 thanks to a 2.38-point Week 7 squeaker (123.78–121.40) over Jackson."
        ),
    },
    19: {
        "epithet": "The Mirage Just Ran Out of Water",
        "crime": "Started 3-1 -> Lost 3 straight • Season-low 67.72 pts in Wk 6 • Still 1 game out of 3rd",
        "roast": (
            "Jackson started 3-1 via pure smoke, mirrors, and the 2nd-softest schedule in the league (803.44 PA). "
            "Since then? Three straight losses, anchored by the lowest single-week score in the entire league all "
            "season (67.72 points in Week 6) and a 2.38-point gut punch in Week 7. He ranks 11th in scoring (811.44 PF, "
            "28-49 All-Play) and is starting Tyler Huntley at QB1 while #2 pick Lamar Jackson sits on IR—and the "
            "sickest joke of this league's parity is that he's STILL one game out of a 6-way tie for 3rd place."
        ),
    },
    13: {
        "epithet": "All Dressed Up With Nowhere to Go",
        "crime": "Outscoring 3 teams ahead of him (911.58 PF) • Wasted 183.00 pts beating Josh by 90",
        "roast": (
            "Billy has actually outscored three teams ahead of him (911.58 PF—more than O'Keefe, Feeney, and Jackson, "
            "and less than 7 points behind #6 Huffner) and is still rotting in 10th place at 2-5. That's what happens "
            "when Round 3 pick Saquon Barkley has 38.10 total points and you blow 183.00 points in Week 5 beating "
            "93.46-point Bad Mother Tucker's by 90 instead of rationing touchdowns for weeks when your opponent has a pulse."
        ),
    },
    18: {
        "epithet": "Escaped the Basement on Technicality",
        "crime": "Only human on Earth to lose to Bad Mother Tucker's • Worst Luck (-1.64) • Started 0-6",
        "roast": (
            "Let's never forget Owen's crowning achievement of 2026: being the ONLY human being on Planet Earth who "
            "managed to lose a fantasy football game to Bad Mother Tucker's (Week 1). Owen owns the worst Luck Index "
            "in the league (-1.64, including a brutal 147.56–149.98 loss in Week 4), watched Round 2–3 picks De'Von "
            "Achane (24.60 pts, IR) and A.J. Brown (19.10 pts) turn to dust, and started 0-6 before dropping 147.92 "
            "on Feeney in Week 7—solely to abandon me alone in the cellar."
        ),
    },
    2: {
        "epithet": "Clinically Deceased Since Week 2 (Comms Desk)",
        "crime": "753.16 PF (#12) • 1,014.80 PA (#12) • -261.64 Diff • Tanner McKee QB1 • 6-Game Skid",
        "roast": (
            "Peaked in Week 1 (153.64 pts, 1-0, mentally measuring ring sizes) and immediately lost SIX STRAIGHT, "
            "finishing as the weekly low scorer 3 times in 4 weeks while opponents hung an absurd 144.97 PPG (1,014.80 PA) "
            "on our heads—highlighted by Wills' 207.86-point Week 2 execution. We can't even blame schedule luck because "
            "we ALSO rank dead last in scoring (753.16 PF, nearly 80 pts behind 11th). #7 pick Jalen Hurts evaporated to "
            "IR, #18 pick Justin Jefferson (72.10) is 6th on our own roster behind Rhamondre and Devaughn Vele, #31 pick "
            "Kyler Murray (53.68) is losing to kicker Brandon Aubrey (58.00) and Steelers D/ST (57.00), and Tanner McKee "
            "(23.14 pts) is our Superflex QB1. Still 2.6% playoff odds—so you're telling me there's a chance."
        ),
    },
}

WEEKLY_EDITORIALS = {
    1: {
        "kicker": "ISSUE NO. 01 • WEEK 1 RECAP",
        "headline": "Fool's Gold: Bad Mother Tucker's Opens 1-0 While Draft-Last Ronjohn Faceplants for 88.22",
        "subhead": (
            "Screenshot the Week 1 standings and hang them in the Louvre: Josh dropped 153.64 to crush Owen, "
            "Wills opened his scoring reign at 175.34, and Ronjohn looked every bit like ESPN's 12th-ranked draft."
        ),
        "teaser": "Alliance Dispatch Wk 1: Josh peaks at 1-0 (153.6), Wills drops 175.3, and Ronjohn opens dead last with 88.2.",
    },
    2: {
        "kicker": "ISSUE NO. 02 • WEEK 2 RECAP",
        "headline": "The 207.86-Point War Crime: Team Miller Vaporizes Bad Mother Tucker's by 106.98 Points",
        "subhead": (
            "Wills dropped the first 200-burger of the season (207.86) on Josh's league-low 100.88, while Ronjohn "
            "began his fraudulent winning streak by beating Jackson 109.16 to 103.66 in a pillow fight."
        ),
        "teaser": "Alliance Dispatch Wk 2: Wills hangs 207.86 to execute Josh by 106.98 pts; Dadd steals a 109-pt ugly win.",
    },
    3: {
        "kicker": "ISSUE NO. 03 • WEEK 3 RECAP",
        "headline": "Three-Peat Scoring King Wills Hits 168.5, Feeney Steals a 1.32-Point Heist Over Huffner",
        "subhead": (
            "Kyle Feeney moved to 3-0 without touching the waiver wire via a 131.36–130.04 miracle over Huffner, "
            "while Bad Mother Tucker's posted a majestic 87.14 to claim back-to-back weekly toilet bowls."
        ),
        "teaser": "Alliance Dispatch Wk 3: Feeney steals a 1.32-pt heist (3-0), Wills wins his 3rd straight scoring belt, Josh hits 87.1.",
    },
    4: {
        "kicker": "ISSUE NO. 04 • WEEK 4 RECAP",
        "headline": "Huffner Detonates a 188-Point Nuke While Owen Suffers a 2.42-Point Tragedy at 147.56",
        "subhead": (
            "Michael Huffner doubled up Chase 188.00 to 93.88, Kyle O'Keefe upset Wills (129.98–108.60), and "
            "0-4 Ottawa Redblacks scored 147.56 points—good enough to beat 9 other teams—only to lose to D B's 149.98."
        ),
        "teaser": "Alliance Dispatch Wk 4: Huffner drops 188.0, Owen loses with 147.56 by 2.42 pts, and undefeated Feeney & Wills fall.",
    },
    5: {
        "kicker": "ISSUE NO. 05 • WEEK 5 RECAP",
        "headline": "Creamers Drop 184.32 on Wills While Billy Wastes 183 Points Executing a Corpse",
        "subhead": (
            "Wills scored 145.60 and still lost by nearly 39 to The Absolute Creamers, while Billy Mattimore "
            "unloaded 183.00 points on 93.46-point Bad Mother Tucker's instead of saving touchdowns for October."
        ),
        "teaser": "Alliance Dispatch Wk 5: Creamers hang 184.3 on Wills' 145.6; Billy blows 183.0 beating Josh by 89.54.",
    },
    6: {
        "kicker": "ISSUE NO. 06 • WEEK 6 RECAP",
        "headline": "Jackson Sets the Season Low at 67.72 While Ronjohn Takes Over 1st Place With 168.20",
        "subhead": (
            "Team Place forgot football was played on Sunday (67.72 pts, letting Huffner win with 100.48), "
            "Tua Hands Dadd hung 168.20 on Wills for his 5th straight win, and Josh scored 81.20 in loss #5."
        ),
        "teaser": "Alliance Dispatch Wk 6: Jackson hits rock bottom (67.72 pts), Dadd drops 168.20 to seize #1, Wills falls to 3-3.",
    },
    7: {
        "kicker": "ISSUE NO. 07 • WEEK 7 RECAP",
        "headline": "0-6 Ottawa Humiliates 1-Move Feeney by 74.26 Points as Six Teams Pile Into a 4-3 Deadlock",
        "subhead": (
            "Owen finally escaped 0-6 by blowing out Kyle Feeney 147.92 to 73.66—leaving Bad Mother Tucker's "
            "all alone at 1-6 (#12)—while O'Keefe (+2.38) and Dadd (+3.34) survived nail-biters to forge a 6-way tie at 4-3."
        ),
        "teaser": "Alliance Dispatch Wk 7: 0-6 Owen blows out Feeney (147.9–73.7), leaving Josh alone in 12th as 6 teams tie at 4-3.",
    },
}


class TagValidator(HTMLParser):
    VOID_TAGS = {"meta", "link", "br", "hr", "img", "input"}

    def __init__(self):
        super().__init__()
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID_TAGS:
            return
        if not self.stack or self.stack[-1] != tag:
            raise ValueError(f"Mismatched closing tag </{tag}>; stack tail={self.stack[-3:]}")
        self.stack.pop()


def load_espn_data(out_dir, fetch_live=False):
    data_dir = os.path.join(out_dir, "data")
    repo_json_path = os.path.join(data_dir, "espn_full.json")
    scratch_json_path = os.path.join(SCRATCH_DIR, "espn_full.json")

    if fetch_live or (not os.path.exists(repo_json_path) and not os.path.exists(scratch_json_path)):
        req = urllib.request.Request(ESPN_URL, headers={"User-Agent": "AllianceDispatch/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
        os.makedirs(data_dir, exist_ok=True)
        with open(repo_json_path, "w") as f:
            f.write(raw)
    elif not os.path.exists(repo_json_path) and os.path.exists(scratch_json_path):
        os.makedirs(data_dir, exist_ok=True)
        shutil.copyfile(scratch_json_path, repo_json_path)

    with open(repo_json_path) as f:
        return json.load(f)


def compute_league_model(data):
    current_mp = data.get("status", {}).get("currentMatchupPeriod", 8)
    completed_weeks = current_mp - 1

    teams = {}
    for t in data.get("teams", []):
        tid = t["id"]
        rec = t.get("record", {}).get("overall", {})
        tx = t.get("transactionCounter", {})
        sim = t.get("currentSimulationResults", {})
        teams[tid] = {
            "id": tid,
            "name": (t.get("name") or "").strip(),
            "abbrev": (t.get("abbrev") or "").strip(),
            "manager": MANAGER_SHORT.get(tid, f"Team {tid}"),
            "wins": rec.get("wins", 0),
            "losses": rec.get("losses", 0),
            "pf": round(rec.get("pointsFor", 0.0), 2),
            "pa": round(rec.get("pointsAgainst", 0.0), 2),
            "diff": round(rec.get("pointsFor", 0.0) - rec.get("pointsAgainst", 0.0), 2),
            "streak": f"{'W' if rec.get('streakType') == 'WIN' else 'L'}{rec.get('streakLength', 0)}",
            "seed": t.get("playoffSeed", 99),
            "moves": tx.get("acquisitions", 0),
            "playoffPct": round(sim.get("playoffPct", 0.0) * 100, 1),
            "weekly": [],
            "epithet": TEAM_ROASTS.get(tid, {}).get("epithet", "League Contender"),
            "crime": TEAM_ROASTS.get(tid, {}).get("crime", ""),
            "roast": TEAM_ROASTS.get(tid, {}).get("roast", ""),
        }

    matchups_by_week = defaultdict(list)
    upcoming_matchups = []
    for m in data.get("schedule", []):
        mp = m.get("matchupPeriodId")
        if not mp or "away" not in m or "home" not in m:
            continue
        aid, hid = m["away"]["teamId"], m["home"]["teamId"]
        apts = round(m["away"].get("totalPoints", 0.0), 2)
        hpts = round(m["home"].get("totalPoints", 0.0), 2)
        if mp <= completed_weeks:
            matchups_by_week[mp].append((aid, apts, hid, hpts))
        elif mp == current_mp:
            upcoming_matchups.append((aid, hid))

    all_play = {tid: [0, 0] for tid in teams}
    cum_records = {tid: {"w": 0, "l": 0, "pf": 0.0, "pa": 0.0} for tid in teams}
    weeks_summary = {}

    for wk in range(1, completed_weeks + 1):
        wk_games = matchups_by_week[wk]
        scores = {}
        formatted_games = []
        for aid, apts, hid, hpts in wk_games:
            scores[aid] = apts
            scores[hid] = hpts
            if apts >= hpts:
                wid, wpts, lid, lpts = aid, apts, hid, hpts
            else:
                wid, wpts, lid, lpts = hid, hpts, aid, apts

            cum_records[wid]["w"] += 1
            cum_records[wid]["pf"] = round(cum_records[wid]["pf"] + wpts, 2)
            cum_records[wid]["pa"] = round(cum_records[wid]["pa"] + lpts, 2)

            cum_records[lid]["l"] += 1
            cum_records[lid]["pf"] = round(cum_records[lid]["pf"] + lpts, 2)
            cum_records[lid]["pa"] = round(cum_records[lid]["pa"] + wpts, 2)

            teams[wid]["weekly"].append([wk, wpts, lid, lpts, "W"])
            teams[lid]["weekly"].append([wk, lpts, wid, wpts, "L"])
            formatted_games.append([wid, wpts, lid, lpts, round(wpts - lpts, 2)])

        ranked_scores = sorted(scores.items(), key=lambda x: -x[1])
        median_pts = round((ranked_scores[5][1] + ranked_scores[6][1]) / 2.0, 2)
        for idx, (tid, _) in enumerate(ranked_scores):
            all_play[tid][0] += (11 - idx)
            all_play[tid][1] += idx

        formatted_games.sort(key=lambda g: -g[1])
        closest = min(formatted_games, key=lambda g: g[4])
        lucky_list = [g for g in formatted_games if g[1] < median_pts]
        brutal_list = [g for g in formatted_games if g[3] > median_pts]

        snap = []
        for tid, cr in cum_records.items():
            snap.append([tid, cr["w"], cr["l"], scores.get(tid, 0.0), cr["pf"], cr["pa"], round(cr["pf"] - cr["pa"], 2)])
        snap.sort(key=lambda x: (-x[1], -x[4]))

        ed = WEEKLY_EDITORIALS.get(wk, {
            "kicker": f"ISSUE NO. {wk:02d} • WEEK {wk} RECAP",
            "headline": f"Week {wk} Recap: {teams[ranked_scores[0][0]]['name']} Takes the Belt ({ranked_scores[0][1]:.2f})",
            "subhead": f"Median score landed at {median_pts:.2f} across The Super Smash Alliance 10.0.",
            "teaser": f"Alliance Dispatch Week {wk} Recap & Standings",
        })

        weeks_summary[str(wk)] = {
            "week": wk,
            "kicker": ed["kicker"],
            "headline": ed["headline"],
            "subhead": ed["subhead"],
            "teaser": ed["teaser"],
            "high": [ranked_scores[0][0], ranked_scores[0][1]],
            "low": [ranked_scores[-1][0], ranked_scores[-1][1]],
            "median": median_pts,
            "closest": closest,
            "lucky": sorted(lucky_list, key=lambda g: g[1])[0] if lucky_list else None,
            "brutal": sorted(brutal_list, key=lambda g: -g[3])[0] if brutal_list else None,
            "games": formatted_games,
            "standings": snap,
        }

    pf_order = sorted(teams.values(), key=lambda x: -x["pf"])
    pa_order = sorted(teams.values(), key=lambda x: x["pa"])
    pf_ranks = {t["id"]: i + 1 for i, t in enumerate(pf_order)}
    pa_ranks = {t["id"]: i + 1 for i, t in enumerate(pa_order)}

    for tid, t in teams.items():
        apw, apl = all_play[tid]
        ap_pct = apw / max(1, (apw + apl))
        exp_w = ap_pct * completed_weeks
        t["allPlayW"] = apw
        t["allPlayL"] = apl
        t["allPlayPct"] = round(ap_pct, 3)
        t["luck"] = round(t["wins"] - exp_w, 2)
        t["pfRank"] = pf_ranks[tid]
        t["paRank"] = pa_ranks[tid]

    sorted_teams = sorted(teams.values(), key=lambda x: x["seed"])

    upcoming_cards = []
    for aid, hid in upcoming_matchups:
        pair = {aid, hid}
        note = "Parity elimination chamber matchup."
        if pair == {15, 1}:
            note = "#1 Scorer (1,099.8 PF) vs. #1 Luck Merchant (1 waiver move). Wills may sue ESPN if Feeney wins scoring 108."
        elif pair == {12, 3}:
            note = "Can Jacoby Brissett and 2-move O'Keefe snap Ronjohn's 6-game heater?"
        elif pair == {19, 17}:
            note = "Win and Jackson drags a 7th body into the .500 crab bucket."
        elif pair == {20, 2}:
            note = "Congrats in advance to Huffner on his upcoming 175-pt week against our Tanner McKee Superflex clinic."
        elif pair == {4, 13}:
            note = "2-5 Billy (911.6 PF) tries to drag D B down out of the top-4."
        elif pair == {5, 18}:
            note = "27-move Chase tries to climb back over the 2.30-pt playoff wall against red-hot 1-6 Owen."
        upcoming_cards.append([aid, hid, note])

    return {
        "leagueName": data.get("settings", {}).get("name", "The Super Smash Alliance 10.0"),
        "leagueId": LEAGUE_ID,
        "completedWeeks": completed_weeks,
        "upcomingWeek": current_mp,
        "teams": sorted_teams,
        "weeks": weeks_summary,
        "upcoming": upcoming_cards,
    }


def render_html_page(model, default_issue="midseason", base_prefix="./", is_root=False):
    if default_issue == "midseason":
        og_title = "SUPER SMASH ALLIANCE 10.0 — Midseason Roast: 8-Player Sudden Death & Bad Mother Tucker's K.O."
        og_desc = (
            "Official Midseason Smash Dispatch: 6 fighters deadlocked at 4-3, 8 of 12 trapped in 8-Player Sudden Death, "
            "0 trades, CPU Lv.1 Feeney's 1 waiver move, and 1-6 Bad Mother Tucker's launched off the Blast Zone."
        )
    else:
        wk_num = default_issue.replace("week-", "")
        wk_obj = model["weeks"].get(wk_num, {})
        og_title = f"SUPER SMASH ALLIANCE 10.0 — Stage {wk_num}: {wk_obj.get('headline', 'Weekly Smash Recap')}"
        og_desc = wk_obj.get("subhead", "Official Weekly Smash Recap & Standings for The Super Smash Alliance 10.0.")

    canonical_url = PUBLIC_SITE_URL if is_root else f"{PUBLIC_SITE_URL}recaps/{default_issue}/"
    og_image_url = f"{PUBLIC_SITE_URL}assets/smash-arena-hero.jpg"
    hero_img_src = f"{base_prefix}assets/smash-arena-hero.jpg"
    trophy_img_src = f"{base_prefix}assets/smash-bmt-trophy.jpg"
    favicon_svg = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
        "%3Cdefs%3E%3Cmask id='m'%3E%3Ccircle cx='50' cy='50' r='46' fill='white'/%3E"
        "%3Crect x='25' y='0' width='15' height='100' fill='black'/%3E"
        "%3Crect x='0' y='60' width='100' height='10' fill='black'/%3E%3C/mask%3E%3C/defs%3E"
        "%3Ccircle cx='50' cy='50' r='48' fill='%230B0D13'/%3E"
        "%3Ccircle cx='50' cy='50' r='44' fill='%23E60012' mask='url(%23m)'/%3E%3C/svg%3E"
    )
    json_payload = json.dumps(model, ensure_ascii=False, separators=(",", ":"))

    page = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(og_title)}</title>
  <meta name="description" content="{html.escape(og_desc)}" />
  <link rel="canonical" href="{html.escape(canonical_url)}" />
  <link rel="icon" type="image/svg+xml" href="{favicon_svg}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{html.escape(canonical_url)}" />
  <meta property="og:site_name" content="The Alliance Dispatch • Super Smash Alliance 10.0" />
  <meta property="og:title" content="{html.escape(og_title)}" />
  <meta property="og:description" content="{html.escape(og_desc)}" />
  <meta property="og:image" content="{html.escape(og_image_url)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{html.escape(og_title)}" />
  <meta name="twitter:description" content="{html.escape(og_desc)}" />
  <meta name="twitter:image" content="{html.escape(og_image_url)}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:ital,wght@0,600;0,700;1,700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&family=Kanit:ital,wght@0,700;0,800;0,900;1,800;1,900&family=Press+Start+2P&display=swap" rel="stylesheet" />
  <style>
    :root, [data-theme="light"] {{
      --bg: #F2F3F7;
      --bg-alt: #E5E8F0;
      --bg-dots: rgba(15, 18, 26, 0.055);
      --card: #FFFFFF;
      --ink: #0F121A;
      --ink-secondary: #373E4D;
      --ink-muted: #5E6678;
      --frame: #0F121A;
      --rule: #CFD5E2;
      --smash-red: #E60012;
      --smash-orange: #FF5E00;
      --smash-gold: #FFB800;
      --smash-blue: #0068B7;
      --crimson: #D90429;
      --crimson-bg: #FFF0F3;
      --crimson-border: #FF8FA3;
      --emerald: #008F4C;
      --emerald-bg: #ECFDF5;
      --emerald-border: #6EE7B7;
      --amber: #B45309;
      --amber-bg: #FFFBEB;
      --amber-border: #FCD34D;
      --slate-bg: #EAEFF8;
      --arcade-shadow: 4px 4px 0px #0F121A;
      --arcade-shadow-sm: 2px 2px 0px #0F121A;
    }}
    [data-theme="dark"] {{
      --bg: #0B0D14;
      --bg-alt: #131724;
      --bg-dots: rgba(255, 255, 255, 0.045);
      --card: #161B29;
      --ink: #F5F7FC;
      --ink-secondary: #C5CCE0;
      --ink-muted: #8E97B0;
      --frame: #2E364F;
      --rule: #283046;
      --smash-red: #FF1E2D;
      --smash-orange: #FF7315;
      --smash-gold: #FFD000;
      --smash-blue: #2997FF;
      --crimson: #FF4D6D;
      --crimson-bg: rgba(217, 4, 41, 0.17);
      --crimson-border: rgba(255, 77, 109, 0.45);
      --emerald: #2CE59B;
      --emerald-bg: rgba(0, 143, 76, 0.2);
      --emerald-border: rgba(44, 229, 155, 0.4);
      --amber: #FFC933;
      --amber-bg: rgba(255, 184, 0, 0.14);
      --amber-border: rgba(255, 201, 51, 0.42);
      --slate-bg: #1F263A;
      --arcade-shadow: 4px 4px 0px #000000;
      --arcade-shadow-sm: 2px 2px 0px #000000;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      background-image: radial-gradient(var(--bg-dots) 1.25px, transparent 1.25px);
      background-size: 16px 16px;
      color: var(--ink);
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 15px;
      line-height: 1.56;
      -webkit-font-smoothing: antialiased;
      padding-bottom: 72px;
    }}
    .mono {{
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-variant-numeric: tabular-nums;
    }}
    .smash-display {{
      font-family: "Kanit", "Impact", sans-serif;
      font-weight: 900;
      font-style: italic;
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }}
    .smash-hud {{
      font-family: "Chakra Petch", "Kanit", sans-serif;
      font-weight: 700;
      font-style: italic;
      font-variant-numeric: tabular-nums;
    }}
    .pixel {{
      font-family: "Press Start 2P", monospace;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .container {{ max-width: 1140px; margin: 0 auto; padding: 0 18px; }}

    /* Top Nintendo Switch / Smash Ultimate Arcade Masthead */
    .masthead {{
      background: linear-gradient(135deg, #070910 0%, #161024 55%, #2B0914 100%);
      color: #FFFFFF;
      border-bottom: 4px solid var(--smash-red);
      position: relative;
      overflow: hidden;
    }}
    .masthead::before {{
      content: "";
      position: absolute;
      top: 0; bottom: 0; left: -8%;
      width: 26%;
      background: linear-gradient(180deg, rgba(230, 0, 18, 0.24), rgba(255, 184, 0, 0.08));
      transform: skewX(-18deg);
      pointer-events: none;
    }}
    .masthead-top {{
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
      padding: 12px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.14);
      position: relative; z-index: 2;
    }}
    .rules-ticker {{
      font-size: 9.5px;
      color: #FFD000;
      line-height: 1.5;
    }}
    .masthead-actions {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .btn {{
      appearance: none;
      border: 2px solid var(--frame);
      background: var(--card);
      color: var(--ink);
      font-family: "Kanit", sans-serif;
      font-weight: 800;
      font-style: italic;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      font-size: 12.5px;
      padding: 6px 13px;
      border-radius: 4px;
      cursor: pointer;
      box-shadow: var(--arcade-shadow-sm);
      transition: transform 0.12s ease, background 0.12s ease;
      display: inline-flex; align-items: center; gap: 6px; text-decoration: none;
    }}
    .btn:hover {{ transform: translate(-1px, -1px); }}
    .btn-masthead {{
      background: rgba(255, 255, 255, 0.1);
      color: #FFFFFF;
      border-color: rgba(255, 255, 255, 0.35);
      box-shadow: 2px 2px 0px #000000;
    }}
    .btn-masthead:hover {{ background: rgba(255, 255, 255, 0.2); }}
    .btn-primary {{
      background: linear-gradient(135deg, #E60012 0%, #FF5E00 100%);
      color: #FFFFFF;
      border-color: #FFD000;
      box-shadow: 2px 2px 0px #000000;
    }}
    .btn-primary:hover {{ filter: brightness(1.08); }}

    /* Arena Hero Stage Showcase */
    .arena-banner {{
      position: relative;
      margin: 16px 0 18px;
      border-radius: 10px;
      overflow: hidden;
      border: 3px solid #FFD000;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.55);
      min-height: 250px;
      display: flex;
      align-items: flex-end;
      background: #090B12;
    }}
    .arena-img {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 38%;
      opacity: 0.82;
    }}
    .arena-scrim {{
      position: absolute;
      inset: 0;
      background: linear-gradient(
        0deg,
        rgba(7, 9, 16, 0.95) 0%,
        rgba(7, 9, 16, 0.68) 46%,
        rgba(7, 9, 16, 0.18) 100%
      );
    }}
    .arena-content {{
      position: relative;
      z-index: 2;
      padding: 22px 24px 20px;
      width: 100%;
      display: flex;
      align-items: center;
      gap: 18px;
      flex-wrap: wrap;
    }}
    .brand-emblem {{
      width: 62px;
      height: 62px;
      flex-shrink: 0;
      filter: drop-shadow(0 0 12px rgba(255, 94, 0, 0.75));
    }}
    .brand-title {{
      font-size: clamp(28px, 5vw, 48px);
      line-height: 0.98;
      color: #FFFFFF;
      text-shadow: 3px 3px 0px #E60012, 6px 6px 0px #000000;
    }}
    .brand-sub {{
      margin-top: 6px;
      font-size: 13.5px;
      color: #E2E8F0;
      font-weight: 600;
    }}
    .brand-pill {{
      display: inline-block;
      background: #FFD000;
      color: #0B0D13;
      font-weight: 900;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 3px;
      margin-right: 6px;
      text-transform: uppercase;
      transform: skewX(-10deg);
    }}

    /* Sticky Slanted Stage-Select Bar */
    .edition-bar {{
      background: #0F121A;
      border-bottom: 3px solid var(--smash-gold);
      position: sticky;
      top: 0;
      z-index: 40;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.22);
    }}
    .edition-inner {{ display: flex; align-items: center; gap: 8px; overflow-x: auto; padding: 10px 0; }}
    .edition-label {{
      font-size: 10px;
      color: #FFD000;
      margin-right: 6px;
      white-space: nowrap;
    }}
    .edition-tab {{
      appearance: none;
      border: 2px solid #2D3548;
      background: #1B2030;
      color: #CBD5E1;
      font-family: "Kanit", sans-serif;
      font-size: 13px;
      font-weight: 800;
      font-style: italic;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      padding: 6px 14px;
      cursor: pointer;
      white-space: nowrap;
      transform: skewX(-10deg);
      transition: all 0.14s ease;
    }}
    .edition-tab span {{ display: inline-block; transform: skewX(10deg); }}
    .edition-tab:hover {{ border-color: #FFD000; color: #FFFFFF; }}
    .edition-tab.active {{
      background: linear-gradient(135deg, #E60012 0%, #FF5E00 100%);
      color: #FFFFFF;
      border-color: #FFD000;
      box-shadow: 2px 2px 0px #000000;
    }}

    /* Challenger Approaching Headline Section */
    .hero {{
      margin-top: 22px;
      padding: 24px 26px;
      background: var(--card);
      border: 2.5px solid var(--frame);
      border-left: 8px solid var(--smash-red);
      border-radius: 8px;
      box-shadow: var(--arcade-shadow);
      position: relative;
      overflow: hidden;
    }}
    .kicker {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--smash-red);
      color: #FFFFFF;
      font-family: "Kanit", sans-serif;
      font-size: 12.5px;
      font-weight: 900;
      font-style: italic;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      padding: 4px 12px;
      transform: skewX(-10deg);
      margin-bottom: 12px;
      box-shadow: 2px 2px 0px #0F121A;
    }}
    .kicker > span {{ transform: skewX(10deg); }}
    .hero h1 {{
      font-size: clamp(26px, 4.1vw, 41px);
      line-height: 1.07;
      max-width: 960px;
      color: var(--ink);
    }}
    .hero-lede {{
      margin-top: 13px;
      font-size: 16px;
      line-height: 1.58;
      color: var(--ink-secondary);
      max-width: 900px;
    }}
    .byline {{
      margin-top: 16px;
      padding-top: 12px;
      border-top: 1.5px dashed var(--rule);
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      color: var(--ink-muted);
    }}
    .ledge-badge {{
      background: #0F121A;
      color: #FFD000;
      padding: 4px 10px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 12px;
    }}

    /* 4 Arcade HUD Boxes */
    .stat-strip {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(225px, 1fr)); gap: 14px; margin: 22px 0; }}
    .stat-box {{
      background: var(--card);
      border: 2.5px solid var(--frame);
      border-radius: 8px;
      padding: 16px 17px;
      box-shadow: var(--arcade-shadow);
      position: relative;
      overflow: hidden;
    }}
    .stat-box::after {{
      content: "";
      position: absolute;
      top: 0; right: 0;
      width: 44px; height: 6px;
      background: var(--smash-red);
    }}
    .stat-box-label {{
      font-family: "Kanit", sans-serif;
      font-size: 12.5px;
      font-weight: 800;
      font-style: italic;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--ink-muted);
    }}
    .stat-box-val {{
      font-size: 28px;
      line-height: 1.1;
      margin-top: 5px;
    }}
    .stat-box-note {{ font-size: 13px; color: var(--ink-secondary); margin-top: 5px; line-height: 1.45; }}

    /* Section Headers with Smash Slash Accent */
    .section {{ margin-top: 38px; }}
    .section-header {{
      display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 10px;
      padding-bottom: 10px; border-bottom: 3px solid var(--frame); margin-bottom: 16px;
    }}
    [data-theme="dark"] .section-header {{ border-bottom-color: var(--smash-red); }}
    .section-title-wrap {{ display: flex; align-items: center; gap: 10px; }}
    .section-slash {{
      display: inline-block;
      width: 10px;
      height: 24px;
      background: linear-gradient(180deg, var(--smash-red), var(--smash-orange));
      transform: skewX(-16deg);
      flex-shrink: 0;
    }}
    .section-title {{ font-size: clamp(21px, 3vw, 27px); line-height: 1.1; }}
    .section-sub {{ font-size: 13px; color: var(--ink-muted); font-weight: 600; }}

    /* 8-Player Smash Sudden Death Stage Panel */
    .parity-panel {{
      background: var(--card);
      border: 2.5px solid var(--frame);
      border-radius: 8px;
      padding: 20px;
      box-shadow: var(--arcade-shadow);
    }}
    .parity-tiers {{ display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 16px; }}
    .tier-row {{
      display: flex; flex-wrap: wrap; align-items: center; gap: 12px;
      padding: 13px 15px; border-radius: 6px;
      border: 2px solid var(--rule);
      background: var(--bg);
    }}
    .tier-row.highlight-boss {{
      border-color: var(--smash-blue);
      background: var(--slate-bg);
    }}
    .tier-row.highlight-parity {{
      background: var(--amber-bg);
      border: 2.5px solid #F59E0B;
      box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.25);
    }}
    .tier-row.highlight-morgue {{
      background: var(--crimson-bg);
      border: 2px solid var(--crimson-border);
    }}
    .tier-tag {{
      font-family: "Kanit", sans-serif;
      font-size: 13.5px;
      font-weight: 900;
      font-style: italic;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      min-width: 245px;
    }}
    .tier-chips {{ display: flex; flex-wrap: wrap; gap: 7px; flex: 1; }}
    .team-chip {{
      font-family: "Chakra Petch", sans-serif;
      font-size: 13px;
      font-weight: 700;
      padding: 6px 11px;
      border-radius: 4px;
      background: var(--card);
      border: 2px solid var(--frame);
      color: var(--ink);
      cursor: pointer;
      box-shadow: var(--arcade-shadow-sm);
      transition: transform 0.1s ease, background 0.1s ease;
    }}
    .team-chip:hover {{
      transform: translate(-1px, -1px);
      background: var(--smash-red);
      color: #FFFFFF;
      border-color: #0F121A;
    }}

    /* Smash Trophy Gallery Autopsy Card (Bad Mother Tucker's) */
    .autopsy-card {{
      background: var(--crimson-bg);
      border: 3px solid var(--crimson);
      border-radius: 10px;
      padding: 22px;
      box-shadow: var(--arcade-shadow);
      position: relative;
      overflow: hidden;
    }}
    .hazard-ribbon {{
      background: repeating-linear-gradient(
        -45deg,
        #0F121A,
        #0F121A 12px,
        #FFD000 12px,
        #FFD000 24px
      );
      height: 8px;
      margin: -22px -22px 16px -22px;
    }}
    .autopsy-layout {{
      display: grid;
      grid-template-columns: 235px 1.25fr 1fr;
      gap: 20px;
      margin-top: 14px;
      align-items: start;
    }}
    @media (max-width: 980px) {{
      .autopsy-layout {{ grid-template-columns: 1fr; }}
    }}
    .trophy-showcase {{
      background: #0B0D14;
      border: 2.5px solid #FFD000;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 3px 3px 0px #0F121A;
      text-align: center;
    }}
    .trophy-showcase img {{
      width: 100%;
      aspect-ratio: 1 / 1;
      object-fit: cover;
      display: block;
    }}
    .trophy-caption {{
      padding: 8px 10px;
      background: #141826;
      color: #FFD000;
      font-size: 11px;
      border-top: 2px solid #FFD000;
    }}
    .autopsy-list {{ list-style: none; display: flex; flex-direction: column; gap: 11px; }}
    .autopsy-list li {{ font-size: 14.5px; line-height: 1.54; }}
    .crime-box {{
      background: var(--card);
      border: 2px solid var(--frame);
      border-radius: 8px;
      padding: 15px;
      box-shadow: var(--arcade-shadow-sm);
    }}
    .crime-row {{ display: flex; justify-content: space-between; gap: 8px; padding: 7px 0; border-bottom: 1px solid var(--rule); font-size: 13px; }}
    .crime-row:last-child {{ border-bottom: none; }}

    /* Tourney Standings Table */
    .table-wrap {{
      background: var(--card);
      border: 2.5px solid var(--frame);
      border-radius: 8px;
      overflow-x: auto;
      box-shadow: var(--arcade-shadow);
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
    th {{
      text-align: left; padding: 11px 12px;
      background: #0F121A;
      color: #FFD000;
      border-bottom: 2px solid var(--smash-red);
      font-family: "Kanit", sans-serif;
      font-size: 12.5px; font-weight: 800; font-style: italic;
      text-transform: uppercase; letter-spacing: 0.05em;
      cursor: pointer; user-select: none; white-space: nowrap;
    }}
    th:hover {{ color: #FFFFFF; }}
    th.num, td.num {{ text-align: right; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid var(--rule); white-space: nowrap; background: var(--card); }}
    th.sticky-col, td.sticky-col {{ position: sticky; left: 0; z-index: 2; }}
    th.sticky-col {{ background: #0F121A; z-index: 3; }}
    tr.team-row {{ cursor: pointer; }}
    tr.team-row:hover td {{ background: var(--slate-bg); }}
    tr.playoff-cut td {{ border-bottom: 3px dashed var(--emerald); }}
    .badge {{ display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 12px; font-weight: 700; }}
    .badge-pos {{ background: var(--emerald-bg); color: var(--emerald); border: 1px solid var(--emerald-border); }}
    .badge-neg {{ background: var(--crimson-bg); color: var(--crimson); border: 1px solid var(--crimson-border); }}
    .badge-mid {{ background: var(--amber-bg); color: var(--amber); border: 1px solid var(--amber-border); }}

    /* Character Select Filter Pills */
    .filter-bar {{ display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 18px; }}
    .filter-pill {{
      appearance: none;
      border: 2px solid var(--frame);
      background: var(--card);
      color: var(--ink-secondary);
      font-family: "Kanit", sans-serif;
      font-size: 12.5px; font-weight: 800; font-style: italic;
      text-transform: uppercase;
      padding: 6px 12px; border-radius: 4px; cursor: pointer;
      box-shadow: var(--arcade-shadow-sm);
    }}
    .filter-pill:hover {{ color: var(--ink); border-color: var(--smash-red); }}
    .filter-pill.active {{
      background: var(--smash-red);
      color: #FFFFFF;
      border-color: #0F121A;
    }}

    /* Character Select Fighter Roast Cards (1P .. 12P) */
    .roast-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(335px, 1fr)); gap: 18px; }}
    .roast-card {{
      background: var(--card);
      border: 2.5px solid var(--frame);
      border-radius: 9px;
      overflow: hidden;
      box-shadow: var(--arcade-shadow);
      display: flex;
      flex-direction: column;
      position: relative;
    }}
    .roast-card.is-bmt {{
      border: 3px solid var(--crimson);
    }}
    .fighter-topbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 7px 14px;
      color: #FFFFFF;
      font-size: 12px;
      font-weight: 800;
      border-bottom: 2px solid var(--frame);
    }}
    .fighter-port {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      letter-spacing: 0.06em;
    }}
    .stock-row {{
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }}
    .smash-stock {{
      width: 14px;
      height: 14px;
      display: inline-block;
    }}
    .smash-stock.ko {{ opacity: 0.32; }}
    .roast-inner {{
      padding: 16px 18px 18px;
      display: flex;
      flex-direction: column;
      gap: 11px;
      flex: 1;
      position: relative;
    }}
    .roast-watermark {{
      position: absolute;
      right: -12px;
      bottom: -12px;
      width: 120px;
      height: 120px;
      opacity: 0.045;
      pointer-events: none;
    }}
    .roast-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }}
    .roast-team {{ font-size: 22px; line-height: 1.08; color: var(--ink); }}
    .roast-mgr {{ font-size: 13px; color: var(--ink-muted); font-weight: 600; margin-top: 2px; }}
    .splash-ribbon {{
      display: inline-block;
      align-self: flex-start;
      background: #0F121A;
      color: #FFD000;
      font-family: "Kanit", sans-serif;
      font-weight: 800;
      font-style: italic;
      font-size: 13px;
      padding: 3px 11px;
      border-left: 4px solid var(--smash-red);
      transform: skewX(-8deg);
    }}
    [data-theme="dark"] .splash-ribbon {{ background: #232B42; }}
    .splash-ribbon span {{ display: inline-block; transform: skewX(8deg); }}

    /* Smash Bros Bottom-HUD Damage % + Metrics Strip */
    .roast-hud {{
      display: grid;
      grid-template-columns: 1.15fr repeat(4, 1fr);
      gap: 5px;
      padding: 9px 8px;
      background: #0F121A;
      color: #FFFFFF;
      border-radius: 6px;
      border: 2px solid var(--frame);
      text-align: center;
      align-items: center;
    }}
    .dmg-meter {{
      border-right: 1px solid rgba(255, 255, 255, 0.16);
      padding-right: 6px;
    }}
    .dmg-val {{
      font-size: 20px;
      line-height: 1;
      text-shadow: 2px 2px 0px #000000;
    }}
    .dmg-pct {{ font-size: 12px; }}
    .rm-label {{ font-size: 10.5px; color: #94A3B8; text-transform: uppercase; font-weight: 700; }}
    .rm-val {{ font-size: 13px; font-weight: 700; margin-top: 2px; color: #F8FAFC; }}

    .roast-crime {{
      font-size: 12.5px; font-weight: 700; padding: 7px 10px; border-radius: 5px;
      background: var(--amber-bg); color: var(--amber); border: 1.5px solid var(--amber-border);
    }}
    .roast-body {{ font-size: 14.5px; line-height: 1.57; color: var(--ink); position: relative; z-index: 1; }}

    .spark-wrap {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; align-items: end; padding-top: 6px; margin-top: auto; }}
    .spark-col {{ display: flex; flex-direction: column; align-items: center; gap: 3px; }}
    .spark-bar-bg {{ width: 100%; height: 42px; background: var(--bg-alt); border-radius: 3px; border: 1px solid var(--rule); display: flex; align-items: flex-end; overflow: hidden; }}
    .spark-bar {{ width: 100%; }}
    .spark-bar.win {{ background: linear-gradient(180deg, #10B981, #047857); }}
    .spark-bar.loss {{ background: linear-gradient(180deg, #F43F5E, #BE123C); }}
    .spark-pts {{ font-size: 11.5px; color: var(--ink-secondary); font-weight: 700; }}
    .spark-wk {{ font-size: 11px; color: var(--ink-muted); }}

    /* Versus Screen Matchup Cards */
    .matchup-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); gap: 14px; }}
    .matchup-card {{
      background: var(--card);
      border: 2.5px solid var(--frame);
      border-radius: 8px;
      padding: 14px 16px;
      box-shadow: var(--arcade-shadow);
    }}
    .mc-row {{ display: flex; justify-content: space-between; align-items: center; padding: 5px 0; font-size: 14.5px; }}
    .mc-row.winner {{ font-weight: 700; }}
    .mc-row.loser {{ color: var(--ink-muted); }}
    .vs-divider {{
      display: flex; align-items: center; gap: 8px; margin: 2px 0;
    }}
    .vs-divider::before, .vs-divider::after {{
      content: ""; flex: 1; height: 1px; background: var(--rule);
    }}
    .vs-pill {{
      background: linear-gradient(135deg, #E60012, #FF5E00);
      color: #FFFFFF;
      font-family: "Kanit", sans-serif;
      font-weight: 900;
      font-style: italic;
      font-size: 11px;
      padding: 1px 8px;
      border-radius: 3px;
      transform: skewX(-12deg);
    }}
    .mc-foot {{
      margin-top: 9px; padding-top: 8px; border-top: 1.5px dashed var(--rule);
      font-size: 12.5px; color: var(--ink-secondary); display: flex; justify-content: space-between; gap: 8px;
    }}

    .toast {{
      position: fixed; bottom: 20px; right: 20px;
      background: #0F121A; color: #FFD000;
      border: 2px solid #E60012;
      padding: 10px 16px; border-radius: 6px;
      font-family: "Kanit", sans-serif; font-size: 13.5px; font-weight: 800; font-style: italic; text-transform: uppercase;
      box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.45); opacity: 0; pointer-events: none;
      transform: translateY(8px); transition: all 0.2s ease; z-index: 100;
    }}
    .toast.show {{ opacity: 1; transform: translateY(0); }}
    .hidden {{ display: none !important; }}
  </style>
</head>
<body>
  <!-- Reusable Super Smash Bros. Crosshair Emblem SVG Definitions -->
  <svg width="0" height="0" style="position:absolute;width:0;height:0;overflow:hidden;" aria-hidden="true">
    <defs>
      <linearGradient id="smash-flame-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#FFE600" />
        <stop offset="45%" stop-color="#FF5E00" />
        <stop offset="100%" stop-color="#E60012" />
      </linearGradient>
      <linearGradient id="smash-ko-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#64748B" />
        <stop offset="100%" stop-color="#334155" />
      </linearGradient>
      <mask id="smash-ball-cutout">
        <rect x="0" y="0" width="100" height="100" fill="black" />
        <circle cx="50" cy="50" r="46" fill="white" />
        <rect x="24" y="0" width="15" height="100" fill="black" />
        <rect x="0" y="60" width="100" height="10" fill="black" />
      </mask>
      <symbol id="smash-ball-flame" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="46" fill="url(#smash-flame-grad)" mask="url(#smash-ball-cutout)" />
      </symbol>
      <symbol id="smash-ball-ko" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="46" fill="url(#smash-ko-grad)" mask="url(#smash-ball-cutout)" />
      </symbol>
      <symbol id="smash-ball-mono" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="46" fill="currentColor" mask="url(#smash-ball-cutout)" />
      </symbol>
    </defs>
  </svg>

  <header class="masthead">
    <div class="container">
      <div class="masthead-top">
        <span class="pixel rules-ticker">NO TRADES • SUPERFLEX ONLY • FINAL DESTINATION • 12-FIGHTER PPR</span>
        <div class="masthead-actions">
          <button id="btn-copy-link" class="btn btn-primary" type="button">Copy Group-Chat Link</button>
          <button id="btn-theme" class="btn btn-masthead" type="button">Final Destination (Dark)</button>
          <a class="btn btn-masthead" href="https://fantasy.espn.com/football/league?leagueId={model['leagueId']}" target="_blank" rel="noopener">ESPN Arena</a>
        </div>
      </div>

      <div class="arena-banner">
        <img
          class="arena-img"
          src="{html.escape(hero_img_src)}"
          onerror="this.onerror=null;this.src='{html.escape(og_image_url)}';"
          alt="Super Smash Alliance 10.0 Final Destination Football Arena"
        />
        <div class="arena-scrim"></div>
        <div class="arena-content">
          <svg class="brand-emblem" viewBox="0 0 100 100" aria-hidden="true">
            <use href="#smash-ball-flame"></use>
          </svg>
          <div>
            <div class="brand-title smash-display">{html.escape(model['leagueName'])}</div>
            <div class="brand-sub">
              <span class="brand-pill">THE ALLIANCE DISPATCH</span>
              Broadcast Live From the 12th-Place Blast Zone at Bad Mother Tucker's HQ
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>

  <nav class="edition-bar" aria-label="Stage Select Editions">
    <div class="container edition-inner" id="edition-tabs">
      <span class="edition-label pixel">STAGE SELECT:</span>
    </div>
  </nav>

  <main class="container">
    <div id="view-midseason">
      <section class="hero">
        <div class="kicker"><span>CHALLENGER APPROACHING! • MIDSEASON ROAST (STAGE {model['completedWeeks']} OF 14)</span></div>
        <h1 class="smash-display">8-Player Sudden Death: 8 of You Are Trapped on One Platform, and I Already SD'd Off the Stage</h1>
        <p class="hero-lede">
          Welcome to the midpoint of <strong>The Super Smash Alliance 10.0</strong>: <strong>zero trades executed</strong>,
          <strong>six consecutive fighters deadlocked at 4-3 (4 stocks left)</strong>, <strong>eight of twelve managers crammed inside an
          8-Player Smash Sudden Death mosh pit</strong> within one game of .500, Kyle Feeney camping in 2nd place on
          <em>CPU Level 1</em> after making ONE waiver move since August, and your Head of Communications blasted off screen
          at <strong>1-6 (-261.64 Diff • 262% Damage)</strong>.
        </p>
        <div class="byline">
          <span>Announcer: <strong>Josh Briskman</strong> (12P • 1-6 • Permanent #1 Waiver Respawn)</span>
          <span class="ledge-badge mono">FINAL PLAYOFF LEDGE (#6 vs #7): 2.30 PTS</span>
        </div>
      </section>

      <div class="stat-strip">
        <div class="stat-box">
          <div class="stat-box-label">8-Player Sudden Death</div>
          <div class="stat-box-val smash-hud">8 OF 12 FIGHTERS</div>
          <div class="stat-box-note">Seeds #2 (5-2) through #9 (3-4) locked within ±1 stock of 4-3; 6 fighters tied at 4-3</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Playoff Ledge-Grab</div>
          <div class="stat-box-val smash-hud" style="color: var(--emerald);">2.30 POINTS</div>
          <div class="stat-box-note">#6 Huffner (918.32 PF) hangs onto the final chair over #7 #FedOut (916.02 PF)</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">AFK Controller Trophy</div>
          <div class="stat-box-val smash-hud" style="color: var(--smash-blue);">+1.91 LUCKY W's</div>
          <div class="stat-box-note">Feeney (5-2) is 9th in PF (856.4), 34-43 All-Play, with ONE (1) waiver move all year</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Blast-Zone Damage Meter</div>
          <div class="stat-box-val smash-hud" style="color: var(--crimson);">262% DAMAGE</div>
          <div class="stat-box-note">Bad Mother Tucker's (-261.64 Diff): #12 PF (753.16), #12 PA (1,014.80), L6 KO streak</div>
        </div>
      </div>

      <section class="section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-slash"></span>
            <h2 class="section-title smash-display">8-Player Smash (Sudden Death 300%): Six Fighters Tied at 4-3</h2>
          </div>
          <span class="section-sub">Tap any fighter badge to warp straight to their Character Card</span>
        </div>
        <div class="parity-panel">
          <p style="color: var(--ink-secondary); font-size: 14.5px;">
            Only <strong>6 tournament brackets</strong> advance to December, yet <strong>8 fighters sit at 4-3 or better</strong>—meaning two winning
            records are getting edge-guarded straight into the consolation pit—while <strong>Seeds #2 through #9 (two-thirds of the entire roster)</strong>
            are separated by a single Sunday stock. Naturally, <strong>0 trades</strong> have happened because everyone thinks their mid-tier main is S-Tier.
          </p>
          <div class="parity-tiers" id="parity-tiers"></div>
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-slash"></span>
            <h2 class="section-title smash-display">Trophy Gallery: Bad Mother Tucker's 1-6 Self-Destruct Pedestal</h2>
          </div>
          <span class="section-sub">"GAME!" — You cannot KO a man who side-B'd off Final Destination in Week 2</span>
        </div>
        <div class="autopsy-card">
          <div class="hazard-ribbon"></div>
          <p style="font-size: 15px; font-weight: 700;">
            Before anyone types "fix your own roster, Josh," allow Player 12 to inspect his own smoking trophy in the vault first:
          </p>
          <div class="autopsy-layout">
            <div class="trophy-showcase">
              <img
                src="{html.escape(trophy_img_src)}"
                onerror="this.onerror=null;this.src='{html.escape(PUBLIC_SITE_URL)}assets/smash-bmt-trophy.jpg';"
                alt="Bad Mother Tucker's Cracked Football Helmet Smash Trophy"
              />
              <div class="trophy-caption smash-hud">TROPHY #012 • "CLINICALLY K.O.'D" (1-6)</div>
            </div>
            <ul class="autopsy-list">
              <li><strong>Wasted Final Smash in Week 1:</strong> Dropped <span class="mono">153.64</span> on Owen in Week 1 to open 1-0, taunted on the ledge, and immediately lost <strong>6 straight stocks</strong>—finishing as the weekly low scorer 3 times in 4 weeks (<span class="mono">100.88</span>, <span class="mono">87.14</span>, <span class="mono">93.46</span>, plus <span class="mono">81.20</span> in Wk 6).</li>
              <li><strong>300% Stamina Handicap + Worst Hitbox:</strong> Opponents average a league-high <span class="mono">144.97 PPG</span> (<span class="mono">1,014.80 PA</span>) against us—highlighted by Wills' <span class="mono">207.86</span>-point Final Smash execution in Week 2 (-106.98 margin) and Billy's <span class="mono">183.00</span> combo in Week 5. And we can't even blame RNG because we <em>also</em> rank dead last in scoring (<span class="mono">753.16 PF</span>, nearly 80 pts behind 11th).</li>
              <li><strong>Unlockable Joke Character at QB1:</strong> Currently maining <strong>Tanner McKee (<span class="mono">23.14</span> season pts)</strong> in Superflex while camping #1 resetting waivers. ESPN still gives us a <span class="mono">2.6%</span> playoff chance—pure Nintendo rubber-banding myth.</li>
            </ul>
            <div class="crime-box">
              <div class="smash-display" style="font-size: 14px; color: var(--crimson); margin-bottom: 8px;">
                Poké Ball / Item RNG From Hell (Rds 1–4 vs. Reality)
              </div>
              <div class="crime-row"><span><strong>Rd 1 (#7)</strong> Jalen Hurts (QB)</span><span class="mono" style="color: var(--crimson);">K.O. / Off Roster</span></div>
              <div class="crime-row"><span><strong>Rd 2 (#18)</strong> Justin Jefferson (WR)</span><span class="mono">72.10 pts (#6 on team)</span></div>
              <div class="crime-row"><span><strong>Rd 3 (#31)</strong> Kyler Murray (QB)</span><span class="mono">53.68 pts (Outscored by K)</span></div>
              <div class="crime-row"><span><strong>Rd 4 (#42)</strong> Breece Hall (RB)</span><span class="mono">43.50 pts (Benched)</span></div>
              <div class="crime-row"><span><strong>Rd 10 (#114)</strong> Brandon Aubrey (K)</span><span class="mono" style="color: var(--emerald);">58.00 pts (&gt; Kyler)</span></div>
              <div class="crime-row"><span><strong>Rd 14 (#162)</strong> Steelers D/ST</span><span class="mono" style="color: var(--emerald);">57.00 pts (&gt; Kyler)</span></div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-slash"></span>
            <h2 class="section-title smash-display">Tournament Bracket Receipts: Stocks, All-Play &amp; RNG Luck</h2>
          </div>
          <span class="section-sub">Click any column header to sort • Dashed emerald line = Top-6 Bracket Ledge</span>
        </div>
        <div class="table-wrap">
          <table id="standings-table">
            <thead>
              <tr>
                <th data-sort="seed">Slot</th>
                <th data-sort="name" class="sticky-col">Fighter (Manager)</th>
                <th data-sort="wins" class="num">Stocks (W-L)</th>
                <th class="num">Streak</th>
                <th data-sort="pf" class="num">Points For</th>
                <th data-sort="pa" class="num">Damage Taken</th>
                <th data-sort="diff" class="num">Diff</th>
                <th data-sort="allPlayPct" class="num">All-Play</th>
                <th data-sort="luck" class="num">RNG Luck</th>
                <th data-sort="moves" class="num">Moves</th>
                <th data-sort="playoffPct" class="num">Bracket %</th>
              </tr>
            </thead>
            <tbody id="standings-tbody"></tbody>
          </table>
        </div>
      </section>

      <section class="section" id="roasts-section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-slash"></span>
            <h2 class="section-title smash-display">Choose Your Fighter: All 12 Franchises Roasted</h2>
          </div>
          <span class="section-sub">Filter by battle tier or select a friend's fighter slot</span>
        </div>
        <div class="filter-bar" id="team-filters"></div>
        <div class="roast-grid" id="roast-grid"></div>
      </section>

      <section class="section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-slash"></span>
            <h2 class="section-title smash-display">Challengers Approaching: Stage {model['upcomingWeek']} Versus Screen</h2>
          </div>
          <span class="section-sub">Next round of Sudden Death elimination matchups</span>
        </div>
        <div class="matchup-grid" id="upcoming-grid"></div>
      </section>
    </div>

    <div id="view-weekly" class="hidden">
      <section class="hero">
        <div class="kicker"><span id="wk-kicker"></span></div>
        <h1 class="smash-display" id="wk-headline"></h1>
        <p class="hero-lede" id="wk-subhead"></p>
        <div class="byline">
          <span>Announcer: <strong>Office of League Communications</strong> • The Super Smash Alliance 10.0</span>
          <span class="ledge-badge mono" id="wk-median-badge"></span>
        </div>
      </section>

      <div class="stat-strip" id="wk-awards"></div>

      <section class="section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-slash"></span>
            <h2 class="section-title smash-display" id="wk-scoreboard-title">Stage Results</h2>
          </div>
          <span class="section-sub">Sorted by highest-damage matchup</span>
        </div>
        <div class="matchup-grid" id="wk-games-grid"></div>
      </section>

      <section class="section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-slash"></span>
            <h2 class="section-title smash-display" id="wk-standings-title">Tournament Standings Snapshot</h2>
          </div>
          <span class="section-sub">Cumulative bracket standings at the end of this stage</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Slot</th>
                <th class="sticky-col">Fighter (Manager)</th>
                <th class="num">Stocks (W-L)</th>
                <th class="num">Stage Pts</th>
                <th class="num">Season PF</th>
                <th class="num">Damage Taken</th>
                <th class="num">Diff</th>
              </tr>
            </thead>
            <tbody id="wk-standings-tbody"></tbody>
          </table>
        </div>
      </section>
    </div>
  </main>

  <div id="toast" class="toast" role="status" aria-live="polite">Link copied!</div>

  <script>
    const LEAGUE_DATA = {json_payload};
    const DEFAULT_ISSUE = "{html.escape(default_issue)}";
    const BASE_PREFIX = "{html.escape(base_prefix)}";
    const PUBLIC_SITE_URL = "{html.escape(PUBLIC_SITE_URL)}";
    const TEAMS_BY_ID = Object.fromEntries(LEAGUE_DATA.teams.map(t => [t.id, t]));

    const PLAYER_PORT_STYLES = {{
      1:  {{ tag: "1P • TOP SEED",      bg: "linear-gradient(135deg, #E60012, #B8000E)" }},
      2:  {{ tag: "2P • CPU LV.1 AFK",  bg: "linear-gradient(135deg, #0068B7, #004B87)" }},
      3:  {{ tag: "3P • FINAL SMASH",   bg: "linear-gradient(135deg, #D97706, #B45309)" }},
      4:  {{ tag: "4P • ARCH-RIVAL",    bg: "linear-gradient(135deg, #009E52, #00703A)" }},
      5:  {{ tag: "5P • ZERO-RNG MAIN", bg: "linear-gradient(135deg, #F96302, #C2410C)" }},
      6:  {{ tag: "6P • LEDGE GRABBER", bg: "linear-gradient(135deg, #00838F, #006064)" }},
      7:  {{ tag: "7P • BUTTON MASHER", bg: "linear-gradient(135deg, #8E24AA, #6A1B9A)" }},
      8:  {{ tag: "8P • DUCT-TAPE",     bg: "linear-gradient(135deg, #455A64, #263238)" }},
      9:  {{ tag: "9P • SHIELD BROKEN", bg: "linear-gradient(135deg, #D81B60, #AD1457)" }},
      10: {{ tag: "10P • OVERKILL",     bg: "linear-gradient(135deg, #6D4C41, #4E342E)" }},
      11: {{ tag: "11P • EXTRA STOCK",  bg: "linear-gradient(135deg, #3949AB, #283593)" }},
      12: {{ tag: "12P • SD'D OFF MAP", bg: "linear-gradient(135deg, #991B1B, #450A0A)" }}
    }};

    function damageMeterColor(dmgPct) {{
      if (dmgPct >= 140) return "#FF4D6D";
      if (dmgPct >= 130) return "#FF8C00";
      if (dmgPct >= 120) return "#FFD000";
      return "#6EE7B7";
    }}

    function renderStockIcons(wins, losses) {{
      let out = '<span class="stock-row" title="' + wins + ' Stocks Remaining, ' + losses + ' KOs">';
      for (let i = 0; i < wins; i++) {{
        out += '<svg class="smash-stock" viewBox="0 0 100 100"><use href="#smash-ball-flame"></use></svg>';
      }}
      for (let j = 0; j < losses; j++) {{
        out += '<svg class="smash-stock ko" viewBox="0 0 100 100"><use href="#smash-ball-ko"></use></svg>';
      }}
      out += "</span>";
      return out;
    }}

    function canonicalIssueUrl(issueId, teamId) {{
      try {{
        const isLocalPreview = (
          window.location.protocol === "file:" ||
          window.location.protocol === "blob:" ||
          window.location.href.startsWith("about:")
        );
        const base = isLocalPreview
          ? new URL("recaps/" + issueId + "/", PUBLIC_SITE_URL)
          : new URL(BASE_PREFIX + "recaps/" + issueId + "/", window.location.href);
        if (teamId) base.searchParams.set("team", String(teamId));
        return base.toString();
      }} catch (_) {{
        return PUBLIC_SITE_URL + "recaps/" + issueId + "/" + (teamId ? "?team=" + teamId : "");
      }}
    }}

    let currentIssue = DEFAULT_ISSUE;
    let currentFilter = "all";
    let sortKey = "seed";
    let sortAsc = true;

    function showToast(msg) {{
      const el = document.getElementById("toast");
      el.textContent = msg;
      el.classList.add("show");
      clearTimeout(window.__toastTimer);
      window.__toastTimer = setTimeout(() => el.classList.remove("show"), 2600);
    }}

    function copyText(text, label) {{
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(text).then(() => showToast(label)).catch(() => fallbackCopy(text, label));
      }} else {{
        fallbackCopy(text, label);
      }}
    }}

    function fallbackCopy(text, label) {{
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      showToast(label);
    }}

    function buildEditionTabs() {{
      const bar = document.getElementById("edition-tabs");
      const editions = [{{ id: "midseason", label: "Midseason Smash Roast (Wks 1–" + LEAGUE_DATA.completedWeeks + ")" }}];
      for (let w = LEAGUE_DATA.completedWeeks; w >= 1; w--) {{
        editions.push({{ id: "week-" + w, label: "Stage " + w }});
      }}
      editions.forEach(ed => {{
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "edition-tab" + (ed.id === currentIssue ? " active" : "");
        btn.dataset.issue = ed.id;
        btn.innerHTML = `<span>${{ed.label}}</span>`;
        btn.addEventListener("click", () => selectIssue(ed.id, true));
        bar.appendChild(btn);
      }});
    }}

    function selectIssue(issueId, pushUrl) {{
      currentIssue = issueId;
      document.querySelectorAll(".edition-tab").forEach(b => b.classList.toggle("active", b.dataset.issue === issueId));
      const midView = document.getElementById("view-midseason");
      const wkView = document.getElementById("view-weekly");
      if (issueId === "midseason") {{
        midView.classList.remove("hidden");
        wkView.classList.add("hidden");
      }} else {{
        midView.classList.add("hidden");
        wkView.classList.remove("hidden");
        renderWeeklyView(issueId.replace("week-", ""));
      }}
      if (pushUrl && window.history && window.history.replaceState) {{
        try {{
          const url = new URL(window.location.href);
          url.searchParams.set("issue", issueId);
          window.history.replaceState({{}}, "", url.toString());
        }} catch (_) {{}}
      }}
      window.scrollTo({{ top: 0, behavior: "smooth" }});
    }}

    function renderParityTiers() {{
      const container = document.getElementById("parity-tiers");
      const tiers = [
        {{ label: "MASTER HAND PLATFORM (1P • 6 STOCKS)", cls: "highlight-boss", teams: LEAGUE_DATA.teams.filter(t => t.seed === 1) }},
        {{ label: "8-PLAYER SMASH: SUDDEN DEATH 300%! (#2–#9)", cls: "highlight-parity", teams: LEAGUE_DATA.teams.filter(t => t.seed >= 2 && t.seed <= 9) }},
        {{ label: "OFF THE BLAST ZONE — K.O. SCREEN (#10–#12)", cls: "highlight-morgue", teams: LEAGUE_DATA.teams.filter(t => t.seed >= 10) }}
      ];
      container.innerHTML = "";
      tiers.forEach(tr => {{
        const row = document.createElement("div");
        row.className = "tier-row " + tr.cls;
        const tag = document.createElement("div");
        tag.className = "tier-tag";
        tag.textContent = tr.label;
        const chips = document.createElement("div");
        chips.className = "tier-chips";
        tr.teams.forEach(t => {{
          const chip = document.createElement("button");
          chip.type = "button";
          chip.className = "team-chip";
          chip.textContent = `${{t.seed}}P • ${{t.name}} (${{t.wins}}-${{t.losses}})`;
          chip.addEventListener("click", () => focusTeamRoast(t.id));
          chips.appendChild(chip);
        }});
        row.appendChild(tag);
        row.appendChild(chips);
        container.appendChild(row);
      }});
    }}

    function renderStandingsTable() {{
      const tbody = document.getElementById("standings-tbody");
      const rows = [...LEAGUE_DATA.teams].sort((a, b) => {{
        const va = a[sortKey], vb = b[sortKey];
        if (typeof va === "string") return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
        return sortAsc ? va - vb : vb - va;
      }});
      tbody.innerHTML = "";
      rows.forEach(t => {{
        const tr = document.createElement("tr");
        tr.className = "team-row" + (sortKey === "seed" && sortAsc && t.seed === 6 ? " playoff-cut" : "");
        const luckCls = t.luck >= 0.7 ? "badge-pos" : (t.luck <= -0.7 ? "badge-neg" : "badge-mid");
        const luckSign = t.luck > 0 ? "+" : "";
        const diffSign = t.diff > 0 ? "+" : "";
        tr.innerHTML = `
          <td class="smash-hud"><strong>${{t.seed}}P</strong></td>
          <td class="sticky-col"><strong>${{t.name}}</strong> <span style="color: var(--ink-muted); font-size: 12.5px;">(${{t.manager}})</span></td>
          <td class="num mono"><strong>${{t.wins}}-${{t.losses}}</strong></td>
          <td class="num mono">${{t.streak}}</td>
          <td class="num mono">${{t.pf.toFixed(2)}} <span style="color: var(--ink-muted);">(#${{t.pfRank}})</span></td>
          <td class="num mono">${{t.pa.toFixed(2)}} <span style="color: var(--ink-muted);">(#${{t.paRank}})</span></td>
          <td class="num mono">${{diffSign}}${{t.diff.toFixed(2)}}</td>
          <td class="num mono">${{t.allPlayW}}-${{t.allPlayL}} (${{(t.allPlayPct * 100).toFixed(1)}}%)</td>
          <td class="num mono"><span class="badge ${{luckCls}}">${{luckSign}}${{t.luck.toFixed(2)}}</span></td>
          <td class="num mono">${{t.moves}}</td>
          <td class="num mono">${{t.playoffPct.toFixed(1)}}%</td>
        `;
        tr.addEventListener("click", () => focusTeamRoast(t.id));
        tbody.appendChild(tr);
      }});
    }}

    function renderTeamFilters() {{
      const bar = document.getElementById("team-filters");
      const presets = [
        {{ id: "all", label: "All 12 Fighters" }},
        {{ id: "parity8", label: "8-Player Sudden Death (#2–#9)" }},
        {{ id: "fourthree", label: "The 4-3 Stalemate (#3–#8)" }},
        {{ id: "bmt", label: "12P Self-Destruct (#12)" }}
      ];
      LEAGUE_DATA.teams.forEach(t => presets.push({{ id: "team-" + t.id, label: `${{t.seed}}P ${{t.name}}` }}));
      bar.innerHTML = "";
      presets.forEach(p => {{
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "filter-pill" + (currentFilter === p.id ? " active" : "");
        btn.dataset.filter = p.id;
        btn.textContent = p.label;
        btn.addEventListener("click", () => {{
          currentFilter = p.id;
          document.querySelectorAll(".filter-pill").forEach(el => el.classList.toggle("active", el.dataset.filter === p.id));
          renderRoastCards();
        }});
        bar.appendChild(btn);
      }});
    }}

    function renderRoastCards() {{
      const grid = document.getElementById("roast-grid");
      let list = LEAGUE_DATA.teams;
      if (currentFilter === "parity8") list = list.filter(t => t.seed >= 2 && t.seed <= 9);
      else if (currentFilter === "fourthree") list = list.filter(t => t.wins === 4 && t.losses === 3);
      else if (currentFilter === "bmt") list = list.filter(t => t.id === 2);
      else if (currentFilter.startsWith("team-")) {{
        const tid = Number(currentFilter.replace("team-", ""));
        list = list.filter(t => t.id === tid);
      }}

      grid.innerHTML = "";
      list.forEach(t => {{
        const card = document.createElement("article");
        card.className = "roast-card" + (t.id === 2 ? " is-bmt" : "");
        const port = PLAYER_PORT_STYLES[t.seed] || {{ tag: t.seed + "P • FIGHTER", bg: "#1E293B" }};
        const luckSign = t.luck > 0 ? "+" : "";
        const dmgPct = Math.round(t.pa / Math.max(1, LEAGUE_DATA.completedWeeks));
        const dmgColor = damageMeterColor(dmgPct);
        const stocksHtml = renderStockIcons(t.wins, t.losses);

        const sparks = t.weekly.map(w => {{
          const [wk, pts, oppId, oppPts, res] = w;
          const oppName = (TEAMS_BY_ID[oppId] || {{}}).name || "";
          const pct = Math.max(14, Math.min(100, Math.round(((pts - 55) / 155) * 100)));
          const cls = res === "W" ? "win" : "loss";
          return `
            <div class="spark-col" title="Stage ${{wk}}: ${{res}} ${{pts.toFixed(2)}} vs ${{oppName}} (${{oppPts.toFixed(2)}})">
              <div class="spark-pts mono">${{Math.round(pts)}}</div>
              <div class="spark-bar-bg"><div class="spark-bar ${{cls}}" style="height:${{pct}}%"></div></div>
              <div class="spark-wk mono">S${{wk}}${{res}}</div>
            </div>
          `;
        }}).join("");

        card.innerHTML = `
          <div class="fighter-topbar smash-hud" style="background: ${{port.bg}};">
            <span class="fighter-port">${{port.tag}} • ${{t.wins}}-${{t.losses}} (${{t.streak}})</span>
            ${{stocksHtml}}
          </div>
          <div class="roast-inner">
            <svg class="roast-watermark" viewBox="0 0 100 100" aria-hidden="true">
              <use href="#smash-ball-mono"></use>
            </svg>
            <div class="roast-head">
              <div>
                <h3 class="roast-team smash-display">${{t.name}}</h3>
                <div class="roast-mgr">${{t.manager}} • ${{t.playoffPct.toFixed(1)}}% Bracket Odds</div>
              </div>
              <button type="button" class="btn share-team-btn" data-tid="${{t.id}}" title="Copy direct link to this fighter's roast">Share</button>
            </div>
            <div class="splash-ribbon"><span>"${{t.epithet}}"</span></div>
            <div class="roast-hud mono">
              <div class="dmg-meter" title="Average Points Against Per Week (Smash Damage %)">
                <div class="dmg-val smash-hud" style="color: ${{dmgColor}};">${{dmgPct}}<span class="dmg-pct">%</span></div>
                <div class="rm-label">DMG/WK</div>
              </div>
              <div><div class="rm-label">PF</div><div class="rm-val">${{t.pf.toFixed(1)}}</div></div>
              <div><div class="rm-label">All-Play</div><div class="rm-val">${{t.allPlayW}}-${{t.allPlayL}}</div></div>
              <div><div class="rm-label">Luck</div><div class="rm-val">${{luckSign}}${{t.luck.toFixed(2)}}</div></div>
              <div><div class="rm-label">Moves</div><div class="rm-val">${{t.moves}}</div></div>
            </div>
            <div class="roast-crime">${{t.crime}}</div>
            <p class="roast-body">${{t.roast}}</p>
            <div class="spark-wrap">${{sparks}}</div>
          </div>
        `;
        grid.appendChild(card);
      }});

      grid.querySelectorAll(".share-team-btn").forEach(btn => {{
        btn.addEventListener("click", (e) => {{
          e.stopPropagation();
          const tid = Number(btn.dataset.tid);
          const team = TEAMS_BY_ID[tid];
          const link = canonicalIssueUrl("midseason", tid);
          copyText(`${{team.name}} (${{team.seed}}P, ${{team.wins}}-${{team.losses}}) — "${{team.epithet}}": ${{link}}`, `Copied ${{team.name}} fighter card!`);
        }});
      }});
    }}

    function focusTeamRoast(tid) {{
      currentFilter = "team-" + tid;
      document.querySelectorAll(".filter-pill").forEach(el => el.classList.toggle("active", el.dataset.filter === currentFilter));
      renderRoastCards();
      document.getElementById("roasts-section").scrollIntoView({{ behavior: "smooth", block: "start" }});
    }}

    function renderUpcoming() {{
      const grid = document.getElementById("upcoming-grid");
      grid.innerHTML = "";
      LEAGUE_DATA.upcoming.forEach(item => {{
        const [aid, hid, note] = item;
        const a = TEAMS_BY_ID[aid], h = TEAMS_BY_ID[hid];
        const div = document.createElement("div");
        div.className = "matchup-card";
        div.innerHTML = `
          <div class="mc-row winner"><span><strong class="smash-hud">${{a.seed}}P</strong> ${{a.name}}</span><span class="mono">${{a.wins}}-${{a.losses}}</span></div>
          <div class="vs-divider"><span class="vs-pill">VS</span></div>
          <div class="mc-row winner"><span><strong class="smash-hud">${{h.seed}}P</strong> ${{h.name}}</span><span class="mono">${{h.wins}}-${{h.losses}}</span></div>
          <div class="mc-foot"><span>${{note}}</span></div>
        `;
        grid.appendChild(div);
      }});
    }}

    function renderWeeklyView(wkNum) {{
      const wk = LEAGUE_DATA.weeks[String(wkNum)];
      if (!wk) return;
      document.getElementById("wk-kicker").textContent = wk.kicker;
      document.getElementById("wk-headline").textContent = wk.headline;
      document.getElementById("wk-subhead").textContent = wk.subhead;
      document.getElementById("wk-median-badge").textContent = `Stage Median Damage: ${{wk.median.toFixed(2)}} Pts`;
      document.getElementById("wk-scoreboard-title").textContent = `Stage ${{wk.week}} Final Smash Results`;
      document.getElementById("wk-standings-title").textContent = `Bracket Standings After Stage ${{wk.week}}`;

      const highT = TEAMS_BY_ID[wk.high[0]], lowT = TEAMS_BY_ID[wk.low[0]];
      const clW = TEAMS_BY_ID[wk.closest[0]], clL = TEAMS_BY_ID[wk.closest[2]];
      const luckyTxt = wk.lucky
        ? `${{TEAMS_BY_ID[wk.lucky[0]].name}} won with ${{wk.lucky[1].toFixed(2)}} (sub-median)`
        : "Every winner cleared the median";
      const brutalTxt = wk.brutal
        ? `${{TEAMS_BY_ID[wk.brutal[2]].name}} scored ${{wk.brutal[3].toFixed(2)}} and got KO'd`
        : "Every above-median scorer won";

      document.getElementById("wk-awards").innerHTML = `
        <div class="stat-box">
          <div class="stat-box-label">Final Smash MVP (High)</div>
          <div class="stat-box-val smash-hud" style="color: var(--emerald);">${{wk.high[1].toFixed(2)}}</div>
          <div class="stat-box-note"><strong>${{highT.name}}</strong> (${{highT.manager}})</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Self-Destruct Award (Low)</div>
          <div class="stat-box-val smash-hud" style="color: var(--crimson);">${{wk.low[1].toFixed(2)}}</div>
          <div class="stat-box-note"><strong>${{lowT.name}}</strong> (${{lowT.manager}})</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Last-Frame Ledge Trump</div>
          <div class="stat-box-val smash-hud">+${{wk.closest[4].toFixed(2)}} PTS</div>
          <div class="stat-box-note">${{clW.name}} (${{wk.closest[1].toFixed(2)}}) over ${{clL.name}} (${{wk.closest[3].toFixed(2)}})</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">RNG Item Drop &amp; Tilt</div>
          <div class="stat-box-val smash-hud" style="font-size: 20px;">MEDIAN: ${{wk.median.toFixed(2)}}</div>
          <div class="stat-box-note">${{brutalTxt}} • ${{luckyTxt}}</div>
        </div>
      `;

      const gamesGrid = document.getElementById("wk-games-grid");
      gamesGrid.innerHTML = "";
      wk.games.forEach(g => {{
        const [wid, wpts, lid, lpts, margin] = g;
        const card = document.createElement("div");
        card.className = "matchup-card";
        card.innerHTML = `
          <div class="mc-row winner"><span>${{TEAMS_BY_ID[wid].name}}</span><span class="mono">${{wpts.toFixed(2)}}</span></div>
          <div class="vs-divider"><span class="vs-pill">K.O.</span></div>
          <div class="mc-row loser"><span>${{TEAMS_BY_ID[lid].name}}</span><span class="mono">${{lpts.toFixed(2)}}</span></div>
          <div class="mc-foot">
            <span>Margin: <strong class="mono">+${{margin.toFixed(2)}}</strong></span>
            <span>${{wpts < wk.median ? "Sub-Median Cheese W" : (lpts > wk.median ? "Above-Median Bad Beat" : "Clean Stock W")}}</span>
          </div>
        `;
        gamesGrid.appendChild(card);
      }});

      const stBody = document.getElementById("wk-standings-tbody");
      stBody.innerHTML = "";
      wk.standings.forEach((s, idx) => {{
        const [tid, w, l, wkPts, pf, pa, diff] = s;
        const tm = TEAMS_BY_ID[tid];
        const rank = idx + 1;
        const tr = document.createElement("tr");
        if (rank === 6) tr.className = "playoff-cut";
        const dSign = diff > 0 ? "+" : "";
        tr.innerHTML = `
          <td class="smash-hud"><strong>${{rank}}P</strong></td>
          <td class="sticky-col"><strong>${{tm.name}}</strong> <span style="color: var(--ink-muted); font-size: 12.5px;">(${{tm.manager}})</span></td>
          <td class="num mono"><strong>${{w}}-${{l}}</strong></td>
          <td class="num mono">${{wkPts.toFixed(2)}}</td>
          <td class="num mono">${{pf.toFixed(2)}}</td>
          <td class="num mono">${{pa.toFixed(2)}}</td>
          <td class="num mono">${{dSign}}${{diff.toFixed(2)}}</td>
        `;
        stBody.appendChild(tr);
      }});
    }}

    document.querySelectorAll("#standings-table th[data-sort]").forEach(th => {{
      th.addEventListener("click", () => {{
        const key = th.dataset.sort;
        if (sortKey === key) sortAsc = !sortAsc;
        else {{
          sortKey = key;
          sortAsc = (key === "seed" || key === "name" || key === "pa");
        }}
        renderStandingsTable();
      }});
    }});

    document.getElementById("btn-theme").addEventListener("click", () => {{
      const root = document.documentElement;
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      document.getElementById("btn-theme").textContent = next === "dark" ? "Daylight Menu (Light)" : "Final Destination (Dark)";
    }});

    document.getElementById("btn-copy-link").addEventListener("click", () => {{
      const url = canonicalIssueUrl(currentIssue);
      let teaser = "SUPER SMASH ALLIANCE 10.0 — Midseason Smash Roast (8 of you trapped in 8-Player Sudden Death at 4-3, and Bad Mother Tucker's 262% Damage K.O.): " + url;
      if (currentIssue.startsWith("week-")) {{
        const wk = LEAGUE_DATA.weeks[currentIssue.replace("week-", "")];
        if (wk) teaser = wk.teaser + " " + url;
      }}
      copyText(teaser, "Smash Roast link copied for group chat!");
    }});

    buildEditionTabs();
    renderParityTiers();
    renderStandingsTable();
    renderTeamFilters();
    renderRoastCards();
    renderUpcoming();

    const params = new URLSearchParams(window.location.search);
    const urlIssue = params.get("issue");
    const urlTeam = params.get("team");
    if (urlIssue && (urlIssue === "midseason" || urlIssue.startsWith("week-"))) {{
      selectIssue(urlIssue, false);
    }} else {{
      selectIssue(DEFAULT_ISSUE, false);
    }}
    if (urlTeam) {{
      const tid = Number(urlTeam);
      if (!Number.isNaN(tid) && TEAMS_BY_ID[tid]) setTimeout(() => focusTeamRoast(tid), 150);
    }}
  </script>
</body>
</html>
"""
    validator = TagValidator()
    validator.feed(page)
    if validator.stack:
        raise ValueError(f"Unclosed HTML tags remaining: {validator.stack}")
    return page


def sync_smash_artwork(out_dir):
    assets_dir = os.path.join(out_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    pairs = [
        (os.path.join(ARTIFACT_DIR, "smash_arena_hero_1793140054669.jpg"), os.path.join(assets_dir, "smash-arena-hero.jpg")),
        (os.path.join(ARTIFACT_DIR, "smash_bmt_trophy_1793140070095.jpg"), os.path.join(assets_dir, "smash-bmt-trophy.jpg")),
    ]
    for src, dst in pairs:
        if os.path.exists(src) and os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)


def build_all(out_dir=SITE_OUT_DIR, fetch_live=False, default_issue=None):
    os.makedirs(out_dir, exist_ok=True)
    sync_smash_artwork(out_dir)
    data = load_espn_data(out_dir=out_dir, fetch_live=fetch_live)
    model = compute_league_model(data)

    # Default root issue: Midseason Roast while through Week 7; auto-advance to latest completed week starting Week 8+
    root_issue = default_issue or (
        "midseason" if model["completedWeeks"] <= 7 else f"week-{model['completedWeeks']}"
    )

    root_html = render_html_page(model, default_issue=root_issue, base_prefix="./", is_root=True)
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(root_html)

    # Add .nojekyll and .gitignore for fast, clean GitHub Pages hosting
    with open(os.path.join(out_dir, ".nojekyll"), "w") as f:
        f.write("")
    with open(os.path.join(out_dir, ".gitignore"), "w") as f:
        f.write("__pycache__/\n.DS_Store\n*.pyc\n")

    # Add automated weekly Tuesday morning GitHub Actions workflow (+ one-click manual trigger)
    wf_dir = os.path.join(out_dir, ".github", "workflows")
    os.makedirs(wf_dir, exist_ok=True)
    workflow_yml = """name: Weekly ESPN Recap Sync

on:
  schedule:
    # Runs every Tuesday at 13:15 UTC (9:15 AM EDT / 8:15 AM EST) after MNF stats finalize
    - cron: "15 13 * * 2"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update-recaps:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Fetch latest ESPN League 1000567 scores & rebuild static editions
        run: python3 build_alliance_site.py --fetch

      - name: Commit and push updated recap editions
        run: |
          git config user.name "Alliance Dispatch Bot"
          git config user.email "briskman-j@users.noreply.github.com"
          git add -A
          if git diff --cached --quiet; then
            echo "No new completed week changes detected."
          else
            git commit -m "Auto-publish latest ESPN weekly recap edition"
            git push
          fi
"""
    with open(os.path.join(wf_dir, "weekly-espn-sync.yml"), "w") as f:
        f.write(workflow_yml)

    editions = ["midseason"] + [f"week-{w}" for w in range(1, model["completedWeeks"] + 1)]
    for ed in editions:
        ed_dir = os.path.join(out_dir, "recaps", ed)
        os.makedirs(ed_dir, exist_ok=True)
        page_html = render_html_page(model, default_issue=ed, base_prefix="../../", is_root=False)
        with open(os.path.join(ed_dir, "index.html"), "w") as f:
            f.write(page_html)

    dst_script = os.path.join(out_dir, "build_alliance_site.py")
    if os.path.abspath(__file__) != os.path.abspath(dst_script):
        shutil.copyfile(__file__, dst_script)

    readme = """# The Alliance Dispatch — Super Smash Alliance 10.0 (`SSA-2026`)

Official static sports broadsheet & roast archive for **The Super Smash Alliance 10.0** (ESPN League `1000567`).

**Live Site:** https://briskman-j.github.io/SSA-2026/

## Shareable Per-Edition Group-Chat Links
Every edition has its own dedicated URL and custom OpenGraph iMessage / WhatsApp preview card:
- **Midseason State of the Alliance Roast (Weeks 1–7):** https://briskman-j.github.io/SSA-2026/recaps/midseason/
- **Week 7 Recap:** https://briskman-j.github.io/SSA-2026/recaps/week-7/
- **Weeks 1–6 Archive:** `/recaps/week-1/` through `/recaps/week-6/`
- **Direct Friend Roast Deep-Link:** append `?team=<TEAM_ID>` (e.g. `https://briskman-j.github.io/SSA-2026/recaps/midseason/?team=1` for Kyle Feeney)

## Automated & Manual Weekly Updates
1. **Zero-Touch GitHub Action (Every Tuesday Morning):**
   `.github/workflows/weekly-espn-sync.yml` runs automatically every Tuesday at 9:15 AM ET (or on-demand via **Actions → Weekly ESPN Recap Sync → Run workflow**) to pull live ESPN scores and publish `/recaps/week-8/`, `/recaps/week-9/`, etc.
2. **Local CLI Update (with Custom Weekly Roast Headlines):**
   Edit `WEEKLY_EDITORIALS` or `TEAM_ROASTS` in `build_alliance_site.py`, then run:
   ```bash
   python3 build_alliance_site.py --fetch
   git add -A && git commit -m "Publish weekly roast" && git push
   ```
"""
    with open(os.path.join(out_dir, "README.md"), "w") as f:
        f.write(readme)

    if os.path.exists(SCRATCH_DIR):
        zip_path = os.path.join(SCRATCH_DIR, "super-smash-alliance-site.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for folder, dirs, files in os.walk(out_dir):
                dirs[:] = [d for d in dirs if d != ".git"]
                for fn in files:
                    full_p = os.path.join(folder, fn)
                    rel_p = os.path.relpath(full_p, out_dir)
                    zf.write(full_p, rel_p)
        print(f"Built zip bundle:  {zip_path}")

    print(f"Validated HTML tags cleanly! Root HTML size: {len(root_html):,} bytes")
    print(f"Built site folder: {out_dir}")
    print(f"Editions ({len(editions)}): {', '.join(editions)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Fetch latest live JSON from ESPN API")
    parser.add_argument("--out-dir", default=SITE_OUT_DIR, help="Output directory for generated static site")
    parser.add_argument("--default-issue", default=None, help="Override featured default issue on root index.html")
    args = parser.parse_args()
    build_all(out_dir=args.out_dir, fetch_live=args.fetch, default_issue=args.default_issue)
