# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

**Goal / task.** VibeFinder suggests the top 5 songs from a small catalog that best fit one listener's stated taste. It predicts "how well does this song match what you said you like?" and shows the reasons behind every score.

**Who it's for.** It is a classroom simulation for learning how recommenders turn data into rankings. It is not built for real listeners.

**Assumptions it makes about the user:**
- The user can describe their taste with one favorite genre, one favorite mood, and a target energy level.
- Their taste does not change with time of day, activity, or what they just listened to.
- Labels in the catalog (like "chill" or "pop") mean the same thing to everyone.

**Intended use:**
- Learning and teaching how content-based scoring and ranking work.
- Experimenting with weights, modes, and fairness rules to see how results change.

**Not intended for:**
- Real music apps or real users' listening decisions.
- Judging the quality or worth of any genre, artist, or song.
- Any decision about people, such as profiling listeners by mood or targeting ads.

---

## 3. How the Model Works

**Algorithm summary, in plain language.** Imagine a judge with a scorecard looking at one song at a time:

- If the song is the user's favorite genre, it gets **2 points**.
- If the song has the user's favorite mood, it gets **1 point**.
- Energy closeness is worth **up to 1.5 points**. A song with exactly the energy the user wants gets all 1.5 points. A song that is a little off gets a bit less. A song at the opposite extreme gets almost nothing. Being "close" matters, not being "high".
- Small bonuses of **up to 0.5 points each** are optional. They cover an acoustic vs. electric sound, an instrumental vs. vocal sound, a happy vs. dark feel (valence), each matching detailed mood tag like "nostalgic", the right decade, and similar popularity.

The judge writes down every point it gives as a "reason". After every song has a score, the songs are sorted from highest to lowest, and the top 5 are shown.

**Changes from the starter logic:**
- I added 5 new song attributes and used 4 of them in scoring.
- I added **scoring modes**: balanced, genre-first, mood-first, and energy-focused. Each is a different set of weights you can swap in.
- I added an optional **diversity rule**. When picking the top 5, a song loses 1.5 points if its artist is already in the list, and 0.5 points for each song of its genre already picked.

---

## 4. Data

**Data used:**
- **22 songs.** The starter file had 10. I added 12 to cover genres and moods that were missing.
- **17 genres:** pop (4 songs), lofi (3), and 1 song each of rock, ambient, jazz, synthwave, indie pop, hip hop, classical, metal, country, r&b, reggae, edm, folk, blues, and latin.
- **Moods:** happy, chill, intense, relaxed, moody, focused, confident, melancholic, angry, nostalgic, romantic, euphoric, and sad.
- **Features per song:** genre, mood, energy, tempo, valence, danceability, acousticness, popularity (0 to 100), release decade, mood tags, instrumentalness, and liveness.

**Limits of the data:**
- Every song is fictional, and the numbers were made up for the class. They are not measured from real audio.
- Pop and lofi have several songs, while most genres have exactly one.
- Each song has exactly one genre and one mood. Real songs blend styles.
- Lyrics, language, culture, region, and what the song *means* to people are all missing.
- The catalog has no high-energy sad song and no high-energy acoustic song, so some tastes simply can't be satisfied.

---

## 5. Strengths

- **Clear, single-style profiles work well.** Pop/Happy, Chill Lofi, and Deep Intense Rock all get the songs I would pick myself at the top.
- **Energy closeness works as intended.** The Chill Lofi user gets quiet songs, not loud ones, even outside lofi. Spacewalk Thoughts (ambient) and Moonlit Sonata (classical) fill in the list sensibly.
- **Every result is explainable.** The reasons column shows exactly where each point came from, so surprises are easy to debug.
- **The advanced features help niche users.** The Nostalgic Night Drive profile gets Night Drive Loop at 6.79 points. That is far ahead of everything else, because it matches genre, mood, both mood tags, and the 1980s.

---

## 6. Limitations and Bias

