"""Generate clearly labeled FAKE data for LedgerLine.

Spec: docs/data-generator.md. Every generated user has is_generated = true and an
@example.com email. Theo's own account and logs are never read or changed, except
that the script refuses to run if his rows depend on generated rows.

Run from the repo root:  python scripts/seed.py
"""
import csv
import os
import unicodedata
import random
import secrets
from datetime import date, datetime, time, timedelta
from itertools import product
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# ---------- 1. Settings ----------
SEED = 20261116                      # fixed: same data shape on every run
TZ = ZoneInfo("America/Denver")      # Windows needs: pip install tzdata
NOW = datetime.now(TZ)
TODAY = NOW.date()
WINDOW_START = TODAY - timedelta(days=8 * 7 - 1)   # 8 weeks, ending today
MESSY_CSV = Path("data/practice_logs_messy.csv")

# Bands use rcm_levels.sort_order (1 = Prep A ... 13 = ARCT).
BANDS = {1: range(1, 5), 2: range(5, 8), 3: range(8, 11), 4: range(11, 14)}
BAND_MINUTES = {1: (20, 40), 2: (40, 70), 3: (60, 120), 4: (90, 180)}  # per day
STUDENTS_PER_BAND = 25
OPTED_IN_PER_BAND = 13               # spec: 12+; 13 of 25 = 52%, close to the 50% assumption
SKIP_RATE = {"steady": 0.10, "average": 0.30, "sporadic": 0.55}
SHAPES = ["taper", "taper_cram", "flat"]
TAGGED_SHARE = 0.7                   # share of students with a preset level tag
WEEKLY_GOAL = {1: (120, 210), 2: (180, 330), 3: (270, 480), 4: (420, 630)}  # minutes, by band
SOLO_EMAIL = "solo.student@example.com"   # existing login with no studio, can accept an invite
DEMO_INVITES = ["new.student.one@example.com", "new.student.two@example.com",
                SOLO_EMAIL]                     # pending invites to demo studio 1

# ---------- 2. Reference data ----------
CITIES = [  # approximate city-centre coordinates
    ("Salt Lake City", 40.76078, -111.89105), ("Provo", 40.23384, -111.65853),
    ("Orem", 40.29690, -111.69465), ("Ogden", 41.22300, -111.97383),
    ("Logan", 41.73549, -111.83439), ("St. George", 37.10415, -113.58412),
    ("Lehi", 40.39162, -111.85077), ("Sandy", 40.56498, -111.85897),
]

# (title, composer, rcm sort_order). Levels are APPROXIMATE demo placements,
# not official RCM syllabus listings.
PIECES = [
    ("Lightly Row", "Traditional", 1), ("Hot Cross Buns", "Traditional", 1),
    ("Ode to Joy (arr.)", "Beethoven", 1),
    ("Au clair de la lune", "Traditional", 2), ("London Bridge", "Traditional", 2),
    ("Twinkle, Twinkle, Little Star", "Traditional", 2),
    ("Minuet in F, K. 2", "Mozart", 3), ("The Bear", "Rebikov", 3),
    ("Melody, Op. 68 No. 1", "Schumann", 3),
    ("Minuet in G, BWV Anh. 114", "Petzold", 4), ("Écossaise in G, WoO 23", "Beethoven", 4),
    ("Soldiers' March, Op. 68 No. 2", "Schumann", 4),
    ("Musette in D, BWV Anh. 126", "Bach", 5), ("The Wild Horseman, Op. 68 No. 8", "Schumann", 5),
    ("Sonatina in G, Anh. 5 No. 1", "Beethoven", 5),
    ("Minuet in G minor, BWV Anh. 115", "Petzold", 6), ("Old French Song, Op. 39 No. 16", "Tchaikovsky", 6),
    ("Sonatina in C, Op. 36 No. 1", "Clementi", 6),
    ("Sonatina in G, Op. 36 No. 2", "Clementi", 7), ("The Doll's Funeral, Op. 39 No. 7", "Tchaikovsky", 7),
    ("Little Prelude in C, BWV 939", "Bach", 7),
    ("Sonatina in C, Op. 36 No. 3", "Clementi", 8), ("Waltz in A minor, B. 150", "Chopin", 8),
    ("Gymnopédie No. 1", "Satie", 8),
    ("Für Elise, WoO 59", "Beethoven", 9), ("Invention No. 1 in C, BWV 772", "Bach", 9),
    ("Prelude in E minor, Op. 28 No. 4", "Chopin", 9),
    ("Invention No. 8 in F, BWV 779", "Bach", 10), ("Prelude in B minor, Op. 28 No. 6", "Chopin", 10),
    ("Sonata in C, K. 545, I", "Mozart", 10),
    ("Nocturne in E-flat, Op. 9 No. 2", "Chopin", 11), ("Arabesque No. 1", "Debussy", 11),
    ("Sinfonia No. 11 in G minor, BWV 797", "Bach", 11),
    ("Clair de lune", "Debussy", 12), ("Sonata Op. 13 'Pathétique', II", "Beethoven", 12),
    ("Impromptu in A-flat, Op. 142 No. 2", "Schubert", 12),
    ("Ballade No. 1 in G minor, Op. 23", "Chopin", 13), ("Sonata Op. 27 No. 2, III", "Beethoven", 13),
    ("Prelude in C-sharp minor, Op. 3 No. 2", "Rachmaninoff", 13),
]

