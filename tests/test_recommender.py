from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# Functional API tests
# ---------------------------------------------------------------------------

from src.recommender import (  # noqa: E402
    SCORING_MODES,
    load_songs,
    recommend_songs,
    score_song,
)


def test_load_songs_converts_types():
    songs = load_songs("data/songs.csv")
    assert len(songs) >= 20
    first = songs[0]
    assert isinstance(first["id"], int)
    assert isinstance(first["energy"], float)
    assert isinstance(first["tempo_bpm"], float)
    assert isinstance(first["popularity"], int)
    assert isinstance(first["mood_tags"], list)


def test_score_song_returns_score_and_reasons():
    song = {"genre": "pop", "mood": "happy", "energy": 0.8, "acousticness": 0.2}
    score, reasons = score_song({"genre": "pop", "mood": "happy", "energy": 0.8}, song)
    assert score == 2.0 + 1.0 + 1.5
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)


def test_energy_rewards_closeness_not_magnitude():
    prefs = {"energy": 0.4}
    near, _ = score_song(prefs, {"genre": "x", "mood": "y", "energy": 0.42})
    loud, _ = score_song(prefs, {"genre": "x", "mood": "y", "energy": 0.95})
    assert near > loud


def test_recommend_songs_sorted_and_limited():
    songs = load_songs("data/songs.csv")
    results = recommend_songs({"genre": "lofi", "mood": "chill", "energy": 0.35}, songs, k=3)
    assert len(results) == 3
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0][0]["genre"] == "lofi"
    assert isinstance(results[0][2], str)


def test_modes_change_rankings():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "pop", "mood": "sad", "energy": 0.3}
    genre_top = recommend_songs(prefs, songs, k=1, mode="genre_first")[0][0]
    mood_top = recommend_songs(prefs, songs, k=1, mode="mood_first")[0][0]
    assert genre_top["genre"] == "pop"
    assert mood_top["mood"] == "sad"
    assert {"balanced", "genre_first", "mood_first", "energy_focused"} <= set(SCORING_MODES)


def test_diversity_penalty_limits_repeat_artists():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    plain = recommend_songs(prefs, songs, k=3)
    diverse = recommend_songs(prefs, songs, k=3, diversity=True)
    plain_artists = [s["artist"] for s, _, _ in plain]
    diverse_artists = [s["artist"] for s, _, _ in diverse]
    assert len(set(plain_artists)) < len(plain_artists)
    assert len(set(diverse_artists)) == len(diverse_artists)


def test_advanced_features_add_points():
    song = {"genre": "synthwave", "mood": "moody", "energy": 0.75,
            "mood_tags": ["nostalgic", "dreamy"], "release_decade": "1980s", "popularity": 60}
    base, _ = score_song({"energy": 0.75}, song)
    rich, reasons = score_song({"energy": 0.75, "mood_tags": ["nostalgic"], "decade": "1980s"}, song)
    assert rich == base + 0.5 + 0.5
    assert any("mood tags" in r for r in reasons)
