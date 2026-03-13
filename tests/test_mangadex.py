import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

print(f'USERNAME: {os.getenv("MANGADEX_USERNAME", "EMPTY")}')
print(f'CLIENT_ID: {os.getenv("MANGADEX_CLIENT_ID", "EMPTY")}')

from api.mangadex import get_reading_list

print('--- reading list ---')
data, err = get_reading_list()
print('error:', err)
print(f'entries: {len(data) if data else 0}')
for m in (data or []):
    unread = '(unread)' if m['has_unread'] else ''
    print(f"  {m['title']} | ch {m['read_chapter']} / {m['latest_chapter']} {unread}")