FIRST = ["Allegra", "Cadence", "Melody", "Harmony", "Octavia", "Treble", "Lenny", "Dot",
         "Rocky", "Sonny", "Tempo", "Viv", "Reed", "Bella", "Clef", "Coda", "Rhett", "Ivy"]
LAST = ["Keyes", "Pedalworth", "Sharpe", "Flatley", "Staccatowski", "Restman",
        "Metronomo", "Scales", "Ivory", "Trillby", "Clefton", "Fermata", "Hammerstein", "Downbeat"]
COMPOSER_NAMES = ["Ludwig van Beatdown", "Frédéric Choplin", "Johann Sebastian Snack",
                  "Wolfgang Amadeus Snoozart"]   # the "very few" composer jokes
LOG_NOTES = ["Left hand finally behaving", "Slow practice, bars 9-16", "Metronome at 72",
             "Memorised the first page", "Played it for my cat. Cat left.",
             "Practised while the pizza was in the oven", "Wrong notes but with confidence",
             "The trill and I are no longer on speaking terms", "Pedal is hard"]
LESSON_NOTES = ["Great progress on dynamics; keep the wrist loose.",
                "Count out loud in bars 5-8 this week.", "Hands separate first, then together.",
                "Lovely phrasing. Watch the tempo in the coda.",
                "Claimed the dog ate the metronome. Doubtful."]
TEMPLATES = [("Slow practice", "Hands separate at half tempo, 5 clean reps."),
             ("Metronome ladder", "Start at 60 bpm; +4 after 3 clean reps.")]
EXTRA_STUDENT_TAGS = [("Recital prep", "#2563EB"), ("Competition", "#D97706")]
PIECE_TAGS = [("Recital", "#059669"), ("Sight-reading", "#7C3AED")]
LEVEL_TAG_COLOR = "#6B7280"
PRESET_STUDENT_TAGS = ["Beginner", "Adult", "RCM 4"]   # locked defaults every studio gets (same as auth.py)


def level_tag_name(sort_order):
    """Preset tag name for an RCM sort_order, e.g. 5 -> '[RCM 3]', 1 -> '[Prep A]'."""
    if sort_order == 1:
        return "[Prep A]"
    if sort_order == 2:
        return "[Prep B]"
    if sort_order == 13:
        return "[ARCT]"
    return f"[RCM {sort_order - 2}]"


def band_of(sort_order):
    """Band number (1-4) for an RCM sort_order."""
    return next(b for b, levels in BANDS.items() if sort_order in levels)


def at(day, hour, minute=0):
    """Timezone-aware datetime for a local date and time."""
    return datetime.combine(day, time(hour, minute), TZ)


def next_lesson(day, weekday):
    """First date on or after `day` that falls on `weekday` (0 = Monday)."""
    return day + timedelta(days=(weekday - day.weekday()) % 7)


