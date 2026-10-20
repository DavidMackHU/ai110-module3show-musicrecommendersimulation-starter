"""Core logic for VibeFinder 1.0, a content-based music recommender simulation."""

from __future__ import annotations

import csv
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INT_FIELDS = {"id", "popularity"}
FLOAT_FIELDS = {
    "energy", "tempo_bpm", "valence", "danceability",
    "acousticness", "instrumentalness", "liveness",
}
LIST_FIELDS = {"mood_tags"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """A song and its attributes (required by tests/test_recommender.py)."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Advanced features (Challenge 1). Defaults keep the original constructor working.
    popularity: int = 50
    release_decade: str = ""
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: float = 0.0
    liveness: float = 0.0


@dataclass
class UserProfile:
    """A user's taste preferences (required by tests/test_recommender.py)."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Optional advanced preferences (Challenge 1).
    target_valence: Optional[float] = None
    preferred_mood_tags: List[str] = field(default_factory=list)
    preferred_decade: Optional[str] = None
    target_popularity: Optional[int] = None
    likes_instrumental: Optional[bool] = None

    def to_prefs(self) -> Dict[str, Any]:
        """Convert this profile into the preference dictionary used by score_song."""
        prefs: Dict[str, Any] = {
            "genre": self.favorite_genre,
            "mood": self.favorite_mood,
            "energy": self.target_energy,
            "likes_acoustic": self.likes_acoustic,
        }
        optional = {
            "valence": self.target_valence,
            "mood_tags": self.preferred_mood_tags or None,
            "decade": self.preferred_decade,
            "popularity": self.target_popularity,
            "likes_instrumental": self.likes_instrumental,
        }
        prefs.update({key: value for key, value in optional.items() if value is not None})
        return prefs


# ---------------------------------------------------------------------------
# Scoring modes (Challenge 2: Strategy pattern)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScoringMode:
    """A named, swappable weighting strategy that score_song reads to judge a song."""
    name: str
    description: str
    genre: float = 2.0          # exact genre match
    mood: float = 1.0           # exact mood match
    energy: float = 1.5         # max points for perfect energy closeness
    acoustic: float = 0.5       # acoustic vs. produced preference
    valence: float = 0.5        # max points for perfect valence closeness
    mood_tags: float = 0.5      # per overlapping detailed mood tag
    decade: float = 0.5         # release decade match
    popularity: float = 0.5     # max points for perfect popularity closeness
    instrumental: float = 0.5   # instrumental vs. vocal preference


SCORING_MODES: Dict[str, ScoringMode] = {
    "balanced": ScoringMode(
        "balanced",
        "Default recipe: genre 2.0, mood 1.0, energy closeness up to 1.5, extras up to 0.5 each."),
    "genre_first": ScoringMode(
        "genre_first", "Genre dominates (4.0); mood and energy act as tie-breakers.",
        genre=4.0, mood=0.5, energy=1.0),
    "mood_first": ScoringMode(
        "mood_first", "Mood (3.0) and mood tags (1.0 each) dominate; genre matters little.",
        genre=0.75, mood=3.0, energy=1.0, mood_tags=1.0),
    "energy_focused": ScoringMode(
        "energy_focused", "Energy closeness dominates (4.0); labels matter little.",
        genre=0.5, mood=0.5, energy=4.0),
    # Phase 4 sensitivity experiments.
    "exp_weight_shift": ScoringMode(
        "exp_weight_shift", "Experiment: energy weight doubled (3.0), genre weight halved (1.0).",
        genre=1.0, energy=3.0),
    "exp_no_mood": ScoringMode(
        "exp_no_mood", "Experiment: mood check removed (mood weight 0).",
        mood=0.0),
}

DEFAULT_MODE = "balanced"


def get_mode(mode: Optional[Any] = None) -> ScoringMode:
    """Return a ScoringMode from a name, an existing ScoringMode, or None (balanced)."""
    if mode is None:
        return SCORING_MODES[DEFAULT_MODE]
    if isinstance(mode, ScoringMode):
        return mode
    try:
        return SCORING_MODES[mode]
    except KeyError:
        raise ValueError(
            f"Unknown scoring mode '{mode}'. Choose from: {', '.join(SCORING_MODES)}"
        ) from None


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _convert_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Convert one raw CSV row's numeric and list columns to proper Python types."""
    song: Dict[str, Any] = {}
    for key, raw in row.items():
        value = (raw or "").strip()
        if key in INT_FIELDS:
            song[key] = int(float(value)) if value else 0
        elif key in FLOAT_FIELDS:
            song[key] = float(value) if value else 0.0
        elif key in LIST_FIELDS:
            song[key] = [tag.strip().lower() for tag in value.split(";") if tag.strip()]
        else:
            song[key] = value
    return song


def load_songs(csv_path: str) -> List[Dict]:
    """Read songs from a CSV with the csv module and return a list of typed dictionaries."""
    path = csv_path
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join(PROJECT_ROOT, csv_path)
    with open(path, newline="", encoding="utf-8") as handle:
        return [_convert_row(row) for row in csv.DictReader(handle)]


# ---------------------------------------------------------------------------
# Scoring and ranking
# ---------------------------------------------------------------------------

def _closeness(value: float, target: float, scale: float = 1.0) -> float:
    """Return 1.0 when value equals target, falling linearly to 0.0 at distance `scale`."""
    return max(0.0, 1.0 - abs(float(value) - float(target)) / scale)


def score_song(user_prefs: Dict, song: Dict, mode: Optional[Any] = None) -> Tuple[float, List[str]]:
    """Score one song against user preferences and return (score, list of reasons)."""
    weights = get_mode(mode)
    score = 0.0
    reasons: List[str] = []

    def add(points: float, label: str) -> None:
        nonlocal score
        if points > 0:
            score += points
            reasons.append(f"{label} (+{points:.2f})")

    genre = user_prefs.get("genre")
    if genre and str(song.get("genre", "")).lower() == str(genre).lower():
        add(weights.genre, f"genre match: {song['genre']}")

    mood = user_prefs.get("mood")
    if mood and str(song.get("mood", "")).lower() == str(mood).lower():
        add(weights.mood, f"mood match: {song['mood']}")

    if user_prefs.get("energy") is not None:
        target = float(user_prefs["energy"])
        add(weights.energy * _closeness(song["energy"], target),
            f"energy {song['energy']:.2f} vs target {target:.2f}")

    if user_prefs.get("likes_acoustic") is not None:
        acoustic = float(song.get("acousticness", 0.0))
        if user_prefs["likes_acoustic"]:
            add(weights.acoustic * acoustic, "acoustic sound")
        else:
            add(weights.acoustic * (1.0 - acoustic), "produced/electric sound")

    if user_prefs.get("valence") is not None:
        target = float(user_prefs["valence"])
        add(weights.valence * _closeness(song.get("valence", 0.5), target),
            f"valence {song.get('valence', 0.5):.2f} vs target {target:.2f}")

    wanted_tags = [tag.lower() for tag in user_prefs.get("mood_tags") or []]
    if wanted_tags:
        overlap = [tag for tag in song.get("mood_tags", []) if tag in wanted_tags]
        add(weights.mood_tags * len(overlap), f"mood tags: {', '.join(overlap)}")

    decade = user_prefs.get("decade")
    if decade and song.get("release_decade") == decade:
        add(weights.decade, f"from the {decade}")

    if user_prefs.get("popularity") is not None:
        target = float(user_prefs["popularity"])
        add(weights.popularity * _closeness(song.get("popularity", 50), target, 100.0),
            f"popularity {song.get('popularity', 50)} vs target {target:.0f}")

    if user_prefs.get("likes_instrumental") is not None:
        inst = float(song.get("instrumentalness", 0.0))
        if user_prefs["likes_instrumental"]:
            add(weights.instrumental * inst, "instrumental")
        else:
            add(weights.instrumental * (1.0 - inst), "has vocals")

    if not reasons:
        reasons.append("no matching preferences (+0.00)")
    return round(score, 4), reasons


def _attr(song: Any, key: str) -> Any:
    """Read a field from either a song dict or a Song dataclass."""
    return song[key] if isinstance(song, dict) else getattr(song, key)


def apply_diversity_penalty(
    ranked: List[Tuple[Any, float, List[str]]],
    k: int,
    artist_penalty: float = 1.5,
    genre_penalty: float = 0.5,
) -> List[Tuple[Any, float, List[str]]]:
    """Greedily pick k songs, penalizing repeats of an artist or genre already picked (Challenge 3)."""
    remaining = list(ranked)
    selected: List[Tuple[Any, float, List[str]]] = []
    while remaining and len(selected) < k:
        best_index, best_adjusted, best_note = 0, float("-inf"), ""
        for index, (song, score, _reasons) in enumerate(remaining):
            artist_repeats = sum(_attr(s, "artist") == _attr(song, "artist") for s, _, _ in selected)
            genre_repeats = sum(_attr(s, "genre") == _attr(song, "genre") for s, _, _ in selected)
            penalty = artist_penalty * artist_repeats + genre_penalty * genre_repeats
            if score - penalty > best_adjusted:
                parts = []
                if artist_repeats:
                    parts.append(f"artist repeat x{artist_repeats}")
                if genre_repeats:
                    parts.append(f"genre repeat x{genre_repeats}")
                note = f"diversity penalty: {', '.join(parts)} (-{penalty:.2f})" if penalty else ""
                best_index, best_adjusted, best_note = index, score - penalty, note
        song, _score, reasons = remaining.pop(best_index)
        selected.append((song, round(best_adjusted, 4), reasons + ([best_note] if best_note else [])))
    return selected


def rank_songs(
    user_prefs: Dict,
    songs: List[Any],
    k: int = 5,
    mode: Optional[Any] = None,
    diversity: bool = False,
) -> List[Tuple[Any, float, List[str]]]:
    """Score every song, sort highest first, optionally diversify, and return the top k with reasons."""
    scored = [
        (song, *score_song(user_prefs, song if isinstance(song, dict) else asdict(song), mode))
        for song in songs
    ]
    # sorted() returns a new list and leaves the caller's catalog order untouched.
    ranked = sorted(scored, key=lambda item: (-item[1], _attr(item[0], "id")))
    if diversity:
        return apply_diversity_penalty(ranked, k)
    return ranked[:k]


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: Optional[Any] = None,
    diversity: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """Return the top k songs as (song_dict, score, explanation) tuples, highest score first."""
    return [
        (song, score, "; ".join(reasons))
        for song, score, reasons in rank_songs(user_prefs, songs, k, mode, diversity)
    ]


# ---------------------------------------------------------------------------
# OOP wrapper (required by tests)
# ---------------------------------------------------------------------------

class Recommender:
    """Object-oriented wrapper around the scoring and ranking functions."""

    def __init__(self, songs: List[Song], mode: Optional[Any] = None, diversity: bool = False):
        """Store the catalog plus the scoring mode and diversity setting to use."""
        self.songs = songs
        self.mode = get_mode(mode)
        self.diversity = diversity

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for this user, highest score first."""
        ranked = rank_songs(user.to_prefs(), self.songs, k, self.mode, self.diversity)
        return [song for song, _score, _reasons in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable sentence explaining how a song's score was built."""
        score, reasons = score_song(user.to_prefs(), asdict(song), self.mode)
        return f"Score {score:.2f} because: " + "; ".join(reasons)
