-- LedgerLine schema (PostgreSQL on Supabase)
-- Base: Lucidchart ERD export, then hand-edited: identity ids, defaults, CHECKs,
-- inline FKs with explicit ON DELETE rules, composite UNIQUEs, updated_at trigger, lookup seeds.
-- Order matters: every table is created after the tables it references.

-- ---------- Lookup tables (ids chosen by us, not generated) ----------

CREATE TABLE rcm_levels (
  id         smallint PRIMARY KEY,
  name       text NOT NULL UNIQUE,
  sort_order smallint NOT NULL UNIQUE
);

CREATE TABLE stages (
  id       smallint PRIMARY KEY,
  name     text NOT NULL UNIQUE,
  position smallint NOT NULL UNIQUE CHECK (position BETWEEN 1 AND 6)
);

CREATE TABLE cities (
  id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name  text NOT NULL,
  state char(2) NOT NULL CHECK (state ~ '^[A-Z]{2}$'),
  lat   numeric(8,5) NOT NULL CHECK (lat BETWEEN -90 AND 90),
  lon   numeric(8,5) NOT NULL CHECK (lon BETWEEN -180 AND 180),
  UNIQUE (name, state)
);

-- ---------- People and studios ----------

CREATE TABLE users (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email         text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  display_name  text NOT NULL,
  role          text NOT NULL CHECK (role IN ('teacher', 'student')),
  is_generated  boolean NOT NULL DEFAULT false,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE studios (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  teacher_id bigint NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  city_id    integer NOT NULL REFERENCES cities(id) ON DELETE RESTRICT,
  name       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE students (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id         bigint NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  studio_id       bigint REFERENCES studios(id) ON DELETE SET NULL,  -- NULL = Student Solo
  parent_email    text CHECK (parent_email LIKE '%@%'),
  parent_phone    text,
  insights_opt_in boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

-- ---------- Repertoire ----------

CREATE TABLE pieces (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title        text NOT NULL,
  composer     text NOT NULL DEFAULT 'Unknown',
  rcm_level_id smallint REFERENCES rcm_levels(id) ON DELETE RESTRICT,
  henle_level  smallint CHECK (henle_level BETWEEN 1 AND 9),
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (title, composer)
);

CREATE TABLE student_pieces (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  student_id       bigint NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  piece_id         bigint NOT NULL REFERENCES pieces(id) ON DELETE RESTRICT,
  seq_order        integer NOT NULL CHECK (seq_order > 0),
  current_stage_id smallint NOT NULL REFERENCES stages(id) ON DELETE RESTRICT,
  started_on       date,
  completed_on     date CHECK (completed_on >= started_on),
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (student_id, piece_id),
  UNIQUE (student_id, seq_order) DEFERRABLE INITIALLY DEFERRED
);

-- Append-only history: rows are never edited, so no updated_at.
-- Intentional duplicate: the newest row here must match student_pieces.current_stage_id
-- (Flask updates both in one transaction).
CREATE TABLE stage_changes (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  student_piece_id bigint NOT NULL REFERENCES student_pieces(id) ON DELETE CASCADE,
  from_stage_id    smallint REFERENCES stages(id) ON DELETE RESTRICT,  -- NULL = first stage set
  to_stage_id      smallint NOT NULL REFERENCES stages(id) ON DELETE RESTRICT,
  changed_by       bigint REFERENCES users(id) ON DELETE SET NULL,
  changed_at       timestamptz NOT NULL DEFAULT now(),
  CHECK (from_stage_id <> to_stage_id)
);

CREATE TABLE practice_logs (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  student_piece_id bigint NOT NULL REFERENCES student_pieces(id) ON DELETE CASCADE,
  started_at       timestamptz NOT NULL,
  minutes          integer NOT NULL CHECK (minutes > 0),
  note             text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

-- ---------- Assignments and notes ----------

CREATE TABLE assignment_templates (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  teacher_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title      text NOT NULL,
  body       text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Loading a template COPIES title/body here; template_id only records where it came from.
CREATE TABLE assignments (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  student_piece_id bigint NOT NULL REFERENCES student_pieces(id) ON DELETE CASCADE,
  template_id      bigint REFERENCES assignment_templates(id) ON DELETE SET NULL,
  title            text NOT NULL,
  body             text,
  minutes_per_day  integer CHECK (minutes_per_day > 0),
  assigned_on      date NOT NULL DEFAULT CURRENT_DATE,
  due_on           date,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  CHECK (due_on >= assigned_on)
);

CREATE TABLE lesson_notes (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  student_id  bigint NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  lesson_date date NOT NULL DEFAULT CURRENT_DATE,
  body        text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- ---------- Tags ----------

CREATE TABLE tags (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  teacher_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name       text NOT NULL,
  applies_to text NOT NULL CHECK (applies_to IN ('student', 'piece')),
  color      text NOT NULL CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (teacher_id, name, applies_to)
);

-- Junction tables: rows are only inserted or deleted, never updated, so no updated_at.
-- Flask must check: tag.applies_to matches, and the tag belongs to the student's teacher.
CREATE TABLE student_tags (
  student_id bigint NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  tag_id     bigint NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (student_id, tag_id)
);

CREATE TABLE piece_tags (
  piece_id   bigint NOT NULL REFERENCES pieces(id) ON DELETE CASCADE,
  tag_id     bigint NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (piece_id, tag_id)
);

-- ---------- updated_at trigger ----------
-- One function, reused by every table that has updated_at.
CREATE FUNCTION set_updated_at() RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER users_set_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER studios_set_updated_at BEFORE UPDATE ON studios
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER students_set_updated_at BEFORE UPDATE ON students
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER pieces_set_updated_at BEFORE UPDATE ON pieces
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER student_pieces_set_updated_at BEFORE UPDATE ON student_pieces
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER practice_logs_set_updated_at BEFORE UPDATE ON practice_logs
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER assignment_templates_set_updated_at BEFORE UPDATE ON assignment_templates
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER assignments_set_updated_at BEFORE UPDATE ON assignments
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER lesson_notes_set_updated_at BEFORE UPDATE ON lesson_notes
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER tags_set_updated_at BEFORE UPDATE ON tags
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- Lookup seed rows (real data, not generated) ----------

INSERT INTO stages (id, name, position) VALUES
  (1, 'learning notes',          1),
  (2, 'slow speed',              2),
  (3, 'articulation + details',  3),
  (4, 'up to tempo',             4),
  (5, 'polished',                5),
  (6, 'performance ready',       6);

INSERT INTO rcm_levels (id, name, sort_order) VALUES
  (1,  'Prep A',    1),
  (2,  'Prep B',    2),
  (3,  'Level 1',   3),
  (4,  'Level 2',   4),
  (5,  'Level 3',   5),
  (6,  'Level 4',   6),
  (7,  'Level 5',   7),
  (8,  'Level 6',   8),
  (9,  'Level 7',   9),
  (10, 'Level 8',  10),
  (11, 'Level 9',  11),
  (12, 'Level 10', 12),
  (13, 'ARCT',     13);

-- ---------- Lock the Supabase Data API ----------
-- Flask connects as the table owner (pooler string), which bypasses RLS.
-- RLS with no policies blocks the public anon key from reading/writing any row
-- (e.g. users.password_hash, parent emails). Never disable this.
ALTER TABLE rcm_levels           ENABLE ROW LEVEL SECURITY;
ALTER TABLE stages               ENABLE ROW LEVEL SECURITY;
ALTER TABLE cities               ENABLE ROW LEVEL SECURITY;
ALTER TABLE users                ENABLE ROW LEVEL SECURITY;
ALTER TABLE studios              ENABLE ROW LEVEL SECURITY;
ALTER TABLE students             ENABLE ROW LEVEL SECURITY;
ALTER TABLE pieces               ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_pieces       ENABLE ROW LEVEL SECURITY;
ALTER TABLE stage_changes        ENABLE ROW LEVEL SECURITY;
ALTER TABLE practice_logs        ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments          ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_notes         ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_tags         ENABLE ROW LEVEL SECURITY;
ALTER TABLE piece_tags           ENABLE ROW LEVEL SECURITY;