# ---------- 3. Planning in Python (no database yet) ----------
def make_names(rng, count):
    """Unique funny names: a few composer jokes, the rest first+last combinations."""
    combos = [f"{f} {l}" for f, l in product(FIRST, LAST)]
    names = COMPOSER_NAMES + rng.sample(combos, count - len(COMPOSER_NAMES))
    rng.shuffle(names)
    return names


def email_for(name, i):
    """Fake, unique email on the reserved example.com domain."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = "".join(c for c in plain.lower() if c.isalnum() or c == " ").replace(" ", ".")
    return f"{slug}.{i}@example.com"


def plan_students(rng):
    """100 Insights students: 25 per band, 13 opted in per band. Returns dicts."""
    students = []
    for band, levels in BANDS.items():
        for k in range(STUDENTS_PER_BAND):
            students.append({"band": band, "level": rng.choice(levels),
                             "opt_in": k < OPTED_IN_PER_BAND, "min_completed": 1})
    rng.shuffle(students)
    return students


def plan_demo_students(rng, count):
    """Demo students: any level, ~50% opt in, may have 0 completed pieces."""
    out = []
    for _ in range(count):
        level = rng.randint(1, 13)
        out.append({"band": band_of(level), "level": level,
                    "opt_in": rng.random() < 0.5, "min_completed": 0})
    return out


def stage_dates(rng, start, piece_level, student_level, lesson_weekday):
    """Dates the piece enters stages 1..6. Each step: 1-3 weeks, slower if harder.

    Stage changes happen at lessons, so each date snaps to the next lesson day.
    """
    harder = max(piece_level - student_level, 0)
    dates, day = [start], start
    for _ in range(5):
        weeks = rng.uniform(1, 3) * (1 + 0.25 * harder)
        day = next_lesson(day + timedelta(days=round(weeks * 7)), lesson_weekday)
        dates.append(day)
    return dates


def plan_pieces(rng, student, pieces_by_level):
    """Completed pieces at the student's level, 1-3 in progress, maybe 1 queued."""
    lvl = student["level"]
    used = set()
    pool = list(pieces_by_level[lvl])
    n_done = rng.randint(max(student["min_completed"], 0), min(2, len(pool)))
    done = rng.sample(pool, n_done)
    used.update(p["id"] for p in done)
    near = [p for l in range(max(lvl - 1, 1), min(lvl + 2, 13) + 1)
            for p in pieces_by_level[l] if p["id"] not in used]
    rest = rng.sample(near, min(len(near), rng.randint(2, 4)))
    in_progress, queued = rest[:3], rest[3:4]
    return done, in_progress, queued


def plan_history(rng, student, done, in_progress, queued):
    """Attach start, stage dates and current stage to each planned piece.

    Completed pieces finished 1-120 days ago. In-progress pieces started part-way
    through their stage timeline, so they have not reached stage 6 yet.
    """
    wd, lvl = student["lesson_weekday"], student["level"]
    rows = []
    for p in done:
        dates = stage_dates(rng, TODAY, p["level"], lvl, wd)
        shift = (dates[5] - dates[0]) + timedelta(days=rng.randint(1, 120))
        dates = [d - shift for d in dates]
        rows.append({"piece": p, "dates": dates})
    for p in in_progress:
        dates = stage_dates(rng, TODAY, p["level"], lvl, wd)
        total = (dates[5] - dates[0]).days
        back = timedelta(days=rng.randint(3, max(total - 7, 4)))
        dates = [d - back for d in dates]
        rows.append({"piece": p, "dates": dates})
    for p in queued:
        rows.append({"piece": p, "dates": None})
    for seq, row in enumerate(rows, start=1):
        row["seq"] = seq
        if row["dates"] is None:                       # assigned, not started
            row["changes"], row["started_on"], row["completed_on"] = [], None, None
            row["stage"] = 1
            continue
        reached = [(i + 1, d) for i, d in enumerate(row["dates"]) if d < TODAY]
        row["changes"] = reached                       # [(stage, date), ...]
        row["stage"] = reached[-1][0]
        row["started_on"] = row["dates"][0]
        row["completed_on"] = row["dates"][5] if row["stage"] == 6 else None
    return rows


