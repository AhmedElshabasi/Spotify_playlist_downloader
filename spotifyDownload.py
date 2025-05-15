import os
import json
import eyed3
import urllib.request
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
load_dotenv()


# --- CONFIGURATION ---
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
SCOPE = 'playlist-read-private playlist-read-collaborative'
DOWNLOAD_DIR = 'Downloads'

# --- AUTHENTICATION ---
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE,
    open_browser=True
))

# --- YOUTUBE-DLP CONFIG ---
YDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),  # <-- output directly to Downloads
    'ffmpeg_location': r'C:\ffmpeg\bin',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }]
}

def download_song(track_name, artist_name, metadata):
    # Clean and use Artist - Title format
    safe_title = track_name.replace('/', '_').replace('\\', '_')
    safe_artist = artist_name.replace('/', '_').replace('\\', '_')
    final_filename = f"{safe_artist} - {safe_title}.mp3"
    final_path = os.path.join(DOWNLOAD_DIR, final_filename)

    # ✅ Skip if already downloaded
    if os.path.exists(final_path):
        print(f"Skipping {artist_name} - {track_name} (already exists)")
        return

    search_query = f"{track_name} {artist_name}"

    # Temp path
    temp_path = os.path.join(DOWNLOAD_DIR, 'temp_download.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_path,
        'ffmpeg_location': r'C:\ffmpeg\bin',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': False
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{search_query}", download=True)['entries'][0]
        downloaded_file = os.path.join(DOWNLOAD_DIR, 'temp_download.mp3')

    if not os.path.exists(downloaded_file):
        print(f"Download failed for: {artist_name} - {track_name}")
        return

    # 🎨 Add metadata and album art
    audiofile = eyed3.load(downloaded_file)
    if audiofile is None:
        print(f"Could not tag file: {downloaded_file}")
        return

    if audiofile.tag is None:
        audiofile.initTag()
        audiofile.tag.version = eyed3.id3.ID3_V2_3  # ensures image embedding works

    audiofile.tag.artist = artist_name
    audiofile.tag.title = track_name
    audiofile.tag.album = metadata.get('album')
    audiofile.tag.track_num = metadata.get('track_number')

    if metadata.get('image_url'):
        try:
            image_data = urllib.request.urlopen(metadata['image_url']).read()
            audiofile.tag.images.set(
                eyed3.id3.frames.ImageFrame.FRONT_COVER,
                image_data,
                'image/jpeg'
            )
        except Exception as e:
            print(f"Couldn't fetch album art: {e}")

    audiofile.tag.save()


    os.rename(downloaded_file, final_path)


def main():
    playlists = sp.current_user_playlists()
    for i, playlist in enumerate(playlists['items']):
        print(f"{i}: {playlist['name']}")

    index = int(input("Enter playlist number to download: "))
    selected = playlists['items'][index]
    playlist_id = selected['id']

    print(f"Downloading: {selected['name']}")
    tracks = sp.playlist_tracks(playlist_id)

    for item in tracks['items']:
        track = item['track']
        name = track['name']
        artist = track['artists'][0]['name']
        album = track['album']['name']
        track_number = track['track_number']
        image_url = track['album']['images'][0]['url'] if track['album']['images'] else None

        print(f"--> {name} - {artist}")
        download_song(name, artist, {
            'album': album,
            'track_number': track_number,
            'image_url': image_url
        })

if __name__ == '__main__':
    main()
