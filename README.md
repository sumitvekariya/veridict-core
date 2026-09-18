# Veridict

Verification evidence for AI-written code, stored in git.

Every check a repository runs becomes a signed attestation bound to the
commit, kept in a git notes ref, demanded by a policy file, and verifiable
from any clone with no forge involved. See `specs/mission.md`.

Status: MVP in progress. Apache-2.0.
