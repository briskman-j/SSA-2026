#!/usr/bin/env python3
"""Static site generator for The Alliance Dispatch (Super Smash Alliance 10.0).

Builds:
  - index.html (Newsstand & Featured Latest Issue)
  - recaps/midseason/index.html (Midseason State of the Alliance Roast + 15-Year Franchise History Chart)
  - recaps/week-1/index.html .. recaps/week-7/index.html (Per-week archive with custom OpenGraph cards)
  - data/league_history.json (2012–2026 franchise team names & championships archive)
  - super-smash-alliance-site.zip (Portable static site bundle)
"""

import argparse
from collections import defaultdict
import copy
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

# Verified 15-Season Franchise History (2012–2026): Team Names & Championships
BASE_LEAGUE_HISTORY = {
    "yearsSpan": "2012–2026",
    "totalSeasons": 15,
    "completedChampionships": 14,
    "franchises": [
        {
            "key": "Dylan",
            "tid": 4,
            "manager": "D B (feeneysucksthebigone)",
            "shortManager": "D B",
            "currentTeam": "The Absolute Creamers",
            "active": True,
            "seasons": 15,
            "nameCount": 12,
            "championships": 0,
            "champYears": [],
            "names": [
                {"name": "Team Sharkey's Better", "years": "2012", "champYears": []},
                {"name": "Team Not a Single Hoot", "years": "2013", "champYears": []},
                {"name": "I am Hoot", "years": "2014", "champYears": []},
                {"name": "Feeney's Last Slice", "years": "2015", "champYears": []},
                {"name": "Dude, Where's My Carr", "years": "2016", "champYears": []},
                {"name": "The Lone Ranger", "years": "2017", "champYears": []},
                {"name": "Half Chubb", "years": "2018", "champYears": []},
                {"name": "2 RBs 1 Kupp", "years": "2019", "champYears": []},
                {"name": "Team Burke", "years": "2020", "champYears": []},
                {"name": "Suck My McmAnus", "years": "2021", "champYears": []},
                {"name": "Chark Week", "years": "2022–23", "champYears": []},
                {"name": "The Absolute Creamers", "years": "2024–26", "champYears": []},
            ],
            "blurb": "12 distinct identities in 15 seasons—rebranding almost every August like a man fleeing creditors—for zero rings.",
        },
        {
            "key": "Brisk",
            "tid": 2,
            "manager": "Josh Briskman",
            "shortManager": "Josh Briskman",
            "currentTeam": "Bad Mother Tucker's",
            "active": True,
            "seasons": 15,
            "nameCount": 9,
            "championships": 4,
            "champYears": [2015, 2017, 2020, 2021],
            "names": [
                {"name": "The WINDOW SMASHERS", "years": "2012", "champYears": []},
                {"name": "Los Locos Torsos", "years": "2013–14", "champYears": []},
                {"name": "man brisk", "years": "2015", "champYears": [2015]},
                {"name": "Team Briskman", "years": "2016–18", "champYears": [2017]},
                {"name": "Don't call the KITTLE Black", "years": "2019", "champYears": []},
                {"name": "One Bad Motha Tucker", "years": "2020", "champYears": [2020]},
                {"name": "Koo Young Hoes", "years": "2021", "champYears": [2021]},
                {"name": "Kick Some b A S S", "years": "2022–23", "champYears": []},
                {"name": "Bad Mother Tucker's", "years": "2024–26", "champYears": []},
            ],
            "blurb": "All-time leader with 4 rings (including back-to-back in 2020–21), which only makes this year's 1-6 Tanner McKee collapse funnier.",
        },
        {
            "key": "Feeney",
            "tid": 1,
            "manager": "Kyle Feeney",
            "shortManager": "Kyle Feeney",
            "currentTeam": "Charlie Kirks Angels",
            "active": True,
            "seasons": 15,
            "nameCount": 8,
            "championships": 1,
            "champYears": [2018],
            "names": [
                {"name": "I Shaved My Balls For This?", "years": "2012", "champYears": []},
                {"name": "The Shaggin Flagon Wagon", "years": "2013", "champYears": []},
                {"name": "Rey Mysterio Love Loads", "years": "2014", "champYears": []},
                {"name": "#mycalvins Johnson", "years": "2015–17", "champYears": []},
                {"name": "Chief Keefs", "years": "2018", "champYears": [2018]},
                {"name": "Chubb(s) Peterson", "years": "2019", "champYears": []},
                {"name": "Fully Chubb'd", "years": "2020–25", "champYears": []},
                {"name": "Charlie Kirks Angels", "years": "2026", "champYears": []},
            ],
            "blurb": "8 career team names—meaning Kyle has changed his team name 8x more often than he has touched the 2026 waiver wire (1 move).",
        },
        {
            "key": "Billy",
            "tid": 13,
            "manager": "Billy Mattimore",
            "shortManager": "Billy Mattimore",
            "currentTeam": "Schmatti schmatti",
            "active": True,
            "seasons": 15,
            "nameCount": 7,
            "championships": 1,
            "champYears": [2019],
            "names": [
                {"name": "team sacco", "years": "2012", "champYears": []},
                {"name": "team Hodor", "years": "2013", "champYears": []},
                {"name": "Aldon's Legal Team", "years": "2014", "champYears": []},
                {"name": "Hodor's Revenge", "years": "2015", "champYears": []},
                {"name": "Team Mattimore", "years": "2016–17", "champYears": []},
                {"name": "Salty Balti", "years": "2018", "champYears": []},
                {"name": "Schmatti schmatti", "years": "2019–26", "champYears": [2019]},
            ],
            "blurb": "Burned through 6 names from 2012–18 with zero titles, landed on 'Schmatti schmatti' in 2019, immediately won a ring, and never changed it again.",
        },
        {
            "key": "Chase",
            "tid": 5,
            "manager": "Chase Bailey",
            "shortManager": "Chase Bailey",
            "currentTeam": "#FedOut",
            "active": True,
            "seasons": 15,
            "nameCount": 6,
            "championships": 1,
            "champYears": [2023],
            "names": [
                {"name": "Demarcus Ware Da Trees At", "years": "2012–14", "champYears": []},
                {"name": "Lovie Loads Smith", "years": "2015", "champYears": []},
                {"name": "Team Bailey", "years": "2016–17", "champYears": []},
                {"name": "Trashville Predators", "years": "2018–19", "champYears": []},
                {"name": "Jan Levinson- Robbie-Gould", "years": "2020–25", "champYears": [2023]},
                {"name": "#FedOut", "years": "2026", "champYears": []},
            ],
            "blurb": "Broke a 12-year title drought as 'Jan Levinson- Robbie-Gould' in 2023 before pivoting to '#FedOut' for his 27-move waiver cardio tour.",
        },
        {
            "key": "Owen",
            "tid": 18,
            "manager": "Owen Bennett",
            "shortManager": "Owen Bennett",
            "currentTeam": "Ottawa Redblacks",
            "active": True,
            "seasons": 10,
            "nameCount": 6,
            "championships": 1,
            "champYears": [2013],
            "names": [
                {"name": "The Window Fixers", "years": "2012", "champYears": []},
                {"name": "The Great Canadian Hope", "years": "2013–14", "champYears": [2013]},
                {"name": "Mahomes Harry Butker", "years": "2020", "champYears": []},
                {"name": "Dillon Dillon Dillon Dillon", "years": "2021–23", "champYears": []},
                {"name": "Two Henrys", "years": "2024", "champYears": []},
                {"name": "Ottawa Redblacks", "years": "2025–26", "champYears": []},
            ],
            "blurb": "6 team names across 10 seasons; lone title ('The Great Canadian Hope', 2013) came during Year 1 of Obama's second term.",
        },
        {
            "key": "RJ",
            "tid": 12,
            "manager": "Ronjohn Dadd",
            "shortManager": "Ronjohn Dadd",
            "currentTeam": "Tua Hands Dadd",
            "active": True,
            "seasons": 15,
            "nameCount": 6,
            "championships": 0,
            "champYears": [],
            "names": [
                {"name": "Dipping Beneath Lasers", "years": "2012", "champYears": []},
                {"name": "Mayor of Titty City", "years": "2013–14", "champYears": []},
                {"name": "Stuck it in her Cooper", "years": "2015–18", "champYears": []},
                {"name": "Where's my Juulio bro?", "years": "2019", "champYears": []},
                {"name": "The Jerry Jeudy Show", "years": "2020–25", "champYears": []},
                {"name": "Tua Hands Dadd", "years": "2026", "champYears": []},
            ],
            "blurb": "15 seasons, 6 rebrands (from 'Mayor of Titty City' to 'The Jerry Jeudy Show'), 0 rings—now sitting 6-1 trying to end a 15-year drought.",
        },
        {
            "key": "RyRy",
            "tid": 17,
            "manager": "Ryan Gutowski",
            "shortManager": "Ryan Gutowski",
            "currentTeam": "Fat Shamed FOGO",
            "active": True,
            "seasons": 14,
            "nameCount": 3,
            "championships": 1,
            "champYears": [2025],
            "names": [
                {"name": "The StUpId NeMa'S", "years": "2012–14", "champYears": []},
                {"name": "Team Gutowski", "years": "2016–18", "champYears": []},
                {"name": "Fat Shamed FOGO", "years": "2019–26", "champYears": [2025]},
            ],
            "blurb": "Reigning champ: kept 'Fat Shamed FOGO' through 8 straight winters (including a 2-12 tank in 2023) until it finally cashed the 2025 title.",
        },
        {
            "key": "O'Keefe",
            "tid": 3,
            "manager": "Kyle O'Keefe",
            "shortManager": "Kyle O'Keefe",
            "currentTeam": "Team O'Keefe",
            "active": True,
            "seasons": 15,
            "nameCount": 2,
            "championships": 2,
            "champYears": [2012, 2024],
            "names": [
                {"name": "Team Wills Sucks", "years": "2012–15", "champYears": [2012]},
                {"name": "Team O'Keefe", "years": "2016–26", "champYears": [2024]},
            ],
            "blurb": "1.00 rings-per-name efficiency: won the inaugural 2012 title out of spite ('Team Wills Sucks'), went default 'Team O'Keefe' in 2016, and won again in 2024.",
        },
        {
            "key": "Wills",
            "tid": 15,
            "manager": "Wills Miller",
            "shortManager": "Wills Miller",
            "currentTeam": "Team Miller",
            "active": True,
            "seasons": 15,
            "nameCount": 2,
            "championships": 0,
            "champYears": [],
            "names": [
                {"name": "Team kylelovesmolly", "years": "2012–15", "champYears": []},
                {"name": "Team Miller", "years": "2016–26", "champYears": []},
            ],
            "blurb": "Traded spite names with O'Keefe from 2012–15, parked on default 'Team Miller' for 11 straight years, and still has 0 rings despite leading 2026 in scoring.",
        },
        {
            "key": "Jackson",
            "tid": 19,
            "manager": "Jackson Place",
            "shortManager": "Jackson Place",
            "currentTeam": "Team Place",
            "active": True,
            "seasons": 7,
            "nameCount": 1,
            "championships": 1,
            "champYears": [2022],
            "names": [
                {"name": "Team Place", "years": "2020–26", "champYears": [2022]},
            ],
            "blurb": "Has never once clicked 'Edit Team Name' in 7 seasons ('Team Place') and still won a ring (2022) before D B, Ronjohn, Wills, or Huffner.",
        },
        {
            "key": "Huffner",
            "tid": 20,
            "manager": "Michael Huffner",
            "shortManager": "Michael Huffner",
            "currentTeam": "Team Huffner",
            "active": True,
            "seasons": 7,
            "nameCount": 1,
            "championships": 0,
            "champYears": [],
            "names": [
                {"name": "Team Huffner", "years": "2012–14, 2023–26", "champYears": []},
            ],
            "blurb": "Rocking untouched ESPN auto-fill 'Team Huffner' since 2012: 1 default name, 2 waiver moves this year, 0 championships.",
        },
        {
            "key": "Sharkey",
            "tid": None,
            "manager": "Matthew Sharkey",
            "shortManager": "Matthew Sharkey",
            "currentTeam": "Ha-Ha Clinton Hates Dix",
            "active": False,
            "seasons": 4,
            "nameCount": 4,
            "championships": 2,
            "champYears": [2014, 2016],
            "names": [
                {"name": "Sit On My Face Book", "years": "2012", "champYears": []},
                {"name": "Suck My Unit", "years": "2013", "champYears": []},
                {"name": "Winter is Cumming", "years": "2014", "champYears": [2014]},
                {"name": "Ha-Ha Clinton Hates Dix", "years": "2016", "champYears": [2016]},
            ],
            "blurb": "Retired legend: played 4 seasons (2012–14, 2016), dropped 4 unhinged names, stole 2 rings (tied for #2 all-time), and rode off into the sunset.",
        },
        {
            "key": "Fuentes",
            "tid": None,
            "manager": "Michael Fuentes",
            "shortManager": "Michael Fuentes",
            "currentTeam": "Team Babs",
            "active": False,
            "seasons": 10,
            "nameCount": 6,
            "championships": 0,
            "champYears": [],
            "names": [
                {"name": "The Fat Chewin Cows", "years": "2012–14", "champYears": []},
                {"name": "We Wilfork You", "years": "2015", "champYears": []},
                {"name": "Team Fuentes", "years": "2016–18", "champYears": []},
                {"name": "Ferrigno Feelers", "years": "2019", "champYears": []},
                {"name": "NEW YORK BLUES", "years": "2020", "champYears": []},
                {"name": "Team Babs", "years": "2021", "champYears": []},
            ],
            "blurb": "Retired alumni (2012–21): 10 seasons, 6 team names, 2015 runner-up, 0 championships.",
        },
        {
            "key": "TBO",
            "tid": None,
            "manager": "Thomas Thibeault",
            "shortManager": "Thomas Thibeault",
            "currentTeam": "Team Thibeault",
            "active": False,
            "seasons": 5,
            "nameCount": 1,
            "championships": 0,
            "champYears": [],
            "names": [
                {"name": "Team Thibeault", "years": "2012–16", "champYears": []},
            ],
            "blurb": "Retired alumni (2012–16): 5 seasons of default 'Team Thibeault', 0 playoff appearances, 0 rings.",
        },
        {
            "key": "Richard",
            "tid": None,
            "manager": "Harte Thompson",
            "shortManager": "Harte Thompson",
            "currentTeam": "Phillymore HTEC",
            "active": False,
            "seasons": 1,
            "nameCount": 1,
            "championships": 0,
            "champYears": [],
            "names": [
                {"name": "Phillymore HTEC", "years": "2022", "champYears": []},
            ],
            "blurb": "One-season cameo (2022): went 7-8 as 'Phillymore HTEC' and retired undefeated in retirement.",
        },
    ],
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


def build_franchise_history(teams_by_id):
    history = copy.deepcopy(BASE_LEAGUE_HISTORY)
    for fr in history["franchises"]:
        tid = fr.get("tid")
        if tid and tid in teams_by_id:
            live_name = " ".join(teams_by_id[tid]["name"].split())
            if live_name:
                fr["currentTeam"] = live_name
                known_lower = {item["name"].lower() for item in fr["names"]}
                if live_name.lower() not in known_lower:
                    fr["names"].append({"name": live_name, "years": str(SEASON_ID), "champYears": []})
                    fr["nameCount"] = len(fr["names"])
    return history


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

    history_model = build_franchise_history(teams)

    return {
        "leagueName": data.get("settings", {}).get("name", "The Super Smash Alliance 10.0"),
        "leagueId": LEAGUE_ID,
        "completedWeeks": completed_weeks,
        "upcomingWeek": current_mp,
        "teams": sorted_teams,
        "weeks": weeks_summary,
        "upcoming": upcoming_cards,
        "history": history_model,
    }


def render_html_page(model, default_issue="midseason", base_prefix="./", is_root=False):
    if default_issue == "midseason":
        og_title = "The Alliance Dispatch — Midseason Roast: 8 Teams in a Phone Booth & Bad Mother Tucker's Funeral"
        og_desc = (
            "Official Midseason State of The Super Smash Alliance 10.0: 6 teams deadlocked at 4-3, "
            "8 of 12 within 1 game, 15-year team names vs. championships chart, and 1-6 Bad Mother Tucker's autopsy."
        )
    else:
        wk_num = default_issue.replace("week-", "")
        wk_obj = model["weeks"].get(wk_num, {})
        og_title = f"The Alliance Dispatch — Week {wk_num}: {wk_obj.get('headline', 'Weekly Roast')}"
        og_desc = wk_obj.get("subhead", "Official Weekly Recap & Standings for The Super Smash Alliance 10.0.")

    canonical_url = PUBLIC_SITE_URL if is_root else f"{PUBLIC_SITE_URL}recaps/{default_issue}/"
    og_image_url = f"{PUBLIC_SITE_URL}assets/smash-arena-hero.jpg"
    hero_img_src = f"{base_prefix}assets/smash-arena-hero.jpg"
    trophy_img_src = f"{base_prefix}assets/smash-bmt-trophy.jpg"
    favicon_svg = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
        "%3Cdefs%3E%3Cmask id='m'%3E%3Ccircle cx='50' cy='50' r='46' fill='white'/%3E"
        "%3Crect x='25' y='0' width='15' height='100' fill='black'/%3E"
        "%3Crect x='0' y='60' width='100' height='10' fill='black'/%3E%3C/mask%3E%3C/defs%3E"
        "%3Ccircle cx='50' cy='50' r='48' fill='%2316191D'/%3E"
        "%3Ccircle cx='50' cy='50' r='42' fill='%23C81E1E' mask='url(%23m)'/%3E%3C/svg%3E"
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
  <style>
    :root, [data-theme="light"] {{
      --bg: #F6F4EE;
      --bg-alt: #EDEAE0;
      --card: #FFFFFF;
      --ink: #16191D;
      --ink-secondary: #485058;
      --ink-muted: #6C737B;
      --rule: #DCD7C9;
      --rule-strong: #16191D;
      --crimson: #B91C1C;
      --crimson-bg: #FEF2F2;
      --crimson-border: #FECACA;
      --emerald: #0F766E;
      --emerald-bg: #F0FDFA;
      --emerald-border: #99F6E4;
      --amber: #B45309;
      --amber-bg: #FFFBEB;
      --amber-border: #FDE68A;
      --navy-bar: #335C81;
      --navy-bg: #EFF4F9;
      --gold-bar: #D97706;
      --gold-bg: #FEF7E6;
      --gold-border: #F6D28B;
      --slate-bg: #F1EFE8;
      --shadow: 0 1px 3px rgba(20, 23, 26, 0.06);
    }}
    [data-theme="dark"] {{
      --bg: #13161B;
      --bg-alt: #1A1E25;
      --card: #20252E;
      --ink: #F1EFEA;
      --ink-secondary: #C3C8D1;
      --ink-muted: #8D95A2;
      --rule: #2F3643;
      --rule-strong: #E6E3DA;
      --crimson: #F87171;
      --crimson-bg: rgba(185, 28, 28, 0.17);
      --crimson-border: rgba(248, 113, 113, 0.35);
      --emerald: #2DD4BF;
      --emerald-bg: rgba(15, 118, 110, 0.2);
      --emerald-border: rgba(45, 212, 191, 0.35);
      --amber: #FBBF24;
      --amber-bg: rgba(180, 83, 9, 0.2);
      --amber-border: rgba(251, 191, 36, 0.35);
      --navy-bar: #5B8FD9;
      --navy-bg: rgba(91, 143, 217, 0.15);
      --gold-bar: #F59E0B;
      --gold-bg: rgba(245, 158, 11, 0.16);
      --gold-border: rgba(245, 158, 11, 0.4);
      --slate-bg: #272D38;
      --shadow: 0 2px 6px rgba(0, 0, 0, 0.32);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
      font-size: 15px;
      line-height: 1.58;
      -webkit-font-smoothing: antialiased;
      padding-bottom: 68px;
    }}
    .mono {{
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-variant-numeric: tabular-nums;
    }}
    .serif {{ font-family: Georgia, Charter, "Iowan Old Style", "Palatino Linotype", serif; }}
    .container {{ max-width: 1120px; margin: 0 auto; padding: 0 18px; }}

    /* Clean Broadsheet Masthead + Framed Smash Arena Illustration */
    .masthead {{ border-bottom: 3px double var(--rule-strong); padding: 14px 0 16px; background: var(--bg); }}
    .masthead-top {{
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
      padding-bottom: 10px; border-bottom: 1px solid var(--rule);
      font-size: 12px; color: var(--ink-muted); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;
    }}
    .masthead-actions {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .btn {{
      appearance: none; border: 1px solid var(--rule); background: var(--card); color: var(--ink);
      font-size: 12.5px; font-weight: 600; padding: 6px 12px; border-radius: 6px; cursor: pointer;
      transition: background 0.15s ease, border-color 0.15s ease;
      display: inline-flex; align-items: center; gap: 6px; text-decoration: none;
    }}
    .btn:hover {{ background: var(--bg-alt); border-color: var(--ink-muted); }}
    .btn-primary {{ background: var(--ink); color: var(--bg); border-color: var(--ink); }}
    .btn-primary:hover {{ opacity: 0.9; background: var(--ink); }}

    .brand-row {{
      display: flex; flex-direction: column; align-items: center; text-align: center;
      padding: 16px 0 12px;
    }}
    .brand-heading {{
      display: inline-flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap;
    }}
    .brand-crest {{ width: 34px; height: 34px; flex-shrink: 0; }}
    .brand-title {{ font-size: clamp(28px, 4.8vw, 44px); font-weight: 700; letter-spacing: -0.025em; line-height: 1.08; }}
    .brand-sub {{ margin-top: 6px; font-size: 13.5px; color: var(--ink-secondary); }}

    .artwork-banner {{
      position: relative;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid var(--rule);
      box-shadow: var(--shadow);
      height: 205px;
      background: #141821;
    }}
    @media (max-width: 640px) {{ .artwork-banner {{ height: 155px; }} }}
    .artwork-banner img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 40%;
      display: block;
    }}
    .artwork-caption {{
      position: absolute;
      left: 0; right: 0; bottom: 0;
      padding: 24px 16px 10px;
      background: linear-gradient(0deg, rgba(16, 18, 23, 0.86) 0%, rgba(16, 18, 23, 0.0) 100%);
      color: #F4F2EC;
      font-size: 12.5px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}

    /* Calm Horizontal Edition Switcher */
    .edition-bar {{ background: var(--bg-alt); border-bottom: 1px solid var(--rule); position: sticky; top: 0; z-index: 30; }}
    .edition-inner {{ display: flex; align-items: center; gap: 6px; overflow-x: auto; padding: 10px 0; }}
    .edition-label {{ font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--ink-muted); margin-right: 4px; white-space: nowrap; }}
    .edition-tab {{
      appearance: none; border: 1px solid var(--rule); background: var(--card); color: var(--ink-secondary);
      font-size: 12.5px; font-weight: 600; padding: 6px 12px; border-radius: 5px; cursor: pointer; white-space: nowrap;
    }}
    .edition-tab:hover {{ color: var(--ink); background: var(--bg); }}
    .edition-tab.active {{ background: var(--crimson); color: #FFFFFF; border-color: var(--crimson); }}

    /* Editorial Lead Story */
    .hero {{ padding: 26px 0 22px; border-bottom: 1px solid var(--rule); }}
    .kicker {{ font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: var(--crimson); margin-bottom: 8px; }}
    .hero h1 {{ font-size: clamp(25px, 3.9vw, 39px); line-height: 1.15; letter-spacing: -0.02em; font-weight: 700; max-width: 920px; }}
    .hero-lede {{ margin-top: 12px; font-size: 16.5px; line-height: 1.58; color: var(--ink-secondary); max-width: 880px; }}
    .byline {{ margin-top: 14px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; font-size: 13px; color: var(--ink-muted); }}

    /* 4 Key Stat Cards */
    .stat-strip {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 22px 0; }}
    .stat-box {{ background: var(--card); border: 1px solid var(--rule); border-radius: 8px; padding: 16px; box-shadow: var(--shadow); }}
    .stat-box-label {{ font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-muted); }}
    .stat-box-val {{ font-size: 23px; font-weight: 700; margin-top: 4px; letter-spacing: -0.02em; }}
    .stat-box-note {{ font-size: 13px; color: var(--ink-secondary); margin-top: 4px; line-height: 1.45; }}

    /* Section Dividers */
    .section {{ margin-top: 36px; }}
    .section-header {{
      display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 10px;
      padding-bottom: 9px; border-bottom: 2px solid var(--rule-strong); margin-bottom: 16px;
    }}
    .section-title {{ font-size: 22px; font-weight: 700; letter-spacing: -0.015em; }}
    .section-sub {{ font-size: 13px; color: var(--ink-muted); }}

    /* Parity Tiers */
    .parity-panel {{ background: var(--card); border: 1px solid var(--rule); border-radius: 8px; padding: 18px; box-shadow: var(--shadow); }}
    .parity-tiers {{ display: grid; grid-template-columns: 1fr; gap: 10px; margin-top: 14px; }}
    .tier-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 12px 14px; border-radius: 6px; border: 1px solid var(--rule); background: var(--bg); }}
    .tier-row.highlight-parity {{ background: var(--amber-bg); border-color: var(--amber-border); }}
    .tier-row.highlight-morgue {{ background: var(--crimson-bg); border-color: var(--crimson-border); }}
    .tier-tag {{ font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; min-width: 230px; }}
    .tier-chips {{ display: flex; flex-wrap: wrap; gap: 6px; flex: 1; }}
    .team-chip {{ font-size: 12.5px; font-weight: 600; padding: 5px 10px; border-radius: 5px; background: var(--card); border: 1px solid var(--rule); color: var(--ink); cursor: pointer; }}
    .team-chip:hover {{ border-color: var(--ink); background: var(--bg-alt); }}

    /* Bad Mother Tucker's Autopsy + Trophy Photo */
    .autopsy-card {{ background: var(--crimson-bg); border: 1px solid var(--crimson-border); border-radius: 8px; padding: 22px; box-shadow: var(--shadow); }}
    .autopsy-grid {{ display: grid; grid-template-columns: 210px 1.25fr 1fr; gap: 20px; margin-top: 14px; align-items: start; }}
    @media (max-width: 940px) {{ .autopsy-grid {{ grid-template-columns: 1fr; }} }}
    .trophy-figure {{
      background: var(--card);
      border: 1px solid var(--rule);
      border-radius: 8px;
      padding: 8px;
      box-shadow: var(--shadow);
      max-width: 260px;
    }}
    .trophy-figure img {{
      width: 100%;
      aspect-ratio: 1 / 1;
      object-fit: cover;
      border-radius: 5px;
      display: block;
    }}
    .trophy-figcaption {{
      margin-top: 7px;
      font-size: 11.5px;
      line-height: 1.4;
      color: var(--ink-muted);
      text-align: center;
    }}
    .autopsy-list {{ list-style: none; display: flex; flex-direction: column; gap: 10px; }}
    .autopsy-list li {{ font-size: 14.5px; line-height: 1.55; }}
    .crime-box {{ background: var(--card); border: 1px solid var(--rule); border-radius: 6px; padding: 15px; }}
    .crime-row {{ display: flex; justify-content: space-between; gap: 8px; padding: 7px 0; border-bottom: 1px solid var(--rule); font-size: 13px; }}
    .crime-row:last-child {{ border-bottom: none; }}

    /* NEW: 15-Year Historical Chart (Team Names vs. Championships) */
    .history-panel {{
      background: var(--card);
      border: 1px solid var(--rule);
      border-radius: 8px;
      padding: 20px;
      box-shadow: var(--shadow);
    }}
    .history-callouts {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .history-callout {{
      background: var(--bg);
      border: 1px solid var(--rule);
      border-radius: 7px;
      padding: 13px 15px;
    }}
    .hc-kicker {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-muted); }}
    .hc-val {{ font-size: 17px; font-weight: 700; margin-top: 3px; color: var(--ink); }}
    .hc-note {{ font-size: 12.5px; color: var(--ink-secondary); margin-top: 3px; line-height: 1.45; }}

    .history-toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--rule);
      margin-bottom: 14px;
    }}
    .history-controls {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }}
    .history-legend {{ display: flex; flex-wrap: wrap; gap: 16px; align-items: center; font-size: 12.5px; font-weight: 600; color: var(--ink-secondary); }}
    .legend-item {{ display: inline-flex; align-items: center; gap: 7px; }}
    .legend-swatch {{ width: 13px; height: 13px; border-radius: 3px; display: inline-block; }}
    .swatch-names {{ background: var(--navy-bar); }}
    .swatch-rings {{ background: var(--gold-bar); }}

    .history-scale-head {{
      display: grid;
      grid-template-columns: 235px 1fr 125px;
      gap: 16px;
      padding: 0 12px 6px;
      font-size: 11.5px;
      color: var(--ink-muted);
      font-weight: 600;
    }}
    .scale-ticks {{
      display: flex;
      justify-content: space-between;
      border-bottom: 1px dashed var(--rule);
      padding-bottom: 4px;
    }}
    @media (max-width: 780px) {{
      .history-scale-head {{ display: none; }}
    }}

    .history-rows {{ display: flex; flex-direction: column; gap: 8px; }}
    .history-row {{
      border: 1px solid var(--rule);
      border-radius: 7px;
      background: var(--bg);
      padding: 11px 13px;
      transition: background 0.14s ease, border-color 0.14s ease;
      cursor: pointer;
    }}
    .history-row:hover {{ border-color: var(--ink-muted); }}
    .history-row.is-alumni {{ opacity: 0.86; border-style: dashed; }}
    .history-row-main {{
      display: grid;
      grid-template-columns: 235px 1fr 125px;
      gap: 16px;
      align-items: center;
    }}
    @media (max-width: 780px) {{
      .history-row-main {{ grid-template-columns: 1fr; gap: 9px; }}
    }}
    .hr-who {{ min-width: 0; }}
    .hr-mgr {{ font-weight: 700; font-size: 14.5px; color: var(--ink); display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }}
    .hr-alumni-tag {{
      font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
      padding: 1px 6px; border-radius: 4px; background: var(--bg-alt); color: var(--ink-muted); border: 1px solid var(--rule);
    }}
    .hr-cur {{ font-size: 12.5px; color: var(--ink-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

    .hr-bars {{ display: flex; flex-direction: column; gap: 6px; }}
    .bar-line {{ display: flex; align-items: center; gap: 9px; }}
    .bar-track {{
      flex: 1;
      height: 18px;
      background: var(--card);
      border: 1px solid var(--rule);
      border-radius: 4px;
      overflow: hidden;
      position: relative;
    }}
    .bar-fill {{ height: 100%; border-radius: 3px 0 0 3px; transition: width 0.25s ease; }}
    .bar-fill.names {{ background: var(--navy-bar); }}
    .bar-fill.rings {{ background: var(--gold-bar); }}
    .bar-stat {{
      min-width: 145px;
      font-size: 12.5px;
      font-weight: 600;
      color: var(--ink-secondary);
      white-space: nowrap;
    }}
    @media (max-width: 520px) {{
      .bar-stat {{ min-width: 118px; font-size: 12px; }}
    }}
    .bar-stat.has-rings {{ color: var(--amber); font-weight: 700; }}
    .bar-stat.zero-rings {{ color: var(--ink-muted); font-weight: 500; }}

    .hr-toggle {{
      text-align: right;
      font-size: 12px;
      font-weight: 600;
      color: var(--ink-muted);
      user-select: none;
    }}
    @media (max-width: 780px) {{ .hr-toggle {{ text-align: left; }} }}

    .history-drawer {{
      margin-top: 11px;
      padding-top: 11px;
      border-top: 1px solid var(--rule);
      display: none;
    }}
    .history-row.open .history-drawer {{ display: block; }}
    .hd-blurb {{ font-size: 13.5px; color: var(--ink-secondary); margin-bottom: 9px; line-height: 1.5; }}
    .hd-chips {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .hd-chip {{
      font-size: 12px;
      padding: 4px 9px;
      border-radius: 5px;
      background: var(--card);
      border: 1px solid var(--rule);
      color: var(--ink);
    }}
    .hd-chip.champ-name {{
      background: var(--gold-bg);
      border-color: var(--gold-border);
      font-weight: 700;
    }}
    .hd-yr {{ color: var(--ink-muted); font-size: 11.5px; margin-left: 3px; font-weight: 500; }}

    /* Standings Table */
    .table-wrap {{ background: var(--card); border: 1px solid var(--rule); border-radius: 8px; overflow-x: auto; box-shadow: var(--shadow); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
    th {{
      text-align: left; padding: 11px 12px; background: var(--bg-alt); border-bottom: 1px solid var(--rule);
      font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-secondary);
      cursor: pointer; user-select: none; white-space: nowrap;
    }}
    th:hover {{ color: var(--ink); }}
    th.num, td.num {{ text-align: right; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid var(--rule); white-space: nowrap; background: var(--card); }}
    th.sticky-col, td.sticky-col {{ position: sticky; left: 0; z-index: 2; }}
    th.sticky-col {{ background: var(--bg-alt); z-index: 3; }}
    tr.team-row {{ cursor: pointer; }}
    tr.team-row:hover td {{ background: var(--slate-bg); }}
    tr.playoff-cut td {{ border-bottom: 2px dashed var(--emerald); }}
    .badge {{ display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 12px; font-weight: 700; }}
    .badge-pos {{ background: var(--emerald-bg); color: var(--emerald); }}
    .badge-neg {{ background: var(--crimson-bg); color: var(--crimson); }}
    .badge-mid {{ background: var(--amber-bg); color: var(--amber); }}

    /* Filter Pills */
    .filter-bar {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }}
    .filter-pill {{
      appearance: none; border: 1px solid var(--rule); background: var(--card); color: var(--ink-secondary);
      font-size: 12.5px; font-weight: 600; padding: 6px 11px; border-radius: 5px; cursor: pointer;
    }}
    .filter-pill:hover {{ color: var(--ink); background: var(--bg-alt); }}
    .filter-pill.active {{ background: var(--ink); color: var(--bg); border-color: var(--ink); }}

    /* Franchise Roast Cards */
    .roast-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(325px, 1fr)); gap: 16px; }}
    .roast-card {{
      background: var(--card); border: 1px solid var(--rule); border-radius: 8px; padding: 18px;
      box-shadow: var(--shadow); display: flex; flex-direction: column; gap: 11px; position: relative; overflow: hidden;
    }}
    .roast-card.is-bmt {{ border-color: var(--crimson); }}
    .roast-watermark {{
      position: absolute; right: -14px; bottom: -14px; width: 110px; height: 110px;
      opacity: 0.035; pointer-events: none;
    }}
    .roast-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }}
    .roast-seed {{ font-size: 12px; font-weight: 700; color: var(--ink-muted); text-transform: uppercase; letter-spacing: 0.06em; }}
    .roast-team {{ font-size: 19.5px; font-weight: 700; letter-spacing: -0.015em; line-height: 1.2; margin-top: 2px; }}
    .roast-mgr {{ font-size: 13px; color: var(--ink-muted); }}
    .roast-epithet {{ font-size: 13.5px; font-style: italic; color: var(--crimson); font-weight: 600; }}
    .roast-metrics {{
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; padding: 9px;
      background: var(--bg); border-radius: 6px; border: 1px solid var(--rule); text-align: center;
    }}
    .rm-label {{ font-size: 11.5px; color: var(--ink-muted); }}
    .rm-val {{ font-size: 13.5px; font-weight: 700; margin-top: 2px; }}
    .roast-crime {{
      font-size: 12.5px; font-weight: 600; padding: 7px 10px; border-radius: 5px;
      background: var(--amber-bg); color: var(--amber); border: 1px solid var(--amber-border);
    }}
    .roast-body {{ font-size: 14.5px; line-height: 1.58; color: var(--ink); position: relative; z-index: 1; }}

    .spark-wrap {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; align-items: end; padding-top: 6px; margin-top: auto; }}
    .spark-col {{ display: flex; flex-direction: column; align-items: center; gap: 3px; }}
    .spark-bar-bg {{ width: 100%; height: 42px; background: var(--bg-alt); border-radius: 3px; display: flex; align-items: flex-end; overflow: hidden; }}
    .spark-bar {{ width: 100%; border-radius: 3px 3px 0 0; }}
    .spark-bar.win {{ background: var(--emerald); }}
    .spark-bar.loss {{ background: var(--crimson); }}
    .spark-pts {{ font-size: 11.5px; color: var(--ink-secondary); }}
    .spark-wk {{ font-size: 11.5px; color: var(--ink-muted); }}

    /* Matchup Cards */
    .matchup-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(305px, 1fr)); gap: 14px; }}
    .matchup-card {{ background: var(--card); border: 1px solid var(--rule); border-radius: 8px; padding: 15px 16px; box-shadow: var(--shadow); }}
    .mc-row {{ display: flex; justify-content: space-between; align-items: center; padding: 5px 0; font-size: 14.5px; }}
    .mc-row.winner {{ font-weight: 700; }}
    .mc-row.loser {{ color: var(--ink-muted); }}
    .mc-foot {{ margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--rule); font-size: 12.5px; color: var(--ink-secondary); display: flex; justify-content: space-between; gap: 8px; }}

    .toast {{
      position: fixed; bottom: 20px; right: 20px; background: var(--ink); color: var(--bg);
      padding: 10px 15px; border-radius: 6px; font-size: 13px; font-weight: 600;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25); opacity: 0; pointer-events: none;
      transform: translateY(8px); transition: all 0.2s ease; z-index: 100;
    }}
    .toast.show {{ opacity: 1; transform: translateY(0); }}
    .hidden {{ display: none !important; }}
  </style>
