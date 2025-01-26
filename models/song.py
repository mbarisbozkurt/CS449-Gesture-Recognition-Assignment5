import pygame
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser

pygame.mixer.init()

class Song:
    # Spotify API credentials
    CLIENT_ID = None  # Spotify Developer Dashboard'dan alınacak
    CLIENT_SECRET = None  # Spotify Developer Dashboard'dan alınacak
    REDIRECT_URI = 'http://localhost:8888/callback'
    
    # Spotify API instance
    spotify = None
    
    # Aktif şarkıyı takip etmek için statik değişken
    active_song = None
    
    # Device ID önbelleği
    _cached_device_id = None
    _last_device_check = 0
    
    @classmethod
    def initialize_spotify(cls, client_id, client_secret):
        cls.CLIENT_ID = client_id
        cls.CLIENT_SECRET = client_secret
        
        # Spotify API'ye bağlan
        cls.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=cls.CLIENT_ID,
            client_secret=cls.CLIENT_SECRET,
            redirect_uri=cls.REDIRECT_URI,
            scope="user-read-playback-state user-modify-playback-state"
        ))
        
        # İlk device ID'yi önbelleğe al
        try:
            devices = cls.spotify.devices()
            if devices['devices']:
                cls._cached_device_id = devices['devices'][0]['id']
                cls._last_device_check = pygame.time.get_ticks()
        except Exception:
            pass

    def __init__(self, title, artist, duration, spotify_uri=None, album=None, progress=0):
        self.title = title
        self.artist = artist
        self.duration = duration
        self.album = album
        self.progress = progress
        self.spotify_uri = spotify_uri
        self.is_playing = False

    def play(self):
        if not self.spotify_uri or not self.__class__.spotify:
            return False

        try:
            current_time = pygame.time.get_ticks()
            
            # Device ID'yi sadece 30 saniyede bir kontrol et
            if (not self.__class__._cached_device_id or 
                current_time - self.__class__._last_device_check > 30000):
                devices = self.__class__.spotify.devices()
                if devices['devices']:
                    self.__class__._cached_device_id = devices['devices'][0]['id']
                    self.__class__._last_device_check = current_time
                else:
                    return False
            
            # Geçici olarak önceki aktif şarkıyı sakla
            previous_song = self.__class__.active_song
            
            # Önce kendimizi aktif şarkı yap ve durumu güncelle
            self.__class__.active_song = self
            self.is_playing = True
            
            # Sonra şarkıyı çal
            self.__class__.spotify.start_playback(
                device_id=self.__class__._cached_device_id, 
                uris=[self.spotify_uri]
            )
            
            # En son önceki şarkıyı temizle
            if previous_song and previous_song != self:
                previous_song.is_playing = False
                previous_song.progress = 0
            
            return True
            
        except Exception as e:
            self.is_playing = False
            self.__class__.active_song = None
            if "Restriction violated" in str(e):
                print("Spotify Premium gerekiyor veya başka bir cihazda çalıyor olabilir.")
            else:
                print(f"Spotify playback error: {e}")
            return False

    def stop(self):
        if self.spotify_uri and self.__class__.spotify:
            try:
                self.__class__.spotify.pause_playback()
                self.is_playing = False
                self.progress = 0
                if self.__class__.active_song == self:
                    self.__class__.active_song = None
                return True
            except Exception as e:
                if "Restriction violated" in str(e):
                    print("Spotify Premium gerekiyor veya başka bir cihazda çalıyor olabilir.")
                return False
        return False

    def pause(self):
        if self.spotify_uri and self.__class__.spotify:
            try:
                self.__class__.spotify.pause_playback()
                self.is_playing = False
                if self.__class__.active_song == self:
                    self.__class__.active_song = None
                return True
            except Exception as e:
                if "Restriction violated" in str(e):
                    print("Spotify Premium gerekiyor veya başka bir cihazda çalıyor olabilir.")
                return False
        return False

    def unpause(self):
        if self.spotify_uri and self.__class__.spotify:
            try:
                self.__class__.spotify.start_playback()
                self.is_playing = True
                self.__class__.active_song = self
                return True
            except Exception as e:
                if "Restriction violated" in str(e):
                    print("Spotify Premium gerekiyor veya başka bir cihazda çalıyor olabilir.")
                return False
        return False

    @staticmethod
    def search_songs(query, limit=10):
        if Song.spotify:
            results = Song.spotify.search(q=query, limit=limit, type='track')
            songs = []
            for track in results['tracks']['items']:
                song = Song(
                    title=track['name'],
                    artist=track['artists'][0]['name'],
                    duration=str(int(track['duration_ms']/1000//60)) + ":" + str(int(track['duration_ms']/1000%60)).zfill(2),
                    spotify_uri=track['uri'],
                    album=track['album']['name']
                )
                songs.append(song)
            return songs
        return []

    @staticmethod
    def get_current_song():
        if Song.spotify:
            current = Song.spotify.current_user_playing_track()
            if current and current['item']:
                track = current['item']
                return Song(
                    track['name'],
                    track['artists'][0]['name'],
                    str(int(track['duration_ms']/1000//60)) + ":" + str(int(track['duration_ms']/1000%60)).zfill(2),
                    track['uri'],
                    track['album']['name'],
                    current['progress_ms'] / track['duration_ms']
                )
        return None

    @staticmethod
    def get_playlist():
        playlist_data = [
            {"title": "Sad but True", "artist": "Metallica", "album": "Metallica (The Black Album)"},
            {"title": "Bir Derdim Var", "artist": "Mor ve Otesi", "album": "Dünya Yalan Söylüyor"},
            {"title": "Kufi", "artist": "Duman", "album": "Duman I"},
            {"title": "The Trooper", "artist": "Iron Maiden", "album": "Piece of Mind"},
            {"title": "Don't Cry", "artist": "Guns N' Roses", "album": "Use Your Illusion I"}
        ]
        
        playlist_songs = []
        if Song.spotify:
            for song_data in playlist_data:
                # Her şarkı için arama yap
                query = f"track:{song_data['title']} artist:{song_data['artist']}"
                results = Song.spotify.search(q=query, limit=1, type='track')
                
                if results['tracks']['items']:
                    track = results['tracks']['items'][0]
                    song = Song(
                        title=song_data['title'],
                        artist=song_data['artist'],
                        duration=str(int(track['duration_ms']/1000//60)) + ":" + str(int(track['duration_ms']/1000%60)).zfill(2),
                        spotify_uri=track['uri'],
                        album=song_data['album']
                    )
                    playlist_songs.append(song)
                else:
                    # Eğer şarkı bulunamazsa URI olmadan ekle
                    song = Song(
                        title=song_data['title'],
                        artist=song_data['artist'],
                        duration="0:00",
                        spotify_uri=None,
                        album=song_data['album']
                    )
                    playlist_songs.append(song)
                    print(f"Şarkı bulunamadı: {song_data['title']} - {song_data['artist']}")
        
        return playlist_songs 