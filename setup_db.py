import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'mytunes_plus.db'


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def recreate_db():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = connect()
    cur = conn.cursor()

    cur.executescript(
        '''
        CREATE TABLE USER (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE ARTIST (
            artist_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT,
            start_year INTEGER
        );

        CREATE TABLE ALBUM (
            album_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            release_year INTEGER NOT NULL,
            label TEXT,
            producer TEXT,
            primary_artist_id INTEGER NOT NULL,
            FOREIGN KEY (primary_artist_id) REFERENCES ARTIST(artist_id)
        );

        CREATE TABLE TRACK (
            track_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            track_no INTEGER NOT NULL,
            duration_sec INTEGER NOT NULL,
            album_id INTEGER NOT NULL,
            FOREIGN KEY (album_id) REFERENCES ALBUM(album_id),
            UNIQUE (album_id, track_no)
        );

        CREATE TABLE PLAYLIST (
            playlist_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            description TEXT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES USER(user_id)
        );

        CREATE TABLE GENRE (
            genre_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE TRACK_ARTIST (
            track_id INTEGER NOT NULL,
            artist_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            PRIMARY KEY (track_id, artist_id, role),
            FOREIGN KEY (track_id) REFERENCES TRACK(track_id),
            FOREIGN KEY (artist_id) REFERENCES ARTIST(artist_id)
        );

        CREATE TABLE PLAYLIST_TRACK (
            playlist_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            PRIMARY KEY (playlist_id, track_id),
            UNIQUE (playlist_id, position),
            FOREIGN KEY (playlist_id) REFERENCES PLAYLIST(playlist_id),
            FOREIGN KEY (track_id) REFERENCES TRACK(track_id)
        );

        CREATE TABLE ALBUM_GENRE (
            album_id INTEGER NOT NULL,
            genre_id INTEGER NOT NULL,
            PRIMARY KEY (album_id, genre_id),
            FOREIGN KEY (album_id) REFERENCES ALBUM(album_id),
            FOREIGN KEY (genre_id) REFERENCES GENRE(genre_id)
        );

        CREATE TABLE USER_FOLLOWS (
            user_id INTEGER NOT NULL,
            artist_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, artist_id),
            FOREIGN KEY (user_id) REFERENCES USER(user_id),
            FOREIGN KEY (artist_id) REFERENCES ARTIST(artist_id)
        );
        '''
    )

    users = [
        (1, 'BhagyaPatel', '2026-01-21T10:00:00Z'),
        (2, 'metalfan24', '2026-01-24T16:45:00Z'),
        (3, 'studybeats', '2026-01-25T19:10:00Z'),
    ]

    artists = [
        (1, 'Metallica', 'USA', 1981),
        (2, 'Black Sabbath', 'UK', 1968),
        (3, 'AC/DC', 'Australia', 1973),
        (4, 'Nirvana', 'USA', 1987),
        (5, 'Daft Punk', 'France', 1993),
        (6, 'Michael Jackson', 'USA', 1964),
        (7, 'Eddie Van Halen', 'Netherlands', 1972),
        (8, 'Phoebe Bridgers', 'USA', 2014),
        (9, 'Dave Grohl', 'USA', 1986),
        (10, 'Sampha', 'UK', 2010),
    ]

    albums = [
        (1, 'Master of Puppets', 1986, 'Elektra', 'Flemming Rasmussen', 1),
        (2, 'Paranoid', 1970, 'Vertigo', 'Rodger Bain', 2),
        (3, 'Back in Black', 1980, 'Albert / Atlantic', 'Robert John "Mutt" Lange', 3),
        (4, 'Nevermind', 1991, 'DGC', 'Butch Vig', 4),
        (5, 'Random Access Memories', 2013, 'Columbia', 'Daft Punk', 5),
        (6, 'Thriller', 1982, 'Epic', 'Quincy Jones', 6),
        (7, 'Punisher', 2020, 'Dead Oceans', 'Tony Berg', 8),
    ]

    tracks = [
        (1, 'Battery', 1, 312, 1),
        (2, 'Master of Puppets', 2, 515, 1),
        (3, 'Welcome Home (Sanitarium)', 4, 390, 1),
        (4, 'War Pigs', 1, 477, 2),
        (5, 'Paranoid', 2, 170, 2),
        (6, 'Iron Man', 4, 355, 2),
        (7, 'Hells Bells', 1, 312, 3),
        (8, 'Back in Black', 6, 255, 3),
        (9, 'Shoot to Thrill', 2, 317, 3),
        (10, 'Smells Like Teen Spirit', 1, 301, 4),
        (11, 'In Bloom', 2, 255, 4),
        (12, 'Come as You Are', 3, 219, 4),
        (13, 'Give Life Back to Music', 1, 274, 5),
        (14, 'Instant Crush', 5, 337, 5),
        (15, 'Get Lucky', 8, 369, 5),
        (16, 'Wanna Be Startin\' Somethin\'', 1, 362, 6),
        (17, 'Beat It', 5, 258, 6),
        (18, 'Billie Jean', 6, 294, 6),
        (19, 'Kyoto', 2, 184, 7),
        (20, 'Chinese Satellite', 3, 217, 7),
        (21, 'I Know the End', 11, 345, 7),
    ]

    genres = [
        (1, 'Metal'),
        (2, 'Rock'),
        (3, 'Classic Rock'),
        (4, 'Grunge'),
        (5, 'Electronic'),
        (6, 'Pop'),
        (7, 'Indie Rock'),
        (8, 'Synthpop'),
    ]

    playlists = [
        (1, 'Gym Metal Mix', '2026-02-01T14:00:00Z', 'Heavy tracks for workouts and long drives.', 1),
        (2, 'Late Night Study', '2026-02-03T21:15:00Z', 'Calmer electronic and indie tracks for focus.', 1),
        (3, 'Classic Essentials', '2026-02-07T17:20:00Z', 'Iconic songs across classic rock and pop.', 2),
    ]

    track_artist = [
        (1, 1, 'primary'), (2, 1, 'primary'), (3, 1, 'primary'),
        (4, 2, 'primary'), (5, 2, 'primary'), (6, 2, 'primary'),
        (7, 3, 'primary'), (8, 3, 'primary'), (9, 3, 'primary'),
        (10, 4, 'primary'), (11, 4, 'primary'), (12, 4, 'primary'),
        (13, 5, 'primary'), (14, 5, 'primary'), (15, 5, 'primary'),
        (16, 6, 'primary'), (17, 6, 'primary'), (18, 6, 'primary'),
        (19, 8, 'primary'), (20, 8, 'primary'), (21, 8, 'primary'),
        (17, 7, 'featuring'),
        (15, 10, 'featuring'),
        (21, 9, 'featuring'),
        (2, 1, 'composer'), (4, 2, 'composer'), (10, 4, 'composer'),
        (15, 5, 'composer'), (17, 6, 'composer')
    ]

    playlist_track = [
        (1, 1, 1), (1, 2, 2), (1, 4, 3), (1, 5, 4), (1, 8, 5), (1, 10, 6),
        (2, 13, 1), (2, 14, 2), (2, 19, 3), (2, 20, 4), (2, 21, 5),
        (3, 7, 1), (3, 8, 2), (3, 17, 3), (3, 18, 4), (3, 4, 5)
    ]

    album_genre = [
        (1, 1), (1, 2),
        (2, 1), (2, 3),
        (3, 2), (3, 3),
        (4, 2), (4, 4),
        (5, 5), (5, 8),
        (6, 6), (6, 2),
        (7, 7), (7, 2),
    ]

    user_follows = [
        (1, 1), (1, 2), (1, 5), (1, 8),
        (2, 1), (2, 2), (2, 3),
        (3, 5), (3, 6), (3, 8),
    ]

    cur.executemany('INSERT INTO USER VALUES (?, ?, ?);', users)
    cur.executemany('INSERT INTO ARTIST VALUES (?, ?, ?, ?);', artists)
    cur.executemany('INSERT INTO ALBUM VALUES (?, ?, ?, ?, ?, ?);', albums)
    cur.executemany('INSERT INTO TRACK VALUES (?, ?, ?, ?, ?);', tracks)
    cur.executemany('INSERT INTO GENRE VALUES (?, ?);', genres)
    cur.executemany('INSERT INTO PLAYLIST VALUES (?, ?, ?, ?, ?);', playlists)
    cur.executemany('INSERT INTO TRACK_ARTIST VALUES (?, ?, ?);', track_artist)
    cur.executemany('INSERT INTO PLAYLIST_TRACK VALUES (?, ?, ?);', playlist_track)
    cur.executemany('INSERT INTO ALBUM_GENRE VALUES (?, ?);', album_genre)
    cur.executemany('INSERT INTO USER_FOLLOWS VALUES (?, ?);', user_follows)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    recreate_db()
    print(f'Created SQLite database at: {DB_PATH}')
