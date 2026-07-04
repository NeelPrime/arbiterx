# ArbiterX Review

Review the current diff (or specified files) against the 10 engineering arbiterxs.

## Instructions

1. Look at the git diff or specified files
2. Check each one against:
   - YAGNI: Is there anything built that wasn't asked for?
   - Error handling: Are all I/O operations protected?
   - Type safety: Are all functions typed?
   - Resource cleanup: Are all resources properly closed?
   - Magic numbers: Are there inline numeric literals?
   - Dead code: Unused imports, commented code?
   - Single responsibility: Functions over 30 lines?
   - Fail fast: Late validation?
   - Performance: O(n²) patterns, string concat in loops?
   - Security: Hardcoded secrets, SQL injection, eval?

3. Output a table:

| File | Issue | ArbiterX | Severity | Fix |
|------|-------|-------|----------|-----|

4. Give an overall score (0-100) and pass/fail (threshold: 70)

Be specific. Point to exact lines. Suggest the minimal fix.
