#!/usr/bin/env python3
"""Search the bundled 2012 Cooper Book transcription without third-party packages."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
FIELDS = ('all', 'title', 'first-line', 'lyrics', 'composer', 'lyric-source',
          'meter', 'lyric-date', 'composition-date')


def normalize(text):
    text = unicodedata.normalize('NFKD', text).casefold()
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.replace('’', '').replace("'", '')
    return ' '.join(re.sub(r'[^\w\s]', ' ', text).split())


def values(song, field):
    metadata = song['metadata']
    if field == 'all':
        return [*metadata.values(), song['lyrics']]
    if field == 'title':
        return [metadata.get(key, '') for key in ('Title', 'Alternative Title', 'Collation')]
    if field == 'first-line':
        return [next((line for line in song['lyrics'].splitlines() if line.strip()), '')]
    if field == 'lyrics':
        return [song['lyrics']]
    if field == 'composer':
        return [v for k, v in metadata.items() if k.endswith(' Composer')]
    if field == 'composition-date':
        return [v for k, v in metadata.items() if k.endswith(' Composition Date')]
    return [metadata.get({'lyric-source': 'Lyrics', 'meter': 'Meter',
                          'lyric-date': 'Lyrics Date'}[field], '')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='?', default='')
    parser.add_argument('--page', action='append', default=[])
    parser.add_argument('--field', choices=FIELDS, default='all')
    parser.add_argument('--limit', type=int, default=20, help='Maximum results; 0 returns all.')
    parser.add_argument('--full', action='store_true', help='Include the complete lyric text.')
    args = parser.parse_args()
    query = normalize(args.query)
    if args.limit < 0:
        parser.error('--limit must be nonnegative')
    if args.query and not query:
        parser.error('query must contain a letter or number')
    if not query and not args.page:
        parser.error('provide a query or --page')
    songs = json.loads((SKILL / 'references/songs.json').read_text(encoding='utf-8'))
    sources = json.loads((SKILL / 'references/sources.json').read_text(encoding='utf-8'))
    pages = {page.strip().lower() for page in args.page}
    matches = []
    for page, song in songs.items():
        if pages and page not in pages:
            continue
        if query and not any(query in normalize(value) for value in values(song, args.field)):
            continue
        result = {'page': page, 'source_url': sources[page], 'metadata': song['metadata'],
                  'opening_lines': [line for line in song['lyrics'].splitlines() if line.strip()][:2]}
        if args.full:
            result['lyrics'] = song['lyrics']
        matches.append(result)
    selected = matches[:args.limit] if args.limit else matches
    print(json.dumps({'total': len(matches), 'returned': len(selected),
                      'truncated': len(selected) < len(matches), 'results': selected},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
