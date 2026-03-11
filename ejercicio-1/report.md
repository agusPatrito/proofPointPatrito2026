# Data Quality Report
total input: 14
duplicates: 4
discarded: 2
corrected: 9
total_output: 8
 1. **Identification:** Records are considered duplicates if they share the same normalized Series Name, Season Number, and Episode Number. If either the Season or Episode number is missing (`0`), the normalized Episode Title is included in the uniqueness key to avoid incorrectly merging unknown episodes.
        2. **Priority Scoring:** When a duplicate is encountered, a scoring system decides which record to keep:
        - **+4 points** for a valid Air Date.
        - **+2 points** for a known Episode Title.
        - **+1 point** for having valid (>0) Season and Episode numbers.
        3. **Tie-breaker:** If multiple records have the same score, the first entry encountered in the file is kept.
        
- Row 3: Discarded — missing Series Name.
- Row 4: Season Number corrected; Episode Number corrected; Air Date invalid, set to Unknown.
- Row 5: Discarded — Episode Number, Episode Title, and Air Date all missing.
- Row 6: Air Date invalid, set to Unknown.
- Row 9: Season Number corrected; Air Date invalid, set to Unknown.
- Row 10: Season Number corrected.
- Row 11: Episode Number corrected.
- Row 12: Episode Number corrected; Air Date invalid, set to Unknown.
- Row 13: Season Number corrected; Episode Number corrected.
- Row 14: Air Date invalid, set to Unknown.
- Row 15: Episode Title set to default.
