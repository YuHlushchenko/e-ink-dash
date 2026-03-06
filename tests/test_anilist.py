import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / '.env')
token = os.getenv('ANILIST_ACCESS_TOKEN', '')
user_id = os.getenv('ANILIST_USER_ID', '')
print(f'TOKEN: {token[:20]}...{token[-10:] if token else "EMPTY"}')
print(f'USER_ID: {user_id}')

from api.anilist import get_current_anime, get_planning_anime, get_user_stats

print('--- current anime ---')
data, err = get_current_anime()
print('error:', err)
entries = [e for lst in data['MediaListCollection']['lists'] for e in lst['entries']] if data else []
print(f'entries: {len(entries)}')
for e in entries:
    print(f"  {e['media']['title']['romaji']} | progress: {e['progress']}")

print('--- planning anime ---')
data, err = get_planning_anime()
print('error:', err)
entries = [e for lst in data['MediaListCollection']['lists'] for e in lst['entries']] if data else []
print(f'entries: {len(entries)}')
for e in entries:
    print(f"  {e['media']['title']['romaji']}")

print('--- user stats ---')
data, err = get_user_stats()
print('error:', err)
print('data:', data)
