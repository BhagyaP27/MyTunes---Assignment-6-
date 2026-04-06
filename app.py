import sqlite3
from pathlib import Path
from flask import Flask, abort, render_template

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'mytunes_plus.db'

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def format_duration(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


@app.context_processor
def inject_helpers():
    return {'format_duration': format_duration}


@app.route('/')
def index():
    conn = get_db_connection()

    stats = {
        'artists': conn.execute('SELECT COUNT(*) AS count FROM ARTIST').fetchone()['count'],
        'albums': conn.execute('SELECT COUNT(*) AS count FROM ALBUM').fetchone()['count'],
        'tracks': conn.execute('SELECT COUNT(*) AS count FROM TRACK').fetchone()['count'],
        'playlists': conn.execute('SELECT COUNT(*) AS count FROM PLAYLIST').fetchone()['count'],
    }

    featured_artists = conn.execute(
        '''
        SELECT a.artist_id, a.name, a.country, COUNT(ta.track_id) AS credited_tracks
        FROM ARTIST a
        LEFT JOIN TRACK_ARTIST ta
            ON a.artist_id = ta.artist_id AND ta.role = 'primary'
        GROUP BY a.artist_id, a.name, a.country
        ORDER BY credited_tracks DESC, a.name ASC
        LIMIT 5;
        '''
    ).fetchall()

    featured_playlists = conn.execute(
        '''
        SELECT p.playlist_id, p.name, p.description,
               COUNT(pt.track_id) AS track_count,
               COALESCE(SUM(t.duration_sec), 0) AS total_duration
        FROM PLAYLIST p
        LEFT JOIN PLAYLIST_TRACK pt ON p.playlist_id = pt.playlist_id
        LEFT JOIN TRACK t ON pt.track_id = t.track_id
        GROUP BY p.playlist_id, p.name, p.description
        ORDER BY p.playlist_id;
        '''
    ).fetchall()

    conn.close()
    return render_template('index.html', stats=stats, featured_artists=featured_artists, featured_playlists=featured_playlists)


@app.route('/artists')
def artists():
    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT a.artist_id, a.name, a.country, a.start_year,
               COUNT(DISTINCT al.album_id) AS album_count,
               COUNT(DISTINCT ta.track_id) AS credited_tracks
        FROM ARTIST a
        LEFT JOIN ALBUM al ON a.artist_id = al.primary_artist_id
        LEFT JOIN TRACK_ARTIST ta ON a.artist_id = ta.artist_id
        GROUP BY a.artist_id, a.name, a.country, a.start_year
        ORDER BY a.name ASC;
        '''
    ).fetchall()
    conn.close()
    return render_template('artists.html', artists=rows)


@app.route('/artists/<int:artist_id>')
def artist_detail(artist_id: int):
    conn = get_db_connection()
    artist = conn.execute('SELECT * FROM ARTIST WHERE artist_id = ?;', (artist_id,)).fetchone()
    if artist is None:
        conn.close()
        abort(404)

    tracks = conn.execute(
        '''
        SELECT t.track_id, t.title AS track_title, t.track_no, t.duration_sec,
               al.album_id, al.title AS album_title, al.release_year,
               GROUP_CONCAT(DISTINCT ta.role) AS roles,
               GROUP_CONCAT(DISTINCT collaborator.name) AS all_artists
        FROM TRACK_ARTIST ta
        JOIN TRACK t ON ta.track_id = t.track_id
        JOIN ALBUM al ON t.album_id = al.album_id
        LEFT JOIN TRACK_ARTIST ta2 ON t.track_id = ta2.track_id
        LEFT JOIN ARTIST collaborator ON ta2.artist_id = collaborator.artist_id
        WHERE ta.artist_id = ?
        GROUP BY t.track_id, t.title, t.track_no, t.duration_sec, al.album_id, al.title, al.release_year
        ORDER BY al.release_year, al.title, t.track_no;
        ''',
        (artist_id,),
    ).fetchall()

    albums = conn.execute(
        '''
        SELECT al.album_id, al.title, al.release_year, al.label, al.producer,
               COUNT(t.track_id) AS track_count,
               COALESCE(SUM(t.duration_sec), 0) AS total_duration
        FROM ALBUM al
        LEFT JOIN TRACK t ON al.album_id = t.album_id
        WHERE al.primary_artist_id = ?
        GROUP BY al.album_id, al.title, al.release_year, al.label, al.producer
        ORDER BY al.release_year, al.title;
        ''',
        (artist_id,),
    ).fetchall()

    followed_by = conn.execute(
        '''
        SELECT u.username
        FROM USER_FOLLOWS uf
        JOIN USER u ON uf.user_id = u.user_id
        WHERE uf.artist_id = ?
        ORDER BY u.username;
        ''',
        (artist_id,),
    ).fetchall()
    conn.close()
    return render_template('artist_detail.html', artist=artist, tracks=tracks, albums=albums, followed_by=followed_by)


@app.route('/albums/<int:album_id>')
def album_detail(album_id: int):
    conn = get_db_connection()
    album = conn.execute(
        '''
        SELECT al.album_id, al.title, al.release_year, al.label, al.producer,
               a.artist_id, a.name AS artist_name,
               COALESCE(SUM(t.duration_sec), 0) AS total_duration,
               COUNT(t.track_id) AS track_count
        FROM ALBUM al
        JOIN ARTIST a ON al.primary_artist_id = a.artist_id
        LEFT JOIN TRACK t ON al.album_id = t.album_id
        WHERE al.album_id = ?
        GROUP BY al.album_id, al.title, al.release_year, al.label, al.producer, a.artist_id, a.name;
        ''',
        (album_id,),
    ).fetchone()
    if album is None:
        conn.close()
        abort(404)

    tracks = conn.execute(
        '''
        SELECT t.track_id, t.track_no, t.title, t.duration_sec,
               GROUP_CONCAT(ar.name || ' (' || ta.role || ')', ', ') AS credits
        FROM TRACK t
        LEFT JOIN TRACK_ARTIST ta ON t.track_id = ta.track_id
        LEFT JOIN ARTIST ar ON ta.artist_id = ar.artist_id
        WHERE t.album_id = ?
        GROUP BY t.track_id, t.track_no, t.title, t.duration_sec
        ORDER BY t.track_no;
        ''',
        (album_id,),
    ).fetchall()

    genres = conn.execute(
        '''
        SELECT g.genre_id, g.name
        FROM ALBUM_GENRE ag
        JOIN GENRE g ON ag.genre_id = g.genre_id
        WHERE ag.album_id = ?
        ORDER BY g.name;
        ''',
        (album_id,),
    ).fetchall()
    conn.close()
    return render_template('album_detail.html', album=album, tracks=tracks, genres=genres)


@app.route('/playlists')
def playlists():
    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT p.playlist_id, p.name, p.created_at, p.description, u.username,
               COUNT(pt.track_id) AS track_count,
               COALESCE(SUM(t.duration_sec), 0) AS total_duration
        FROM PLAYLIST p
        JOIN USER u ON p.user_id = u.user_id
        LEFT JOIN PLAYLIST_TRACK pt ON p.playlist_id = pt.playlist_id
        LEFT JOIN TRACK t ON pt.track_id = t.track_id
        GROUP BY p.playlist_id, p.name, p.created_at, p.description, u.username
        ORDER BY p.playlist_id;
        '''
    ).fetchall()
    conn.close()
    return render_template('playlists.html', playlists=rows)


