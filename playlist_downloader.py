# first step: take playlist and put it in soundiiz to turn it into a youtube playlist
# unfortunately the soundiiz limit is 200 tracks and my playlist is pushing 300 so it is missing some but oh well

# we will be using yt-dlp to download from a youtube playlist, and checking a csv of saved songs to make sure nothing is downloaded twice.
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import subprocess
import os

os.environ['SPOTIPY_CLIENT_ID'] = 'd2982ca926f54dcc808061140706457e'
os.environ['SPOTIPY_CLIENT_SECRET'] = 'dd8c295844e64707a42bfa9b8e1928c9'

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

# URL = ['https://www.youtube.com/playlist?list=PL2woi35GYAN3mvqPrZuZLQW-_wGa4bP4v']

class MyLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)
            print(msg)

    def info(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        print(msg)
# ℹ️ See "progress_hooks" in help(yt_dlp.YoutubeDL)
output_filename = None
def my_hook(d):
    print(d['status'])

    if d['status'] == 'finished':
        print('Done downloading, now post-processing ...')

        print(MyLogger.info)

ydl_opts_og = {
    'progress_hooks': [my_hook],
    'extract_flat': 'discard_in_playlist',
    'final_ext': 'mp3',
    'format': 'bestaudio/best',
    'fragment_retries': 10,
    'ignoreerrors': 'only_download',
    # 'outtmpl': 'downloaded_music/%(title)s-%(id)s.%(ext)s',
    'postprocessors': [{'key': 'FFmpegExtractAudio',
                     'nopostoverwrites': False,
                     'preferredcodec': 'mp3',
                     'preferredquality': '5'},
                    {'key': 'FFmpegConcat',
                     'only_multi_video': True,
                     'when': 'playlist'}],
    # 'postprocessor_args': [
    #     '-metadata', f'artist={metadata["artist"]}',
    #     '-metadata', f'title={metadata["title"]}',
    #     '-metadata', f'album={metadata["album"]}',
    #     '-metadata', f'date={metadata["date"]}',
    # ],
 'retries': 10}


def set_thumbnail_with_ffmpeg(input_filename, thumbnail_url):
    output_filename = "01_" + input_filename 
    try:
        subprocess.run(['ffmpeg', '-i', input_filename, '-i', thumbnail_url, '-c', 'copy', '-map', '0', '-map', '1', '-y', output_filename])
        os.replace(output_filename, input_filename)
    except:
        print("error adding the thumbnail to " + input_filename + " moving on")

def download_with_metadata(url, custom_metadata, output_filename):
    print("WE ARE IN DOWNLOAD_WITH_METADATA (2 LAYERS IN)")

    ydl_opts = {
        'progress_hooks': [my_hook],
        'extract_flat': 'discard_in_playlist',
        'final_ext': 'mp3',
        'format': 'bestaudio/best',
        'fragment_retries': 10,
        'ignoreerrors': 'only_download',
        # 'outtmpl': 'downloaded_music/%(title)s-%(id)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio',
                        'nopostoverwrites': False,
                        'preferredcodec': 'mp3',
                        'preferredquality': '5'},
                        {'key': 'FFmpegConcat',
                        'only_multi_video': True,
                        'when': 'playlist'}],
        'postprocessor_args': [
            '-metadata', f'artist={custom_metadata["artist"]}',
            '-metadata', f'title={custom_metadata["title"]}',
            '-metadata', f'album={custom_metadata["album"]}',
            '-metadata', f'date={custom_metadata["date"]}',
        ],
        'retries': 10}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(url)

    # get thumbnail url with spotipy, input_filename is the output file name from ydl
    
    input_filename = output_filename
    print(output_filename)
    set_thumbnail_with_ffmpeg(input_filename, custom_metadata["album_art_url"])


def get_metadata(url, metadata):
    print("WE ARE IN GET_METADATA (1 LAYER IN)")
    with yt_dlp.YoutubeDL(ydl_opts_og) as ydl:
        # global metadata
        info_dict = ydl.extract_info(url, download=False)

        title = info_dict.get('title',None)
        id = info_dict.get('id',None)
        ext = info_dict.get('ext',None)
        # test_str = ''.join(letter for letter in title if letter.isalnum())
        filename = title + " [" + id + "].mp3"
        # filename = test_str + ".mp3"
        print("yeahh", info_dict.keys())
        print("EXT: ", ext)
        print("FILENAME:", filename)
        print("TITLE:", title)
        # metadata = get_md(title)


        download_with_metadata(url, metadata, filename)


def get_spotify_playlist_tracks(sp, playlist_url):
    # username = playlist_url.split('/')[4]
    # playlist_id = playlist_url.split('/')[6].split('?')[0]

    results = sp.playlist_tracks(playlist_url)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])




    return tracks

def search_youtube_for_track(track_name, artist_name):
    query = f"{track_name} {artist_name}"
    ydl_opts = {
        'quiet': True,
        'extract_info': True,
        'force_generic_extractor': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in search_results:
                # Return the URL of the first result
                return search_results['entries'][0]['original_url']
        except yt_dlp.DownloadError as e:
            print(f"Error searching for {query}: {e}")
    
    return None

playlist_url = 'https://open.spotify.com/playlist/5H4Vy1crI6gJfyQH526kqG?si=4d7a4a7f36ea4b61'
playlist_tracks = get_spotify_playlist_tracks(spotify, playlist_url)
# print(playlist_tracks)
for index, track in enumerate(playlist_tracks, start=1):
    track_name = track['track']['name']
    artist_name = track['track']['artists'][0]['name']

# THIS IS THE NEW METADATA GENERATION LOCATION!!!
    first_track = track['track']
    title = first_track['name']
    artist_name = first_track['artists'][0]['name']
    album_name = first_track['album']['name']
    release_date = first_track['album']['release_date']
    album_art_url = first_track['album']['images'][0]['url'] if 'images' in first_track['album'] and first_track['album']['images'] else None

    metadata = {
        'artist': artist_name,
        'title': title,
        'album': album_name,
        'date': release_date,
        'album_art_url': album_art_url
    }



    with open(r'songsDownloaded.txt', 'a+') as file:
        # append and read the file
        # read all content from a file using read()
        file.seek(0)
        content = file.read()
        # check if string present or not
        if title in content:
            print('song already downloaded, moving to next song')
            continue
        else:
            print('song not downloaded, downloading now')
            file.write(title)
            file.write("\n")


        # for index, line in enumerate(f):
        #     # search string
        #     if title in line:
        #         print('song already downloaded, moving to next song')
        #         break
                
            
        #     print('string does not exist in a file')






    # Search for the track on YouTube
    youtube_url = search_youtube_for_track(track_name, artist_name)

    if youtube_url:
        print(f"Track {index}: {track_name} by {artist_name} - YouTube URL: {youtube_url}")
        
        get_metadata(youtube_url, metadata)
    else:
        print(f"Track {index}: {track_name} by {artist_name} - No YouTube match found")






# yt-dlp -x --audio-format "mp3" --add-metadata --embed-thumbnail 'playlistlink'
