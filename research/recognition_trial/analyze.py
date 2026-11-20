"""Score voluntarily supplied participant exports for the fixed 2018 recognition trial."""
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


def normalize(name):
    return ''.join(ch for ch in unicodedata.normalize('NFKD', name).casefold() if ch.isalnum())


def analyze(key, responses):
    pairs = {p['item']: p['names'] for p in key['pairs']}
    if set(pairs) != set(range(1, 9)) or len(key['pairs']) != 8:
        raise ValueError('Unexpected study key')
    cells = defaultdict(Counter)
    people, participants = Counter(), set()
    for record in responses:
        pid, form, experience = (record[k] for k in ('participant', 'form', 'experience'))
        if (record['study'] != key['study'] or record['keyId'] != key['keyId']
                or not re.fullmatch('[0-9a-f]{32}', pid) or pid in participants
                or form not in ('A', 'B') or experience not in ('closely', 'occasionally')):
            raise ValueError('Duplicate participant or incompatible response metadata')
        trials = record['responses']
        if len(trials) != 8 or {r['item'] for r in trials} != set(pairs):
            raise ValueError('Missing or duplicated pair')
        participants.add(pid)
        people[experience, form] += 1
        for row in trials:
            item, choice, guesses = row['item'], row['choice'], row['guesses']
            if (type(choice) is not int or choice not in (0, 1) or not isinstance(guesses, list)
                    or len(guesses) != 2 or any(not isinstance(g, str) or len(g) > 85 for g in guesses)):
                raise ValueError('Invalid choice or guess')
            shown = item % 2 == (1 if form == 'A' else 0)
            cell = cells[item, shown]
            cell['prompts'] += 2
            cell['abstentions'] += sum(not g.strip() for g in guesses)
            cell['correct'] += sum(normalize(guess) == normalize(name) for guess, name in zip(guesses, pairs[item]))
            cell['firstPlayerChosen'] += int(choice == 0)
            cell['choices'] += 1

    rows, contrasts = [], []
    for item in sorted(pairs):
        row = {'item': item}
        for shown, label in [(True, 'schoolShown'), (False, 'schoolHidden')]:
            cell = cells[item, shown]
            row[label] = dict(cell) if cell['prompts'] else None
        if row['schoolShown'] and row['schoolHidden']:
            displayed, masked = cells[item, True], cells[item, False]
            contrasts.append(displayed['correct']/displayed['prompts'] - masked['correct']/masked['prompts'])
        rows.append(row)
    return {'participants': len(participants),
            'experienceByForm': {e: {f: people[e, f] for f in ('A', 'B')} for e in ('closely', 'occasionally')},
            'pairs': rows, 'equalPairRecognitionDifference': mean(contrasts) if len(contrasts) == len(pairs) else None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('key', type=Path)
    parser.add_argument('responses', nargs='*', type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(json.loads(args.key.read_text()), [json.loads(p.read_text()) for p in args.responses]), indent=2))
