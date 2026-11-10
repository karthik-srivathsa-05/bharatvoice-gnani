"""Conservative English house-number grammar; never rewrites stored source text."""
import re

SMALL = dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(), range(20)))
TENS = dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(), range(20,100,10)))
UNIT = r'(?:zero|one|two|three|four|five|six|seven|eight|nine)'
UNDER100 = rf'(?:(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:[ -]+{UNIT})?|(?:ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)|{UNIT})'
NUMBER = rf'(?:{UNIT}\s+hundred(?:[ -]+(?:and\s+)?{UNDER100})?|{UNDER100}|\d+)'
HOUSE = re.compile(rf'\bhouse\s+(?:(?:number|no\.?)\s+)?(?P<number>{NUMBER})(?![\w-])', re.I)
# Reject partial parses of unsupported number sequences rather than invent addresses.
CONTINUATION = re.compile(r'^[ -]+(?:and\s+)?(?:hundred|thousand|' + '|'.join(SMALL.keys() | TENS.keys()) + r')\b', re.I)

def number_value(text):
    tokens=text.lower().replace('-', ' ').split()
    if text.isdigit(): return int(text)
    if 'hundred' in tokens:
        n=tokens.index('hundred')
        return SMALL[tokens[0]]*100 + sum(SMALL.get(t,TENS.get(t,0)) for t in tokens[n+1:] if t!='and')
    return sum(SMALL.get(t,TENS.get(t,0)) for t in tokens)

def normalize(text):
    """Normalize only explicit house addresses. Bare numbers retain their meaning."""
    def replace(m):
        if CONTINUATION.match(text[m.end():]): return 'house [unsupported number]'
        return f'house {number_value(m["number"])}'
    return HOUSE.sub(replace,text)