def day_weight(shape, days_since_lesson):
    """Practice multiplier for one day, by the student's weekly shape."""
    taper = 1.3 - 0.12 * days_since_lesson
    if shape == "flat":
        return 1.0
    if shape == "taper_cram" and days_since_lesson == 6:
        return 1.6
    return taper


def plan_logs(rng, student, rows):
    """Daily practice for the last 8 weeks, split across in-progress pieces."""
    lo, hi = BAND_MINUTES[student["band"]]
    logs, day = [], WINDOW_START
    while day <= TODAY:
        active = [r for r in rows if r["started_on"] and r["started_on"] <= day
                  and (r["completed_on"] is None or day < r["completed_on"])]
        if active and rng.random() >= SKIP_RATE[student["persona"]]:
            since = (day.weekday() - student["lesson_weekday"]) % 7
            total = max(5, round(rng.randint(lo, hi) * day_weight(student["shape"], since)))
            today_pieces = rng.sample(active, rng.randint(1, min(3, len(active))))
            start = at(day, rng.randint(7, 20), rng.choice([0, 15, 30, 45]))
            for r in today_pieces:
                minutes = max(1, round(total / len(today_pieces) * rng.uniform(0.7, 1.3)))
                if start + timedelta(minutes=minutes) > NOW:
                    break                              # never log the future
                note = rng.choice(LOG_NOTES) if rng.random() < 0.3 else None
                logs.append({"row": r, "started_at": start, "minutes": minutes, "note": note})
                start += timedelta(minutes=minutes + 5)
        day += timedelta(days=1)
    return logs


# ---------- 4. Database helpers ----------
def check_real_data_is_safe(cur):
    """Stop if a real (non-generated) student is in a generated studio.

    Deleting generated users would otherwise change that real row
    (students.studio_id ON DELETE SET NULL).
    """
    cur.execute("""
        SELECT count(*)
        FROM students s
        JOIN users u ON u.id = s.user_id
        JOIN studios st ON st.id = s.studio_id
        JOIN users t ON t.id = st.teacher_id
        WHERE NOT u.is_generated
          AND t.is_generated
    """)
    if cur.fetchone()[0]:
        raise SystemExit("A real student is in a generated studio. Move them first.")


def delete_generated(cur):
    """Remove all generated data. ON DELETE CASCADE removes their rows in every table."""
    cur.execute("DELETE FROM users WHERE is_generated")
    print(f"deleted {cur.rowcount} generated users (and their rows, by cascade)")


def insert_reference(cur):
    """Cities and pieces are real reference data: insert if missing, then read ids."""
    cur.executemany("""
        INSERT INTO cities (name, state, lat, lon)
        VALUES (%s, 'UT', %s, %s)
        ON CONFLICT (name, state) DO NOTHING
    """, CITIES)
    cur.execute("SELECT name, id FROM cities WHERE state = 'UT'")
    city_ids = dict(cur.fetchall())
    cur.execute("SELECT id, sort_order FROM rcm_levels")
    rcm_id = {sort: rid for rid, sort in cur.fetchall()}
    cur.executemany("""
        INSERT INTO pieces (title, composer, rcm_level_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (title, composer) DO NOTHING
    """, [(t, c, rcm_id[lvl]) for t, c, lvl in PIECES])
    pieces_by_level = {lvl: [] for lvl in range(1, 14)}
    for title, composer, lvl in PIECES:
        cur.execute("SELECT id FROM pieces WHERE title = %s AND composer = %s", (title, composer))
        pieces_by_level[lvl].append({"id": cur.fetchone()[0], "level": lvl, "title": title})
    return city_ids, pieces_by_level


def insert_user(cur, name, email, role, pw_hash):
    """Insert one generated user and return its id."""
    cur.execute("""
        INSERT INTO users (email, password_hash, display_name, role, is_generated)
        VALUES (%s, %s, %s, %s, true)
        RETURNING id
    """, (email, pw_hash, name, role))
    return cur.fetchone()[0]