@app.route('/playlists/<int:playlist_id>')
def playlist_detail(playlist_id: int):
    conn = get_db_connection()
    playlist = conn.execute(
        '''
        SELECT p.playlist_id, p.name, p.created_at, p.description, u.username,
               COUNT(pt.track_id) AS track_count,
               COALESCE(SUM(t.duration_sec), 0) AS total_duration
        FROM PLAYLIST p
        JOIN USER u ON p.user_id = u.user_id
        LEFT JOIN PLAYLIST_TRACK pt ON p.playlist_id = pt.playlist_id
        LEFT JOIN TRACK t ON pt.track_id = t.track_id
        WHERE p.playlist_id = ?
        GROUP BY p.playlist_id, p.name, p.created_at, p.description, u.username;
        ''',
        (playlist_id,),
    ).fetchone()
    if playlist is None:
        conn.close()
        abort(404)

    tracks = conn.execute(
        '''
        SELECT pt.position, t.track_id, t.title AS track_title, t.duration_sec,
               al.album_id, al.title AS album_title,
               GROUP_CONCAT(ar.name, ', ') AS artists
        FROM PLAYLIST_TRACK pt
        JOIN TRACK t ON pt.track_id = t.track_id
        JOIN ALBUM al ON t.album_id = al.album_id
        LEFT JOIN TRACK_ARTIST ta ON t.track_id = ta.track_id AND ta.role = 'primary'
        LEFT JOIN ARTIST ar ON ta.artist_id = ar.artist_id
        WHERE pt.playlist_id = ?
        GROUP BY pt.position, t.track_id, t.title, t.duration_sec, al.album_id, al.title
        ORDER BY pt.position;
        ''',
        (playlist_id,),
    ).fetchall()
    conn.close()
    return render_template('playlist_detail.html', playlist=playlist, tracks=tracks)


@app.route('/genres')
def genres():
    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT g.genre_id, g.name, COUNT(ag.album_id) AS album_count
        FROM GENRE g
        LEFT JOIN ALBUM_GENRE ag ON g.genre_id = ag.genre_id
        GROUP BY g.genre_id, g.name
        ORDER BY g.name;
        '''
    ).fetchall()
    conn.close()
    return render_template('genres.html', genres=rows)


@app.route('/genres/<int:genre_id>')
def genre_albums(genre_id: int):
    conn = get_db_connection()
    genre = conn.execute('SELECT * FROM GENRE WHERE genre_id = ?;', (genre_id,)).fetchone()
    if genre is None:
        conn.close()
        abort(404)

    albums = conn.execute(
        '''
        SELECT al.album_id, al.title, al.release_year, al.label, al.producer,
               a.name AS artist_name,
               COUNT(t.track_id) AS track_count,
               COALESCE(SUM(t.duration_sec), 0) AS total_duration
        FROM ALBUM_GENRE ag
        JOIN ALBUM al ON ag.album_id = al.album_id
        JOIN ARTIST a ON al.primary_artist_id = a.artist_id
        LEFT JOIN TRACK t ON al.album_id = t.album_id
        WHERE ag.genre_id = ?
        GROUP BY al.album_id, al.title, al.release_year, al.label, al.producer, a.name
        ORDER BY al.release_year, al.title;
        ''',
        (genre_id,),
    ).fetchall()
    conn.close()
    return render_template('genre_albums.html', genre=genre, albums=albums)


@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)