</head>
<body>
  <!-- Subtle Super Smash Bros. Emblem SVG Definitions -->
  <svg width="0" height="0" style="position:absolute;width:0;height:0;overflow:hidden;" aria-hidden="true">
    <defs>
      <linearGradient id="smash-crest-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#F59E0B" />
        <stop offset="50%" stop-color="#DC2626" />
        <stop offset="100%" stop-color="#991B1B" />
      </linearGradient>
      <mask id="smash-ball-cutout">
        <rect x="0" y="0" width="100" height="100" fill="black" />
        <circle cx="50" cy="50" r="46" fill="white" />
        <rect x="24" y="0" width="14" height="100" fill="black" />
        <rect x="0" y="60" width="100" height="10" fill="black" />
      </mask>
      <symbol id="smash-ball-crest" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="46" fill="url(#smash-crest-grad)" mask="url(#smash-ball-cutout)" />
      </symbol>
      <symbol id="smash-ball-mono" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="46" fill="currentColor" mask="url(#smash-ball-cutout)" />
      </symbol>
    </defs>
  </svg>

  <header class="masthead">
    <div class="container">
      <div class="masthead-top">
        <span>Vol. X • {html.escape(model['leagueName'])} • 12-Team Superflex PPR</span>
        <div class="masthead-actions">
          <button id="btn-copy-link" class="btn btn-primary" type="button">Copy Group-Chat Link</button>
          <button id="btn-theme" class="btn" type="button">Night Mode</button>
          <a class="btn" href="https://fantasy.espn.com/football/league?leagueId={model['leagueId']}" target="_blank" rel="noopener">ESPN League</a>
        </div>
      </div>

      <div class="brand-row">
        <div class="brand-heading">
          <svg class="brand-crest" viewBox="0 0 100 100" aria-hidden="true">
            <use href="#smash-ball-crest"></use>
          </svg>
          <div class="brand-title serif">The Alliance Dispatch</div>
        </div>
        <div class="brand-sub">Office of League Communications • Dispatches Live From the 12th-Place Bunker at Bad Mother Tucker's HQ</div>
      </div>

      <div class="artwork-banner">
        <img
          src="{html.escape(hero_img_src)}"
          onerror="this.onerror=null;this.src='{html.escape(og_image_url)}';"
          alt="The Super Smash Alliance 10.0 Stadium Illustration"
        />
        <div class="artwork-caption">
          <span><strong>{html.escape(model['leagueName'])}</strong> • Est. 2012 (15th Anniversary Season)</span>
          <span class="mono">0 Trades • 6 Teams Tied at 4-3 • 14 Historical Rings</span>
        </div>
      </div>
    </div>
  </header>

  <nav class="edition-bar" aria-label="Recap Editions">
    <div class="container edition-inner" id="edition-tabs">
      <span class="edition-label">Editions:</span>
    </div>
  </nav>

  <main class="container">
    <div id="view-midseason">
      <section class="hero">
        <div class="kicker">Special Midseason Roast • Through Week {model['completedWeeks']} of 14</div>
        <h1 class="serif">Halfway Through the Season: 8 of You Are the Spider-Man Pointing Meme, and I Am Already Dead</h1>
        <p class="hero-lede">
          We have reached the midpoint of The Super Smash Alliance 10.0 regular season with <strong>zero trades executed</strong>,
          <strong>six consecutive teams deadlocked at 4-3</strong>, <strong>eight of twelve managers crammed within a single game of .500</strong>,
          Kyle Feeney sitting in 2nd place after making <em>one</em> waiver move since August, and your Head of Communications
          reporting from a 1-6 crater with a -261.64 point differential.
        </p>
        <div class="byline">
          <span>By <strong>Josh Briskman</strong> (Head of Comms • 1-6 • #1 Waiver Priority Forever)</span>
          <span class="mono">Playoff Cutoff Margin (#6 vs #7): 2.30 Pts</span>
        </div>
      </section>

      <div class="stat-strip">
        <div class="stat-box">
          <div class="stat-box-label">The Parity Mosh Pit</div>
          <div class="stat-box-val mono">8 of 12 Teams</div>
          <div class="stat-box-note">Seeds #2 (5-2) through #9 (3-4) separated by 1 game of 4-3; 6 teams tied at 4-3</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Playoff Bubble Razor</div>
          <div class="stat-box-val mono">2.30 Points</div>
          <div class="stat-box-note">#6 Huffner (918.32 PF) holds the final chair over #7 #FedOut (916.02 PF)</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Casino Heist Trophy</div>
          <div class="stat-box-val mono">+1.91 Wins</div>
          <div class="stat-box-note">Feeney (5-2) is 9th in PF (856.4), 34-43 All-Play, with 1 waiver move all year</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Comms Desk Morgue</div>
          <div class="stat-box-val mono" style="color: var(--crimson);">-261.64 Diff</div>
          <div class="stat-box-note">Bad Mother Tucker's: #12 PF (753.16), #12 PA (1,014.80), L6 skid, 2.6% odds</div>
        </div>
      </div>

      <section class="section">
        <div class="section-header">
          <h2 class="section-title serif">The 8-of-12 Parity Circus: Six Guys at 4-3, Eight Teams in a Phone Booth</h2>
          <span class="section-sub">Tap any team chip to jump straight to their roast</span>
        </div>
        <div class="parity-panel">
          <p style="color: var(--ink-secondary); font-size: 14.5px;">
            Only <strong>6 playoff chairs</strong> exist, yet <strong>8 teams sit at 4-3 or better</strong>—meaning two winning records are
            headed straight to the consolation bracket—while <strong>Seeds #2 through #9 (two-thirds of the league)</strong> sit within one Sunday
            swing of the six-way 4-3 pileup. Naturally, <strong>0 trades</strong> have been made because everyone thinks their mediocre roster is one backup TE away.
          </p>
          <div class="parity-tiers" id="parity-tiers"></div>
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <h2 class="section-title serif">Self-Roast First: The Autopsy of Bad Mother Tucker's (#12 • 1-6)</h2>
          <span class="section-sub">You cannot hurt a man who has been clinically deceased since Week 2</span>
        </div>
        <div class="autopsy-card">
          <p style="font-size: 15px; font-weight: 600;">
            Before anyone replies "focus on your own lineup, Josh," allow the Office of Communications to empty the clip on itself first:
          </p>
          <div class="autopsy-grid">
            <figure class="trophy-figure">
              <img
                src="{html.escape(trophy_img_src)}"
                onerror="this.onerror=null;this.src='{html.escape(PUBLIC_SITE_URL)}assets/smash-bmt-trophy.jpg';"
                alt="Bad Mother Tucker's Cracked Helmet Last-Place Trophy"
              />
              <figcaption class="trophy-figcaption">
                Exhibit A: The 2026 Bad Mother Tucker's Last-Place Trophy (<span class="mono">1-6</span>, <span class="mono">-261.64</span> Diff)
              </figcaption>
            </figure>
            <ul class="autopsy-list">
              <li><strong>Peaked in Week 1:</strong> Dropped <span class="mono">153.64</span> on Owen in Week 1 to go 1-0, started measuring ring sizes, and immediately lost <strong>6 straight games</strong>—finishing as the weekly low scorer 3 times in 4 weeks (<span class="mono">100.88</span>, <span class="mono">87.14</span>, <span class="mono">93.46</span>, plus <span class="mono">81.20</span> in Wk 6).</li>
              <li><strong>Both Terrible AND Cursed:</strong> Opponents average a league-high <span class="mono">144.97 PPG</span> (<span class="mono">1,014.80 PA</span>) against us—highlighted by Wills' <span class="mono">207.86</span>-point thermonuclear execution in Week 2 (-106.98 margin) and Billy's <span class="mono">183.00</span> in Week 5. Yet we can't even cry schedule luck because we <em>also</em> rank dead last in scoring (<span class="mono">753.16 PF</span>, nearly 80 pts behind 11th and 346.66 behind Wills).</li>
              <li><strong>Superflex Masterclass:</strong> Currently rolling out <strong>Tanner McKee (<span class="mono">23.14</span> season pts)</strong> at QB1 while squatting permanently on #1 weekly resetting waivers. ESPN still gives us a <span class="mono">2.6%</span> playoff chance—proof AI hallucination is very real.</li>
            </ul>
            <div class="crime-box">
              <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--crimson); margin-bottom: 8px;">
                Draft Board Built in Hell (Rounds 1–4 vs. Reality)
              </div>
              <div class="crime-row"><span><strong>Rd 1 (#7)</strong> Jalen Hurts (QB)</span><span class="mono" style="color: var(--crimson);">IR / Off Roster</span></div>
              <div class="crime-row"><span><strong>Rd 2 (#18)</strong> Justin Jefferson (WR)</span><span class="mono">72.10 pts (#6 on team)</span></div>
              <div class="crime-row"><span><strong>Rd 3 (#31)</strong> Kyler Murray (QB)</span><span class="mono">53.68 pts (Beat by Kicker)</span></div>
              <div class="crime-row"><span><strong>Rd 4 (#42)</strong> Breece Hall (RB)</span><span class="mono">43.50 pts (Riding Pine)</span></div>
              <div class="crime-row"><span><strong>Rd 10 (#114)</strong> Brandon Aubrey (K)</span><span class="mono" style="color: var(--emerald);">58.00 pts (&gt; Kyler)</span></div>
              <div class="crime-row"><span><strong>Rd 14 (#162)</strong> Steelers D/ST</span><span class="mono" style="color: var(--emerald);">57.00 pts (&gt; Kyler)</span></div>
            </div>
          </div>
        </div>
      </section>

      <section class="section" id="history-section">
        <div class="section-header">
          <h2 class="section-title serif">15 Years of Alliance Lore (2012–2026): Team Names vs. Championships</h2>
          <span class="section-sub">Click any manager row to inspect every historical team name &amp; title year</span>
        </div>
        <div class="history-panel">
          <div class="history-callouts">
            <div class="history-callout">
              <div class="hc-kicker">Witness Protection Award</div>
              <div class="hc-val">D B — 12 Names, 0 Rings</div>
              <div class="hc-note">A fresh rebrand almost every August since 2012; still waiting on trophy number one.</div>
            </div>
            <div class="history-callout">
              <div class="hc-kicker">Fallen Dynasty</div>
              <div class="hc-val">Josh — 4 Titles, Now 1-6</div>
              <div class="hc-note">Owns 4 of 14 historical rings (2015, '17, '20, '21) and currently sits dead last starting Tanner McKee.</div>
            </div>
            <div class="history-callout">
              <div class="hc-kicker">ESPN Auto-Fill Club</div>
              <div class="hc-val">3 Rings on "Team LastName"</div>
              <div class="hc-note">O'Keefe (2) &amp; Jackson (1) won titles without touching settings; Wills &amp; Huffner have 0 in 22 combined seasons.</div>
            </div>
          </div>

          <div class="history-toolbar">
            <div class="history-controls">
              <button type="button" class="filter-pill active" data-hsort="names">Sort: Most Team Names</button>
              <button type="button" class="filter-pill" data-hsort="rings">Sort: Most Championships</button>
              <button type="button" class="filter-pill" data-hsort="ratio">Sort: Rings / Name</button>
              <button type="button" class="btn" id="btn-expand-names">Expand All Names</button>
              <button type="button" class="btn" id="btn-toggle-alumni">Include 4 Retired Alumni</button>
            </div>
            <div class="history-legend">
              <span class="legend-item"><span class="legend-swatch swatch-names"></span> Distinct Team Names (2012–26)</span>
              <span class="legend-item"><span class="legend-swatch swatch-rings"></span> Championships Won (2012–25)</span>
            </div>
          </div>

          <div class="history-scale-head mono">
            <div>Manager (Current Franchise)</div>
            <div class="scale-ticks"><span>0</span><span>3</span><span>6</span><span>9</span><span>12</span></div>
            <div style="text-align:right;">Name Archive</div>
          </div>

          <div class="history-rows" id="history-chart-rows"></div>
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <h2 class="section-title serif">Midseason Receipts: Standings, All-Play &amp; Schedule Luck</h2>
          <span class="section-sub">Click any column header to sort • Dashed emerald line = Top-6 Playoff Cutoff</span>
        </div>
        <div class="table-wrap">
          <table id="standings-table">
            <thead>
              <tr>
                <th data-sort="seed">Seed</th>
                <th data-sort="name" class="sticky-col">Team (Manager)</th>
                <th data-sort="wins" class="num">Record</th>
                <th class="num">Streak</th>
                <th data-sort="pf" class="num">Points For</th>
                <th data-sort="pa" class="num">Points Against</th>
                <th data-sort="diff" class="num">Diff</th>
                <th data-sort="allPlayPct" class="num">All-Play</th>
                <th data-sort="luck" class="num">LuckWins</th>
                <th data-sort="moves" class="num">Moves</th>
                <th data-sort="playoffPct" class="num">Playoff %</th>
              </tr>
            </thead>
            <tbody id="standings-tbody"></tbody>
          </table>
        </div>
      </section>

      <section class="section" id="roasts-section">
        <div class="section-header">
          <h2 class="section-title serif">All 12 Franchises, Roasted With Receipts</h2>
          <span class="section-sub">Filter by tier or tap your friend's name to isolate their crime scene</span>
        </div>
        <div class="filter-bar" id="team-filters"></div>
        <div class="roast-grid" id="roast-grid"></div>
      </section>

      <section class="section">
        <div class="section-header">
          <h2 class="section-title serif">Week {model['upcomingWeek']} Chaos Watch</h2>
          <span class="section-sub">Upcoming slate entering the back half of the regular season</span>
        </div>
        <div class="matchup-grid" id="upcoming-grid"></div>
      </section>
    </div>

    <div id="view-weekly" class="hidden">
      <section class="hero">
        <div class="kicker" id="wk-kicker"></div>
        <h1 class="serif" id="wk-headline"></h1>
        <p class="hero-lede" id="wk-subhead"></p>
        <div class="byline">
          <span>By <strong>Office of League Communications</strong> • The Super Smash Alliance 10.0</span>
          <span class="mono" id="wk-median-badge"></span>
        </div>
      </section>

      <div class="stat-strip" id="wk-awards"></div>

      <section class="section">
        <div class="section-header">
          <h2 class="section-title serif" id="wk-scoreboard-title">Week Box Scores</h2>
          <span class="section-sub">Sorted by highest-scoring matchup</span>
        </div>
        <div class="matchup-grid" id="wk-games-grid"></div>
      </section>

      <section class="section">
        <div class="section-header">
          <h2 class="section-title serif" id="wk-standings-title">Standings Snapshot</h2>
          <span class="section-sub">Cumulative league table at the conclusion of this week</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th class="sticky-col">Team (Manager)</th>
                <th class="num">Record</th>
                <th class="num">Week Score</th>
                <th class="num">Season PF</th>
                <th class="num">Season PA</th>
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

    let historySort = "names";
    let showAlumni = false;
    let expandAllHistory = false;
    const openHistoryKeys = new Set();

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
      const editions = [{{ id: "midseason", label: "Midseason Roast (Wks 1–" + LEAGUE_DATA.completedWeeks + ")" }}];
      for (let w = LEAGUE_DATA.completedWeeks; w >= 1; w--) {{
        editions.push({{ id: "week-" + w, label: "Week " + w }});
      }}
      editions.forEach(ed => {{
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "edition-tab" + (ed.id === currentIssue ? " active" : "");
        btn.dataset.issue = ed.id;
        btn.textContent = ed.label;
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
        {{ label: "The Horseshoe Penthouse (1 Team)", cls: "", teams: LEAGUE_DATA.teams.filter(t => t.seed === 1) }},
        {{ label: "The 8-Team Parity Pit (#2–#9 • ±1 Game of 4-3)", cls: "highlight-parity", teams: LEAGUE_DATA.teams.filter(t => t.seed >= 2 && t.seed <= 9) }},
        {{ label: "The Cellar & Comms Morgue (3 Teams)", cls: "highlight-morgue", teams: LEAGUE_DATA.teams.filter(t => t.seed >= 10) }}
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
          chip.className = "team-chip mono";
          chip.textContent = `#${{t.seed}} ${{t.name}} (${{t.wins}}-${{t.losses}})`;
          chip.addEventListener("click", () => focusTeamRoast(t.id));
          chips.appendChild(chip);
        }});
        row.appendChild(tag);
        row.appendChild(chips);
        container.appendChild(row);
      }});
    }}

    function renderHistoryChart() {{
      const container = document.getElementById("history-chart-rows");
      if (!container || !LEAGUE_DATA.history) return;
      const allFr = LEAGUE_DATA.history.franchises || [];
      let rows = showAlumni ? [...allFr] : allFr.filter(f => f.active);

      rows.sort((a, b) => {{
        if (historySort === "rings") {{
          if (b.championships !== a.championships) return b.championships - a.championships;
          if (a.nameCount !== b.nameCount) return a.nameCount - b.nameCount;
          return a.shortManager.localeCompare(b.shortManager);
        }}
        if (historySort === "ratio") {{
          const ra = a.championships / Math.max(1, a.nameCount);
          const rb = b.championships / Math.max(1, b.nameCount);
          if (rb !== ra) return rb - ra;
          if (b.championships !== a.championships) return b.championships - a.championships;
          return a.nameCount - b.nameCount;
        }}
        // Default: Most Team Names
        if (b.nameCount !== a.nameCount) return b.nameCount - a.nameCount;
        if (b.championships !== a.championships) return b.championships - a.championships;
        return a.shortManager.localeCompare(b.shortManager);
      }});

      const maxScale = Math.max(12, ...rows.map(r => Math.max(r.nameCount, r.championships)));
      container.innerHTML = "";

      rows.forEach(fr => {{
        const isOpen = expandAllHistory || openHistoryKeys.has(fr.key);
        const rowEl = document.createElement("div");
        rowEl.className = "history-row" + (fr.active ? "" : " is-alumni") + (isOpen ? " open" : "");

        const namePct = Math.max(3, Math.round((fr.nameCount / maxScale) * 100));
        const ringPct = fr.championships > 0 ? Math.max(3, Math.round((fr.championships / maxScale) * 100)) : 0;

        const nameLabel = fr.nameCount === 1 ? "1 Team Name" : `${{fr.nameCount}} Team Names`;
        let ringLabel = "0 Titles";
        if (fr.championships > 0) {{
          const yrsShort = fr.champYears.map((y, idx) => idx === 0 ? String(y) : "'" + String(y).slice(2)).join(", ");
          ringLabel = `🏆 ${{fr.championships}} ${{fr.championships === 1 ? "Title" : "Titles"}} (${{yrsShort}})`;
        }}

        const chipsHtml = fr.names.map(n => {{
          const isChamp = n.champYears && n.champYears.length > 0;
          const trophy = isChamp ? ` 🏆 ${{n.champYears.join(", ")}}` : "";
          return `<span class="hd-chip${{isChamp ? " champ-name" : ""}}">${{n.name}}<span class="hd-yr">(${{n.years}})${{trophy}}</span></span>`;
        }}).join("");

        rowEl.innerHTML = `
          <div class="history-row-main">
            <div class="hr-who">
              <div class="hr-mgr">
                <span>${{fr.shortManager}}</span>
                ${{fr.active ? "" : '<span class="hr-alumni-tag">Alumni</span>'}}
              </div>
              <div class="hr-cur">${{fr.currentTeam}} • ${{fr.seasons}} ${{fr.seasons === 1 ? "season" : "seasons"}}</div>
            </div>
            <div class="hr-bars">
              <div class="bar-line">
                <div class="bar-track"><div class="bar-fill names" style="width:${{namePct}}%;"></div></div>
                <div class="bar-stat mono">${{nameLabel}}</div>
              </div>
              <div class="bar-line">
                <div class="bar-track"><div class="bar-fill rings" style="width:${{ringPct}}%;"></div></div>
                <div class="bar-stat mono ${{fr.championships > 0 ? "has-rings" : "zero-rings"}}">${{ringLabel}}</div>
              </div>
            </div>
            <div class="hr-toggle">${{isOpen ? "Hide names ▴" : "View names ▾"}}</div>
          </div>
          <div class="history-drawer">
            <div class="hd-blurb">${{fr.blurb}}</div>
            <div class="hd-chips">${{chipsHtml}}</div>
          </div>
        `;

        rowEl.addEventListener("click", () => {{
          if (expandAllHistory) {{
            expandAllHistory = false;
            document.getElementById("btn-expand-names").textContent = "Expand All Names";
            openHistoryKeys.clear();
            rows.forEach(r => {{ if (r.key !== fr.key) openHistoryKeys.add(r.key); }});
          }} else if (openHistoryKeys.has(fr.key)) {{
            openHistoryKeys.delete(fr.key);
          }} else {{
            openHistoryKeys.add(fr.key);
          }}
          renderHistoryChart();
        }});

        container.appendChild(rowEl);
      }});
    }}

    function initHistoryControls() {{
      document.querySelectorAll("[data-hsort]").forEach(btn => {{
        btn.addEventListener("click", () => {{
          historySort = btn.dataset.hsort;
          document.querySelectorAll("[data-hsort]").forEach(b => b.classList.toggle("active", b.dataset.hsort === historySort));
          renderHistoryChart();
        }});
      }});
      const expBtn = document.getElementById("btn-expand-names");
      if (expBtn) {{
        expBtn.addEventListener("click", () => {{
          expandAllHistory = !expandAllHistory;
          if (!expandAllHistory) openHistoryKeys.clear();
          expBtn.textContent = expandAllHistory ? "Collapse All Names" : "Expand All Names";
          renderHistoryChart();
        }});
      }}
      const alumBtn = document.getElementById("btn-toggle-alumni");
      if (alumBtn) {{
        alumBtn.addEventListener("click", () => {{
          showAlumni = !showAlumni;
          alumBtn.textContent = showAlumni ? "Hide 4 Retired Alumni" : "Include 4 Retired Alumni";
          renderHistoryChart();
        }});
      }}
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
          <td class="mono"><strong>#${{t.seed}}</strong></td>
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
        {{ id: "all", label: "All 12 Franchises" }},
        {{ id: "parity8", label: "The 8-Team Parity Pit (#2–#9)" }},
        {{ id: "fourthree", label: "The 4-3 Six-Pack (#3–#8)" }},
        {{ id: "bmt", label: "Bad Mother Tucker's Autopsy (#12)" }}
      ];
      LEAGUE_DATA.teams.forEach(t => presets.push({{ id: "team-" + t.id, label: `#${{t.seed}} ${{t.name}}` }}));
      bar.innerHTML = "";
      presets.forEach(p => {{
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "filter-pill" + (currentFilter === p.id ? " active" : "");
        btn.dataset.filter = p.id;
        btn.textContent = p.label;
        btn.addEventListener("click", () => {{
          currentFilter = p.id;
          document.querySelectorAll("#team-filters .filter-pill").forEach(el => el.classList.toggle("active", el.dataset.filter === p.id));
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
        const luckSign = t.luck > 0 ? "+" : "";
        const sparks = t.weekly.map(w => {{
          const [wk, pts, oppId, oppPts, res] = w;
          const oppName = (TEAMS_BY_ID[oppId] || {{}}).name || "";
          const pct = Math.max(14, Math.min(100, Math.round(((pts - 55) / 155) * 100)));
          const cls = res === "W" ? "win" : "loss";
          return `
            <div class="spark-col" title="Wk ${{wk}}: ${{res}} ${{pts.toFixed(2)}} vs ${{oppName}} (${{oppPts.toFixed(2)}})">
              <div class="spark-pts mono">${{Math.round(pts)}}</div>
              <div class="spark-bar-bg"><div class="spark-bar ${{cls}}" style="height:${{pct}}%"></div></div>
              <div class="spark-wk mono">W${{wk}}${{res}}</div>
            </div>
          `;
        }}).join("");

        card.innerHTML = `
          <svg class="roast-watermark" viewBox="0 0 100 100" aria-hidden="true">
            <use href="#smash-ball-mono"></use>
          </svg>
          <div class="roast-head">
            <div>
              <div class="roast-seed mono">Seed #${{t.seed}} • ${{t.wins}}-${{t.losses}} (${{t.streak}}) • ${{t.playoffPct.toFixed(1)}}% Odds</div>
              <h3 class="roast-team serif">${{t.name}}</h3>
              <div class="roast-mgr">${{t.manager}}</div>
            </div>
            <button type="button" class="btn share-team-btn" data-tid="${{t.id}}" title="Copy direct link to this roast">Share</button>
          </div>
          <div class="roast-epithet">"${{t.epithet}}"</div>
          <div class="roast-metrics mono">
            <div><div class="rm-label">PF</div><div class="rm-val">${{t.pf.toFixed(1)}}</div></div>
            <div><div class="rm-label">All-Play</div><div class="rm-val">${{t.allPlayW}}-${{t.allPlayL}}</div></div>
            <div><div class="rm-label">Luck</div><div class="rm-val">${{luckSign}}${{t.luck.toFixed(2)}}</div></div>
            <div><div class="rm-label">Moves</div><div class="rm-val">${{t.moves}}</div></div>
          </div>
          <div class="roast-crime">${{t.crime}}</div>
          <p class="roast-body">${{t.roast}}</p>
          <div class="spark-wrap">${{sparks}}</div>
        `;
        grid.appendChild(card);
      }});

      grid.querySelectorAll(".share-team-btn").forEach(btn => {{
        btn.addEventListener("click", (e) => {{
          e.stopPropagation();
          const tid = Number(btn.dataset.tid);
          const team = TEAMS_BY_ID[tid];
          const link = canonicalIssueUrl("midseason", tid);
          copyText(`${{team.name}} (#${{team.seed}}, ${{team.wins}}-${{team.losses}}) — "${{team.epithet}}": ${{link}}`, `Copied ${{team.name}} roast link!`);
        }});
      }});
    }}

    function focusTeamRoast(tid) {{
      currentFilter = "team-" + tid;
      document.querySelectorAll("#team-filters .filter-pill").forEach(el => el.classList.toggle("active", el.dataset.filter === currentFilter));
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
          <div class="mc-row winner"><span>#${{a.seed}} ${{a.name}}</span><span class="mono">${{a.wins}}-${{a.losses}}</span></div>
          <div class="mc-row winner"><span>@ #${{h.seed}} ${{h.name}}</span><span class="mono">${{h.wins}}-${{h.losses}}</span></div>
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
      document.getElementById("wk-median-badge").textContent = `League Weekly Median: ${{wk.median.toFixed(2)}} Pts`;
      document.getElementById("wk-scoreboard-title").textContent = `Week ${{wk.week}} Final Box Scores`;
      document.getElementById("wk-standings-title").textContent = `Standings Snapshot Through Week ${{wk.week}}`;

      const highT = TEAMS_BY_ID[wk.high[0]], lowT = TEAMS_BY_ID[wk.low[0]];
      const clW = TEAMS_BY_ID[wk.closest[0]], clL = TEAMS_BY_ID[wk.closest[2]];
      const luckyTxt = wk.lucky
        ? `${{TEAMS_BY_ID[wk.lucky[0]].name}} won with ${{wk.lucky[1].toFixed(2)}} (sub-median)`
        : "Every winner cleared the median";
      const brutalTxt = wk.brutal
        ? `${{TEAMS_BY_ID[wk.brutal[2]].name}} scored ${{wk.brutal[3].toFixed(2)}} and LOST`
        : "Every above-median scorer won";

      document.getElementById("wk-awards").innerHTML = `
        <div class="stat-box">
          <div class="stat-box-label">Scoring Belt (High)</div>
          <div class="stat-box-val mono" style="color: var(--emerald);">${{wk.high[1].toFixed(2)}}</div>
          <div class="stat-box-note"><strong>${{highT.name}}</strong> (${{highT.manager}})</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Toilet Bowl (Low)</div>
          <div class="stat-box-val mono" style="color: var(--crimson);">${{wk.low[1].toFixed(2)}}</div>
          <div class="stat-box-note"><strong>${{lowT.name}}</strong> (${{lowT.manager}})</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Closest Sweat</div>
          <div class="stat-box-val mono">+${{wk.closest[4].toFixed(2)}} Pts</div>
          <div class="stat-box-note">${{clW.name}} (${{wk.closest[1].toFixed(2)}}) over ${{clL.name}} (${{wk.closest[3].toFixed(2)}})</div>
        </div>
        <div class="stat-box">
          <div class="stat-box-label">Heist &amp; Heartbreak</div>
          <div class="stat-box-val mono" style="font-size: 17px;">Median: ${{wk.median.toFixed(2)}}</div>
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
          <div class="mc-row loser"><span>${{TEAMS_BY_ID[lid].name}}</span><span class="mono">${{lpts.toFixed(2)}}</span></div>
          <div class="mc-foot">
            <span>Margin: <strong class="mono">+${{margin.toFixed(2)}}</strong></span>
            <span>${{wpts < wk.median ? "Sub-Median Heist" : (lpts > wk.median ? "Above-Median Loss" : "Regulation W")}}</span>
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
          <td class="mono"><strong>#${{rank}}</strong></td>
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
      document.getElementById("btn-theme").textContent = next === "dark" ? "Light Mode" : "Night Mode";
    }});

    document.getElementById("btn-copy-link").addEventListener("click", () => {{
      const url = canonicalIssueUrl(currentIssue);
      let teaser = "The Alliance Dispatch — Midseason Roast (8 of you in a 4-3 phone booth, 15 years of team names vs. rings, and Bad Mother Tucker's 1-6 funeral): " + url;
      if (currentIssue.startsWith("week-")) {{
        const wk = LEAGUE_DATA.weeks[currentIssue.replace("week-", "")];
        if (wk) teaser = wk.teaser + " " + url;
      }}
      copyText(teaser, "Group-chat link copied!");
    }});

    buildEditionTabs();
    renderParityTiers();
    initHistoryControls();
    renderHistoryChart();
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

    # Persist structured 15-year franchise history JSON alongside espn_full.json
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "league_history.json"), "w") as f:
        json.dump(model["history"], f, indent=2, ensure_ascii=False)

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

Official static sports broadsheet, 15-year franchise lore archive (2012–2026), and weekly roast site for **The Super Smash Alliance 10.0** (ESPN League `1000567`).

**Live Site:** https://briskman-j.github.io/SSA-2026/

## Shareable Per-Edition Group-Chat Links
Every edition has its own dedicated URL and custom OpenGraph iMessage / WhatsApp preview card:
- **Midseason State of the Alliance Roast (Weeks 1–7 + 15-Year Team Names vs. Rings Chart):** https://briskman-j.github.io/SSA-2026/recaps/midseason/
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
