class Song:
    def __init__(self, title, artist, duration, album=None, progress=0):
        self.title = title
        self.artist = artist
        self.duration = duration
        self.album = album
        self.progress = progress

    @staticmethod
    def get_current_song():
        return Song(
            "Starlight Dreams",
            "Luna Eclipse",
            "3:45",
            "Midnight Waves",
            0.7
        )

    @staticmethod
    def get_playlist():
        return [
            Song("Cosmic Journey", "Solar Beats", "4:12"),
            Song("Ocean Breeze", "Wave Riders", "3:28"),
            Song("Mountain Echo", "Nature Sound", "5:01"),
            Song("City Lights", "Urban Pulse", "3:56"),
            Song("Desert Wind", "Sand Walker", "4:45"),
            Song("Forest Rain", "Green Echo", "3:33"),
            Song("Night Drive", "Midnight Run", "4:22"),
            Song("Morning Mist", "Dawn Breaker", "3:15"),
            Song("Sunset Melody", "Evening Glow", "4:05"),
            Song("River Flow", "Water Spirit", "3:48"),
        ] 