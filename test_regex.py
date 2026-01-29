#!/usr/bin/env python3

import re

messages = [
    'can u equip thorn',
    'can u equip the last word',
    'equip thorn',
    'equip the last word'
]

for message in messages:
    match = re.search(r'\bequip\s+(?:my\s+)?(.+)$', message, re.IGNORECASE)
    if match:
        print(f'"{message}" -> Match: "{match.group(1).strip()}"')
    else:
        print(f'"{message}" -> No match')