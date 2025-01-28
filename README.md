# Hand Gesture-Controlled Spotify Player

A music player application that integrates with Spotify and can be controlled through hand gestures. The computer camera detects user's hand movements in real-time and converts these movements into music controls.

## Prerequisites

- Python 3.x
- Webcam
- Spotify Account
- Spotify Developer Account (for API credentials)

## Installation

1. Clone the repository

```bash
git clone https://github.com/mbarisbozkurt/CS449-Gesture-Recognition-Assignment5.git
```

2. Install required packages

```bash
pip install -r requirements.txt
```

3. Set up Spotify API credentials
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new application
   - Get your Client ID and Client Secret
   - Create a `.env` file in the project root
   - Add your credentials:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

## Usage

1. Run the application:

```bash
python main.py
```

2. Available Gestures:

   - Index finger movement: Control cursor
   - Pinch gesture (thumb + index finger): Click/Select and Play/Pause songs
   - Two fingers up or down (index + middle): Scroll playlist

3. Controls:
   - Play/Pause songs using the pinch gesture
   - Control playback through either the application or Spotify
   - Scroll through your playlist using two fingers up or down

## Note

- The application requires a working webcam
- Make sure you have an active Spotify account and are logged in
- The application syncs with your Spotify playback state

## Dependencies

- python-dotenv
- spotipy
- opencv-python
- mediapipe
- numpy

## License

[MIT License](LICENSE)
