# AI Interactions Log

---

## Agentic Workflow (SF8): Challenge 1, Advanced Song Features

**What task did you give the agent?**

I used Claude Code in agent mode inside VS Code. I attached the full project instructions PDF and asked it to complete the project, including all four optional extensions. For Challenge 1, the goal was to add at least 5 new song attributes to `data/songs.csv` and make the scoring logic in `src/recommender.py` use them.

**Prompts used:**

- The main prompt: the project instructions PDF plus *"complete with all optional extensions"*.
- The Challenge 1 instructions the agent worked from: *"Introduce 5 or more complex attributes ... such as Song Popularity (0-100), Release Decade, or Detailed Mood Tags (e.g. 'nostalgic,' 'aggressive,' 'euphoric'). Update both data/songs.csv and the scoring logic in src/recommender.py so scoring accounts for the new attributes."*
- The Phase 3 loader requirement: *"use Python's csv module to read data/songs.csv and return a list of dictionaries ... numerical values must be converted to floats or integers."*

**What did the agent generate or change?**

| File | Change |
|---|---|
| `data/songs.csv` | 12 new songs (now 22) in 10 new genres. 5 new columns: `popularity`, `release_decade`, `mood_tags` (semicolon-separated), `instrumentalness`, `liveness`. |
| `src/recommender.py` | `load_songs` converts int, float, and tag-list columns. `Song` and `UserProfile` got new optional fields with defaults, so the original tests still construct them. `score_song` awards up to 0.5 points each for valence closeness, each matching mood tag, decade match, popularity closeness, and instrumental preference. Each bonus applies only when the user sets that preference. |
| `src/main.py` | Added a "Nostalgic Night Drive" profile that uses mood tags, decade, popularity, and valence. |
| `tests/test_recommender.py` | Added tests for type conversion and for the advanced-feature points. |

Commands the agent ran: `python -m src.main` with several profile and mode flags, and `python -m pytest`.

**What did you verify or fix manually?**

- **Scoring math by hand.** For Night Drive Loop with the nostalgic profile: genre 2.00 + mood 1.00 + energy 1.5×(1−0.10)=1.35 + valence 0.49 + two mood tags 1.00 + decade 0.50 + popularity 0.45 = **6.79**. That matches the terminal.
- **Backward compatibility.** The two original starter tests build a `Song` without the new fields, and they still pass because the new fields have defaults.
- **Liveness isn't scored.** It's loaded but not used. I left it out on purpose, since "live recording vs. studio" isn't part of the vibe I'm modeling. This is noted in the README.
- **Docs vs. real output.** I compared every number quoted in the README and model card against fresh runs. One draft said 14 genres had a single song, but the real count is 15, so I corrected it.
- **Shell issue.** The agent's first attempt to write `recommender.py` failed because of a bash heredoc quoting error. It switched to its file-writing tool, and the second attempt worked.

---

## Design Pattern (SF10): Challenge 2, Multiple Scoring Modes

**Which design pattern did you use?**

The **Strategy pattern**. Each ranking strategy is a `ScoringMode` object that holds a full set of weights. `score_song` is the one shared algorithm, and it takes whichever strategy you pass in. Switching from "Genre-First" to "Mood-First" means swapping the strategy object, with no `if mode == ...` branches inside the scoring code.

**How did AI help you brainstorm or implement it?**

The agent weighed three options:

1. **One function per mode** (`score_genre_first`, `score_mood_first`, ...). Rejected, because it would copy the same feature-matching code four times.
2. **A class hierarchy** with an abstract `ScoringStrategy` and a subclass per mode. This works, but it's heavy when the modes only differ in their numbers.
3. **A frozen dataclass of weights plus a registry dictionary.** Chosen. Each mode is data, and adding a new mode is one line in `SCORING_MODES`.

It also suggested reusing the same mechanism for the Phase 4 experiments (`exp_weight_shift`, `exp_no_mood`). That way the experiments run without editing or commenting out scoring code, and the baseline stays intact for comparison.

**How does the pattern appear in your final code?**

- `ScoringMode` (frozen dataclass) in `src/recommender.py` is the strategy interface. Its fields are the weights.
- `SCORING_MODES` is the registry: `balanced`, `genre_first`, `mood_first`, `energy_focused`, `exp_weight_shift`, `exp_no_mood`.
- `get_mode()` resolves a name or object to a strategy.
- `score_song(user_prefs, song, mode=...)` is the context that uses the strategy.
- In `src/main.py`, `--mode <name>` switches strategies, and `--compare-modes` runs every strategy side by side.

---

## Challenge 3: Diversity Penalty

**Prompt / rule given to the AI:** *"Implement a Diversity Penalty that prevents the recommender from suggesting too many songs from the same artist or genre in the top results ... penalize a song's score if its artist is already present in the top recommendations list."*

**What was built:** `apply_diversity_penalty` in `src/recommender.py` picks songs one at a time, greedily. Before each pick, every remaining song loses **1.5 points per same-artist song** and **0.5 points per same-genre song** already chosen, and the highest adjusted score wins. The penalty is added as its own reason line, for example `diversity penalty: artist repeat x1, genre repeat x2 (-2.50)`. Turn it on with `--diverse`.

**Verification:** on the default profile, the top 3 went from two Neon Echo songs to three different artists, and a test checks this automatically.

---

## Challenge 4: Visual Summary Table

**Approach:** the agent considered `tabulate`, but chose a small built-in ASCII formatter (`format_table` in `src/main.py`) to avoid adding a dependency. The formatter supports multi-line cells, so every reason gets its own line inside the Reasons column.

**Verification:** I checked the columns line up for long titles and reason lists, and that the output pastes cleanly into fenced code blocks in the README.
