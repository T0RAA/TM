# Music Dating App

A Python application that matches users based on their music preferences using Spotify integration and Discord Rich Presence.

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your credentials:
   - Copy `src/config.example.py` to `src/config.py`
   - Get your Spotify API credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Get your Discord Client ID from [Discord Developer Portal](https://discord.com/developers/applications)
   - Update the values in `src/config.py` with your credentials

4. Run the application:
   ```bash
   python src/app.py
   ```

## Features

- Spotify integration for music playback tracking
- User profile management with music preferences
- Compatibility matching based on music taste
- Discord Rich Presence integration
- Modern GUI interface

## Security Note

Never commit your `config.py` file or share your API credentials. The `config.py` file is already added to `.gitignore` to prevent accidental commits.

TM

 