**Main weakness: the genre bonus creates a filter bubble that favors listeners of well-stocked genres.** A genre match is worth 2 points, more than mood and more than a perfect energy match. Pop has 4 songs and lofi has 3, while 15 genres have only one. So a pop fan gets a full top 5 of strong matches, but an edm, blues, or metal fan gets one good song followed by filler that only matches on energy. When a user's wishes conflict, genre silently wins. The "sad but hyped" user asked for sad, high-energy edm and got the euphoric edm song first. The genuinely sad songs were ranked below it. Genre matching is also exact, so a "k-pop" fan gets zero genre points from anything, and "indie pop" counts as a total miss for a "pop" fan.

**Other patterns I observed:**
- **Gym Hero shows up for Happy Pop listeners.** It is pop and high-energy, so it collects 2 genre points plus about 1.3 energy points. That beats every non-pop song even though its mood is "intense". With the mood check turned off, it tied for first place.
- **Some preferences are nearly powerless.** The acoustic-loving metalhead got about 0.01 acoustic points, because every high-energy song in the catalog is electric. The preference is technically "used" but changes nothing.
- **Artist repetition.** Without the diversity rule, Neon Echo appears twice in the Pop/Happy top 3.
- **Energy-only users get the "middle".** With no genre or mood, songs near 0.5 energy win no matter their style, from r&b to blues to lofi.

---

## 7. Evaluation

**Profiles tested** (full terminal output is in the README):

| Profile | Type | Top result |
|---|---|---|
| Default Pop/Happy | core | Sunrise City (4.47) |
| High-Energy Pop | core | Neon Heartbeat (4.93) |
| Chill Lofi | core | Library Rain (5.38) |
| Deep Intense Rock | core | Storm Runner (4.93) |
| Nostalgic Night Drive | advanced features | Night Drive Loop (6.79) |
| Sad but Hyped (edm, sad, 0.9) | edge case | Laser Bloom (3.42), not sad |
| Genre not in catalog (k-pop) | edge case | Golden Hour Drive (2.35) |
| Acoustic-loving Metalhead | edge case | Iron Tempest (4.49) |
| Energy only (0.5) | edge case | Velvet Hours (1.47) |

**What I looked for.** I checked whether the top results "felt right" for each profile. I checked whether one song showed up everywhere, and whether conflicting requests were handled sensibly.

**Did it feel right?** For Pop/Happy, yes. Sunrise City, Neon Heartbeat, and Golden Hour Drive are all upbeat pop, which is what I'd queue up. Gym Hero at #4 felt a little off, because it's a workout song, not a happy one.

**Why did Sunrise City rank first?** It matched pop (+2.00) and happy (+1.00), and its energy of 0.82 is almost exactly the 0.80 target (+1.47). Neon Heartbeat matched the same labels but its energy of 0.88 is a bit further away, so it lost by 0.09.

**What surprised me:**
- How much a single weight decides conflicts. The sad-but-hyped user's result flipped from euphoric edm to slow blues just by switching from balanced to mood-first mode.
- Gym Hero and Neon Heartbeat appear in the Deep Intense Rock list, because they are loud. To the system, "loud" looks like "rock".
- The k-pop fan still got reasonable happy songs, but only because mood and energy rescued them.

