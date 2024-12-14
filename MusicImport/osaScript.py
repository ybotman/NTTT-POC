import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_path = "/Users/tobybalsley/Music/ooops downgrand/Media.localized/Apple Music/Aníbal Troilo/Toda Mi Vida/Pablo.m4p"
# AppleScript to add and play the file

script = f'''
tell application "Finder"
    open POSIX file "{file_path}"
end tell
'''

subprocess.run(["osascript", "-e", script], check=True)

"""
script = f'''
tell application "Music"
    activate
    set theTrack to add POSIX file "{file_path}"
    play theTrack
end tell
'''
"""

try:
    logging.info(f"Executing AppleScript to play {file_path}")
    subprocess.run(["osascript", "-e", script], check=True)
    logging.info("Playback started successfully.")
except subprocess.CalledProcessError as e:
    logging.error(f"Error playing the file: {e.stderr.decode('utf-8') if e.stderr else 'No error message available.'}")