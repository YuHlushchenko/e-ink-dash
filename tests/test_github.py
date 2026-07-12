"""
Smoke test for api/github.py — hits the real GitHub API (needs GITHUB_TOKEN/
GITHUB_USERNAME in .env). Run:

    python3 tests/test_github.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')
token = os.getenv('GITHUB_TOKEN', '')
username = os.getenv('GITHUB_USERNAME', '')
print(f'TOKEN: {token[:8]}...{token[-4:] if token else "EMPTY"}')
print(f'USERNAME: {username}')

from api.github import get_contributions, fetch_contributions

print('--- cache-only read (before any fetch) ---')
data, err = get_contributions()
print('error:', err)
print('cached:', 'none' if data is None else f"total={data['total']}, days={len(data['days'])}")

print('--- network fetch ---')
data, err = fetch_contributions()
print('error:', err)
if data:
    print(f"total contributions: {data['total']}")
    print(f"days returned: {len(data['days'])}")
    sample = list(data['days'].items())[:5]
    print('sample:', sample)

print('--- cache-only read (after fetch) ---')
data, err = get_contributions()
print('error:', err)
print('cached:', 'none' if data is None else f"total={data['total']}, days={len(data['days'])}")
