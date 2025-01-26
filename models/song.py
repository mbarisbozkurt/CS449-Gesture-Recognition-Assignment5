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
    
    def __init__(self, title, artist, duration, spotify_uri=None, album=None, progress=0):
        self.title = title
        self.artist = artist
        self.duration = duration
        self.album = album
        self.progress = progress
        self.spotify_uri = spotify_uri
        self.is_playing = False

    def play(self):
        if self.spotify_uri and self.__class__.spotify:
            try:
                # Aktif cihazı kontrol et
                devices = self.__class__.spotify.devices()
                if devices['devices']:
                    device_id = devices['devices'][0]['id']  # İlk aktif cihazı kullan
                    try:
                        # Önceki şarkıyı durdur
                        if hasattr(self.__class__, 'current_playing_song') and self.__class__.current_playing_song:
                            try:
                                self.__class__.current_playing_song.is_playing = False
                                self.__class__.spotify.pause_playback()  # Önceki şarkıyı durdur
                            except:
                                pass
                        
                        # Yeni şarkıyı çal
                        self.__class__.spotify.start_playback(device_id=device_id, uris=[self.spotify_uri])
                        self.is_playing = True
                        self.__class__.current_playing_song = self
                        print(f"Now playing: {self.title} by {self.artist}")
                    except Exception as e:
                        print(f"Şarkı çalınırken hata oluştu: {e}")
                        self.is_playing = False
                else:
                    print("Aktif Spotify cihazı bulunamadı. Lütfen Spotify'ı bir cihazda açın.")
            except Exception as e:
                print(f"Spotify bağlantısında hata: {e}")
                self.is_playing = False

    def stop(self):
        try:
            if self.__class__.spotify:
                try:
                    self.__class__.spotify.pause_playback()
                except:
                    pass
                self.is_playing = False
                if hasattr(self.__class__, 'current_playing_song'):
                    self.__class__.current_playing_song = None
        except Exception as e:
            print(f"Şarkı durdurulurken hata oluştu: {e}")
            self.is_playing = False

    def pause(self):
        try:
            if self.__class__.spotify and self.is_playing:
                try:
                    self.__class__.spotify.pause_playback()
                except:
                    pass
                self.is_playing = False
        except Exception as e:
            print(f"Şarkı duraklatılırken hata oluştu: {e}")
            self.is_playing = False

    def unpause(self):
        try:
            if self.__class__.spotify and not self.is_playing:
                try:
                    self.__class__.spotify.start_playback()
                except:
                    pass
                self.is_playing = True
        except Exception as e:
            print(f"Şarkı devam ettirilirken hata oluştu: {e}")
            self.is_playing = False

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
        # Popüler şarkıları getir
        if Song.spotify:
            results = Song.spotify.search(q='year:2024', limit=10, type='track')
            return [
                Song(
                    track['name'],
                    track['artists'][0]['name'],
                    str(int(track['duration_ms']/1000//60)) + ":" + str(int(track['duration_ms']/1000%60)).zfill(2),
                    track['uri'],
                    track['album']['name']
                )
                for track in results['tracks']['items']
            ]
        return [] 