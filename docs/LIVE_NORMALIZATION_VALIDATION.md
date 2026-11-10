# English house-number fix validation — 2026-11-10

A genuine repeat request through the unchanged `GnaniPrisma` adapter returned
HTTP **200**, model **prisma-v3.0**, request ID
`ad7386c0-d1de-4900-9033-b32dc89069d2`.
Input: the retained offline Flite synthetic speech WAV, mono PCM 16 kHz,
8.215 seconds, RMS 0.1575, peak 0.7024. No human recording or secret is committed.

Actual API transcript (unchanged):

> There is no water at house number forty-two. Sorry. Not forty-two, house number twenty-four. The problem started on Monday.

Passing this actual transcript directly to the existing engine produced:

- category: `water`
- location: `House 24`
- time reference: `Monday`
- status: `awaiting_confirmation`
- confirmed: `false`; missing fields: none
- location revisions: unset → House 42 → House 24
- time revision: unset → Monday

Each revision retains the original transcript fragment as evidence. The original
turn text is unchanged; a separate extraction representation contains normalized
house numbers. Neither the test nor the application auto-confirms this issue.

## Measured comparison

| Case | Previous engine | Improved engine | Simple baseline |
| --- | --- | --- | --- |
| Captured real transcript, expected water / House 24 / Monday | location missing; failed | exact match | location missing; failed |
| Five existing hand-authored synthetic fixtures | 5/5 | 5/5 | 0/5 |

The previous engine was loaded from an unchanged local copy for the comparison.
The evaluation script was run before and after the fix. The simple baseline
still uses the first recognized category/location/time without corrections.
These are known regression cases, not a held-out benchmark or a multilingual
accuracy estimate. The live test demonstrates this one synthetic English clip
through Gnani; it does not establish Kannada-English number coverage.

The full suite passes with **80 tests** (the original 52 plus 28 regressions),
with one upstream Starlette/httpx deprecation warning. Added coverage includes
the exact captured transcript, all English zero–99 values, hundreds, address
variants, repeated corrections, issue/field scope, ambiguous alternatives,
incomplete inputs, original evidence retention and explicit API confirmation.
See the README normalization section for supported grammar and limitations.