def new_join_code(cur):
    """Unused 6-digit studio join code, e.g. '048213'. Uses `secrets`, like share tokens."""
    while True:
        code = f"{secrets.randbelow(1_000_000):06d}"        # keeps leading zeros
        cur.execute("SELECT 1 FROM studios WHERE join_code = %s", (code,))
        if cur.fetchone() is None:
            return code


def insert_teacher(cur, rng, name, email, city_id, studio_name, pw_hash):
    """Teacher user + studio + preset level tags + extra tags + templates."""
    teacher_id = insert_user(cur, name, email, "teacher", pw_hash)
    join_code = new_join_code(cur)
    cur.execute("""
        INSERT INTO studios (teacher_id, city_id, name, join_code)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (teacher_id, city_id, studio_name, join_code))
    if email.startswith("demo."):
        print(f"join code for {email}: {join_code}")
    studio_id = cur.fetchone()[0]
    tags = {}
    # (name, applies_to, color, is_preset): level tags + the 3 defaults are locked presets
    tag_rows = ([(level_tag_name(s), "student", LEVEL_TAG_COLOR, True) for s in range(1, 14)]
                + [(n, "student", LEVEL_TAG_COLOR, True) for n in PRESET_STUDENT_TAGS]
                + [(n, "student", c, False) for n, c in EXTRA_STUDENT_TAGS]
                + [(n, "piece", c, False) for n, c in PIECE_TAGS])
    for tag_name, applies_to, color, is_preset in tag_rows:
        cur.execute("""
            INSERT INTO tags (teacher_id, name, applies_to, color, is_preset)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (teacher_id, tag_name, applies_to, color, is_preset))
        tags[tag_name] = cur.fetchone()[0]
    templates = []
    for title, body in TEMPLATES:
        cur.execute("""
            INSERT INTO assignment_templates (teacher_id, title, body)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (teacher_id, title, body))
        templates.append((cur.fetchone()[0], title, body))
    return {"user_id": teacher_id, "studio_id": studio_id, "tags": tags, "templates": templates}


def insert_student(cur, rng, s, teacher, pieces_by_level, pw_hash, demo):
    """One student: user, student row, tags, pieces + stage history, logs, notes."""
    s["user_id"] = insert_user(cur, s["name"], s["email"], "student", pw_hash)
    cur.execute("""
        INSERT INTO students
          (user_id, studio_id, parent_email, insights_opt_in, weekly_goal_minutes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (s["user_id"], teacher["studio_id"], f"parent.{s['email']}", s["opt_in"],
          s["weekly_goal"]))
    student_id = s["student_id"] = cur.fetchone()[0]

    if s["tagged"]:
        cur.execute("INSERT INTO student_tags (student_id, tag_id) VALUES (%s, %s)",
                    (student_id, teacher["tags"][level_tag_name(s["level"])]))
    if rng.random() < 0.2:
        name, _ = rng.choice(EXTRA_STUDENT_TAGS)
        cur.execute("INSERT INTO student_tags (student_id, tag_id) VALUES (%s, %s)",
                    (student_id, teacher["tags"][name]))

    done, in_progress, queued = plan_pieces(rng, s, pieces_by_level)
    rows = plan_history(rng, s, done, in_progress, queued)
    for r in rows:
        # Insert the piece with its FINAL stage, and its full stage history, in the
        # same transaction (the whole run is one transaction), so they always agree.
        cur.execute("""
            INSERT INTO student_pieces
              (student_id, piece_id, seq_order, current_stage_id, started_on, completed_on)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (student_id, r["piece"]["id"], r["seq"], r["stage"],
              r["started_on"], r["completed_on"]))
        r["id"] = cur.fetchone()[0]
        cur.executemany("""
            INSERT INTO stage_changes
              (student_piece_id, from_stage_id, to_stage_id, changed_by, changed_at)
            VALUES (%s, %s, %s, %s, %s)
        """, [(r["id"], stage - 1 if stage > 1 else None, stage, teacher["user_id"],
               at(day, 16)) for stage, day in r["changes"]])

    logs = plan_logs(rng, s, rows)
    cur.executemany("""
        INSERT INTO practice_logs (student_piece_id, started_at, minutes, note)
        VALUES (%s, %s, %s, %s)
    """, [(l["row"]["id"], l["started_at"], l["minutes"], l["note"]) for l in logs])

    last_lesson = TODAY - timedelta(days=(TODAY.weekday() - s["lesson_weekday"]) % 7)
    for r in rows:
        if r["started_on"] and r["completed_on"] is None:
            tid, title, body = rng.choice(teacher["templates"])
            cur.execute("""
                INSERT INTO assignments
                  (student_piece_id, template_id, title, body, minutes_per_day, assigned_on, due_on)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (r["id"], tid, title, body, BAND_MINUTES[s["band"]][0],
                  last_lesson, last_lesson + timedelta(days=7)))

    if demo:
        lesson = next_lesson(WINDOW_START, s["lesson_weekday"])
        notes = []
        while lesson <= TODAY:
            notes.append((student_id, lesson, rng.choice(LESSON_NOTES)))
            lesson += timedelta(days=7)
        cur.executemany("""
            INSERT INTO lesson_notes (student_id, lesson_date, body)
            VALUES (%s, %s, %s)
        """, notes)

    for r in rng.sample(rows, min(2, len(rows))):
        if rng.random() < 0.3:
            tag_name, _ = rng.choice(PIECE_TAGS)
            cur.execute("""
                INSERT INTO piece_tags (piece_id, tag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (r["piece"]["id"], teacher["tags"][tag_name]))
    return logs


def insert_solo_student(cur, pw_hash):
    """One Student Solo login (studio_id NULL) so the invite-accept flow can be demoed."""
    user_id = insert_user(cur, "Solo Sammy Sightreader", SOLO_EMAIL, "student", pw_hash)
    cur.execute("""
        INSERT INTO students (user_id, studio_id, insights_opt_in, weekly_goal_minutes)
        VALUES (%s, NULL, false, %s)
    """, (user_id, 150))


def insert_demo_extras(cur, teacher, student):
    """Pending invites + one share link for demo studio 1, so both can be demoed.

    The token comes from `secrets`, not the seeded rng: the seed is in a public
    repo, so a seeded token could be recomputed by anyone.
    """
    cur.executemany("""
        INSERT INTO invites (studio_id, email)
        VALUES (%s, %s)
    """, [(teacher["studio_id"], email) for email in DEMO_INVITES])
    token = secrets.token_urlsafe(32)                       # 43 characters
    monday = TODAY - timedelta(days=TODAY.weekday())
    cur.execute("""
        INSERT INTO share_links (student_id, created_by, token, week_start)
        VALUES (%s, %s, %s, %s)
    """, (student["student_id"], teacher["user_id"], token, monday))
    print(f"share link for {student['name']}: /share/{token}")


# ---------- 5. Messy CSV for Thursday's cleaning notebook ----------
def write_messy_csv(rng, all_logs):
    """Copy of generated logs with deliberate problems. The database stays clean."""
    MESSY_CSV.parent.mkdir(exist_ok=True)
    rows = [{"source": "generated", "student_email": l["email"],
             "piece_title": l["row"]["piece"]["title"],
             "started_at": l["started_at"].isoformat(), "minutes": str(l["minutes"]),
             "note": l["note"] or ""} for l in all_logs]
    for r in rng.sample(rows, len(rows) // 50):
        rows.append(dict(r))                                # duplicates (~2%)
    for r in rng.sample(rows, len(rows) // 50):
        r["minutes"] = ""                                   # missing values
    for r in rng.sample(rows, len(rows) // 50):
        r["minutes"] = f"{r['minutes'] or 30} min"          # text in a number column
    for r in rng.sample(rows, len(rows) // 100):
        r["piece_title"] = ""                               # missing piece
    rng.choice(rows)["minutes"] = "600"                     # outlier
    rng.shuffle(rows)
    with MESSY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {MESSY_CSV}")


# ---------- 6. Checks (run inside the transaction: a failure rolls everything back) ----------
CHECKS = {
    "logs in the future": """
        SELECT count(*) FROM practice_logs WHERE started_at > now()""",
    "logs before their piece started": """
        SELECT count(*)
        FROM practice_logs pl
        JOIN student_pieces sp ON sp.id = pl.student_piece_id
        WHERE pl.started_at::date < sp.started_on""",
    "newest stage change != current stage": """
        SELECT count(*)
        FROM student_pieces sp
        JOIN LATERAL (
          SELECT to_stage_id
          FROM stage_changes sc
          WHERE sc.student_piece_id = sp.id
          ORDER BY sc.changed_at DESC, sc.id DESC
          LIMIT 1
        ) last ON true
        WHERE last.to_stage_id <> sp.current_stage_id""",
    "generated students without a weekly goal": """
        SELECT count(*)
        FROM students s
        JOIN users u ON u.id = s.user_id
        WHERE u.is_generated
          AND s.weekly_goal_minutes IS NULL""",
    "generated users without @example.com": """
        SELECT count(*) FROM users WHERE is_generated AND email NOT LIKE '%@example.com'""",
}


def run_checks(cur, insights_students):
    """Print row counts and assert every rule from spec section 8."""
    for table in ["cities", "users", "studios", "students", "pieces", "tags",
                  "student_pieces", "stage_changes", "practice_logs",
                  "assignment_templates", "assignments", "lesson_notes",
                  "student_tags", "piece_tags", "invites", "share_links"]:
        cur.execute(f"SELECT count(*) FROM {table}")   # table names are ours, not user input
        print(f"{table:22} {cur.fetchone()[0]:>6}")
    for name, sql in CHECKS.items():
        cur.execute(sql)
        bad = cur.fetchone()[0]
        assert bad == 0, f"check failed: {name} ({bad} rows)"
    for band in BANDS:
        n = sum(1 for s in insights_students if s["band"] == band and s["opt_in"])
        assert n >= 12, f"band {band} has only {n} opted-in students"
    print("all checks passed")


# ---------- 7. Main ----------
def main():
    """Plan, delete old generated data, insert new data, check, commit."""
    load_dotenv()
    rng = random.Random(SEED)
    pw_hash = generate_password_hash(os.environ["DEMO_PASSWORD"])  # one hash, reused

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.transaction():
            cur = conn.cursor()
            check_real_data_is_safe(cur)
            delete_generated(cur)
            city_ids, pieces_by_level = insert_reference(cur)

            demo = plan_demo_students(rng, 12)
            insights = plan_students(rng)
            names = make_names(rng, 10 + len(demo) + len(insights))
            for i, s in enumerate(demo + insights):
                s["name"] = names[10 + i]
                s["email"] = email_for(s["name"], i)
                s["tagged"] = rng.random() < TAGGED_SHARE
                s["persona"] = rng.choice(list(SKIP_RATE))
                s["shape"] = rng.choice(SHAPES)
                s["lesson_weekday"] = rng.randrange(0, 6)   # Mon-Sat
                lo, hi = WEEKLY_GOAL[s["band"]]
                s["weekly_goal"] = rng.randrange(lo, hi + 1, 30)   # steps of 30 min

            teacher_specs = [("demo.teacher1@example.com", "Salt Lake City", demo[:8]),
                             ("demo.teacher2@example.com", "Provo", demo[8:])]
            cities = [c[0] for c in CITIES]
            for k in range(8):                               # 8 extra studios, 12-13 students
                chunk = insights[k * 100 // 8:(k + 1) * 100 // 8]
                teacher_specs.append((None, cities[k % len(cities)], chunk))

            insert_solo_student(cur, pw_hash)
            all_logs = []
            for k, (email, city, students) in enumerate(teacher_specs):
                tname = names[k]
                teacher = insert_teacher(cur, rng, tname, email or email_for(tname, 1000 + k),
                                         city_ids[city], f"{tname.split()[-1]} Piano Studio",
                                         pw_hash)
                for s in students:
                    for log in insert_student(cur, rng, s, teacher, pieces_by_level,
                                              pw_hash, demo=email is not None):
                        log["email"] = s["email"]
                        all_logs.append(log)
                if k == 0:                                   # demo teacher 1
                    insert_demo_extras(cur, teacher, students[0])

            run_checks(cur, insights)
        # leaving the `with conn.transaction()` block without an error = COMMIT
    write_messy_csv(rng, all_logs)


if __name__ == "__main__":
    main()