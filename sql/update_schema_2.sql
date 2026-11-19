-- Migration 003: every account email is stored lowercase (approved by Theo, Thu Nov 19)
-- Why: invites.email is already forced lowercase; this makes invites always match users.email.
-- Flask must call .strip().lower() on the email at signup and login.
-- Checked before writing: 0 existing users have uppercase letters in their email.
BEGIN;

ALTER TABLE users
  ADD CONSTRAINT users_email_lowercase CHECK (email = lower(email));

COMMIT;
