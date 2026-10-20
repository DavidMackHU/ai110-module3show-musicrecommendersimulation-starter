"""
Command line runner for VibeFinder 1.0, the Music Recommender Simulation.

Run from the project root:

    python -m src.main                          # default pop/happy profile, balanced mode
    python -m src.main --profile all            # every profile (core + advanced + edge cases)
    python -m src.main --profile chill_lofi --mode mood_first
    python -m src.main --diverse                # turn on the artist/genre diversity penalty
    python -m src.main --compare-modes          # one profile under every scoring mode
    python -m src.main --list                   # show available profiles and modes
"""

import argparse
from typing import Dict, List, Sequence

try:
    from src.recommender import SCORING_MODES, load_songs, rank_songs
except ImportError:  # allows `python src/main.py` as well
    from recommender import SCORING_MODES, load_songs, rank_songs


DEFAULT_PROFILE = "pop_happy"

PROFILES: Dict[str, Dict] = {
    # --- Core profiles -----------------------------------------------------
    "pop_happy": {
        "label": "Default Pop/Happy (starter profile)",
        "prefs": {"genre": "pop", "mood": "happy", "energy": 0.8},
    },
    "high_energy_pop": {
        "label": "High-Energy Pop",
        "prefs": {"genre": "pop", "mood": "happy", "energy": 0.9, "likes_acoustic": False},
    },
    "chill_lofi": {
        "label": "Chill Lofi",
        "prefs": {"genre": "lofi", "mood": "chill", "energy": 0.35,
                  "likes_acoustic": True, "likes_instrumental": True},
    },
    "deep_intense_rock": {
        "label": "Deep Intense Rock",
        "prefs": {"genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False},
    },
    # --- Advanced-feature profile (Challenge 1) ------------------------------
    "nostalgic_night_drive": {
        "label": "Nostalgic Night Drive (uses advanced features)",
        "prefs": {"genre": "synthwave", "mood": "moody", "energy": 0.65,
                  "mood_tags": ["nostalgic", "dreamy"], "decade": "1980s",
                  "popularity": 50, "valence": 0.5},
    },
    # --- Adversarial / edge-case profiles ------------------------------------
    "edge_sad_but_hyped": {
        "label": "EDGE: Sad but Hyped (energy 0.9 + mood sad)",
        "prefs": {"genre": "edm", "mood": "sad", "energy": 0.9},
    },
    "edge_unknown_genre": {
        "label": "EDGE: Genre not in catalog (k-pop)",
        "prefs": {"genre": "k-pop", "mood": "happy", "energy": 0.6},
    },
    "edge_acoustic_metalhead": {
        "label": "EDGE: Acoustic-loving Metalhead",
        "prefs": {"genre": "metal", "mood": "angry", "energy": 0.95, "likes_acoustic": True},
    },
    "edge_energy_only": {
        "label": "EDGE: Energy only (no genre or mood)",
        "prefs": {"energy": 0.5},
    },
}


def format_table(headers: Sequence[str], rows: List[Sequence[str]]) -> str:
    """Render rows as an ASCII table; cells may contain newlines (Challenge 4)."""
    split_rows = [[str(cell).split("\n") for cell in row] for row in rows]
    widths = []
    for col, header in enumerate(headers):
        cell_width = max((len(line) for row in split_rows for line in row[col]), default=0)
        widths.append(max(len(header), cell_width))

    def border(char: str = "-") -> str:
        return "+" + "+".join(char * (w + 2) for w in widths) + "+"

    def line(cells: Sequence[str]) -> str:
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

    out = [border(), line(headers), border("=")]
    for row in split_rows:
        height = max(len(cell) for cell in row)
        for i in range(height):
            out.append(line([cell[i] if i < len(cell) else "" for cell in row]))
        out.append(border())
    return "\n".join(out)


def describe_prefs(prefs: Dict) -> str:
    """Return the preference dictionary as a compact key=value string."""
    parts = []
    for key, value in prefs.items():
        if isinstance(value, list):
            value = "/".join(value)
        parts.append(f"{key}={value}")
    return ", ".join(parts)


def print_recommendations(songs: List[Dict], profile_key: str, mode: str, k: int, diverse: bool) -> None:
    """Rank songs for one profile and print them as a table with reasons."""
    profile = PROFILES[profile_key]
    results = rank_songs(profile["prefs"], songs, k=k, mode=mode, diversity=diverse)
    print(f"\n=== {profile['label']} ===")
    print(f"Prefs: {describe_prefs(profile['prefs'])}")
    print(f"Mode: {mode} | Diversity penalty: {'on' if diverse else 'off'}")
    rows = [
        (str(rank), song["title"], song["artist"], f"{song['genre']} / {song['mood']}",
         f"{score:.2f}", "\n".join(reasons))
        for rank, (song, score, reasons) in enumerate(results, start=1)
    ]
    print(format_table(["#", "Title", "Artist", "Genre / Mood", "Score", "Reasons"], rows))


def main() -> None:
    """Parse CLI options, load the catalog, and print ranked recommendations."""
    parser = argparse.ArgumentParser(description="VibeFinder 1.0 music recommender simulation")
    parser.add_argument("--profile", default=DEFAULT_PROFILE,
                        help=f"profile name or 'all' (default: {DEFAULT_PROFILE})")
    parser.add_argument("--mode", default="balanced", choices=list(SCORING_MODES),
                        help="scoring strategy (default: balanced)")
    parser.add_argument("--k", type=int, default=5, help="number of recommendations (default: 5)")
    parser.add_argument("--diverse", action="store_true",
                        help="penalize repeated artists/genres in the top results")
    parser.add_argument("--compare-modes", action="store_true",
                        help="run the selected profile(s) under every scoring mode")
    parser.add_argument("--list", action="store_true", help="list profiles and modes, then exit")
    args = parser.parse_args()

    if args.list:
        print("Profiles:")
        for key, profile in PROFILES.items():
            print(f"  {key:<25} {profile['label']}")
        print("\nScoring modes:")
        for key, mode in SCORING_MODES.items():
            print(f"  {key:<25} {mode.description}")
        return

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    if args.profile == "all":
        profile_keys = list(PROFILES)
    elif args.profile in PROFILES:
        profile_keys = [args.profile]
    else:
        parser.error(f"unknown profile '{args.profile}'. Use --list to see options.")

    modes = list(SCORING_MODES) if args.compare_modes else [args.mode]
    for profile_key in profile_keys:
        for mode in modes:
            print_recommendations(songs, profile_key, mode, args.k, args.diverse)


if __name__ == "__main__":
    main()