**Pairwise comparisons:**
- **Pop/Happy vs. High-Energy Pop:** the same songs fill the top 5, but Neon Heartbeat (energy 0.88) overtakes Sunrise City (0.82). The target moved from 0.8 to 0.9, and the "produced sound" bonus slightly favors less acoustic tracks. This makes sense: the same taste, turned up.
- **Pop/Happy vs. Chill Lofi:** there is no overlap at all. Pop/Happy gets bright, 0.7 to 0.9 energy pop, while Chill Lofi gets quiet 0.2 to 0.4 energy tracks with high acousticness. This shows that energy closeness plus genre cleanly separates "party" from "study" music.
- **Pop/Happy vs. Deep Intense Rock:** Gym Hero appears in both lists. In Pop/Happy it gets in through the genre bonus, while in Rock it gets in through the "intense" mood and high energy. A single song can sit on the border of two tastes.
- **High-Energy Pop vs. Deep Intense Rock:** both want energy around 0.9 and an electric sound, so Neon Heartbeat and Gym Hero appear in both. What separates them is only the genre and mood labels, not how the songs sound.
- **High-Energy Pop vs. Chill Lofi:** these are opposites in everything. Lofi results are acoustic and instrumental, pop results are produced and vocal. This is a good sanity check that the acoustic and instrumental preferences push in the right directions.
- **Chill Lofi vs. Deep Intense Rock:** there is no overlap. Rock's #1 has energy 0.91 and lofi's has 0.35, which is the "intense rock vs. chill lofi" test from Phase 2, and the profiles pass it.
- **Nostalgic Night Drive vs. Pop/Happy:** Golden Hour Drive appears in both, because its "nostalgic" mood tag earns points for the night-drive user even though it's a happy pop song. Mood tags let songs cross genre lines.
- **Sad but Hyped vs. Acoustic Metalhead:** both have conflicting wishes. The sad-hyped user loses their mood, and the metalhead loses their acoustic preference. In both cases genre and energy win, which shows that the weaker preferences give way first.
- **k-pop vs. Energy only:** both lack a genre match. The k-pop user still gets happy songs because mood is set, while the energy-only user gets a random-feeling mix of mid-energy songs. This shows how much the labels do.

**Experiments run** (details and output in the README):
1. **Weight shift** (energy ×2, genre ÷2) changed results without making them more accurate. Gym Hero almost caught Storm Runner for the rock fan.
2. **Removing the mood check** made results worse. Gym Hero tied for #1 for High-Energy Pop, and the k-pop user lost all the happy songs.
3. **Scoring modes** on the conflicting profile showed that each mode chooses which half of the request to ignore.
4. **Diversity penalty** removed the repeat artist from the Pop/Happy top 3 and brought in indie pop and hip hop.

**Automated tests.** There are 9 pytest tests covering loading, the scoring math, sorting, modes, diversity, and advanced features. All pass.

---

## 8. Future Work

1. **Similarity between labels instead of exact matches.** "indie pop" should earn partial credit for a pop fan, and "relaxed" should be close to "chill". A small genre or mood similarity table would fix the biggest blind spot.
2. **Turn on diversity by default and balance the catalog.** Use the diversity penalty for everyone, and add songs so no genre has only one track.
3. **Learn from behavior.** Add simple likes and skips so weights adjust per user over time. That's a first step toward collaborative filtering.
4. **Multiple tastes per user.** Let a profile hold "workout" and "study" moods, or a list of genres, instead of a single favorite.

---

## 9. Personal Reflection

**Biggest learning moment.** The biggest moment was seeing that the whole recommender is just "score every song, then sort". The interesting part isn't the code; it's the weights. When I turned off the mood check, Gym Hero tied for first for a happy-pop listener. That made it obvious that one number in a config can change what millions of people would hear in a real app.

**How AI tools helped, and when I double-checked.** I used Claude Code as an agent to write the loader, scoring function, modes, diversity rule, table formatter, tests, and the first drafts of these docs. I then checked the results myself. I verified the scoring math by hand for Sunrise City (2.00 + 1.00 + 1.47 = 4.47). I ran every profile and confirmed that the claims in the docs matched the real terminal output. I also caught a counting mistake in a draft, which said 14 single-song genres when the real number was 15. The AI was fast, but I still had to confirm that numbers in the writing came from actual runs.

**What surprised me.** Even a simple formula with five rules "feels" like a real recommendation when the top results are right and come with reasons. The reasons column made me trust it more than I expected. It also made the bad results easy to spot, like the euphoric edm song for a sad listener.

**What I'd try next.** I would add partial-credit genre and mood similarity, and a tiny listening history with likes and skips. Then I'd compare a content-based ranking against a simple "users like you also liked" ranking on the same catalog.
