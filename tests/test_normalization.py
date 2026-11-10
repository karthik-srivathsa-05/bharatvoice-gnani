"""One captured Prisma transcript and bounded synthetic grammar regressions."""
import pytest
from app.normalization import normalize
from app.engine import Session,process

REAL = 'There is no water at house number forty-two. Sorry. Not forty-two, house number twenty-four. The problem started on Monday.'

def test_real_prisma_regression():
    s=process(Session(),REAL,'gnani_live');i=s.issues[0]
    assert (i.category,i.location,i.time_reference)==('water','House 24','Monday')
    assert i.view()['status']=='awaiting_confirmation' and not i.confirmed
    assert i.original_text==REAL and s.turns[0]['text']==REAL
    assert 'house 42' in s.turns[0]['extraction_text']
    assert any(r.before=='House 42' and r.after=='House 24' and r.evidence==REAL for r in i.revisions)

@pytest.mark.parametrize('address', ['house twenty four','house number twenty-four','house no 24','house no. 24','house number 24','House 24'])
def test_house_variants(address):
    assert process(Session(),'Water at '+address).issues[0].location=='House 24'

@pytest.mark.parametrize('words,n', [('zero',0),('nineteen',19),('ninety-nine',99),('one hundred',100),('two hundred and forty-two',242),('nine hundred ninety nine',999)])
def test_numbers(words,n):
    assert normalize('house number '+words)==f'house {n}'

def test_all_under_hundred():
    from app.normalization import SMALL,TENS
    for word,n in SMALL.items(): assert normalize('house '+word)==f'house {n}'
    for word,n in TENS.items():
        for unit,k in list(SMALL.items())[:10]:
            spoken=word if k==0 else word+' '+unit
            assert normalize('house '+spoken)==f'house {n+k}'

def test_repeated_spoken_corrections():
    s=process(Session(),'Water at house forty-two')
    process(s,'Sorry. House twenty-four.');process(s,'Actually house twenty-six.')
    assert s.issues[0].location=='House 26'
    assert [(r.before,r.after) for r in s.issues[0].revisions]==[(None,'House 42'),('House 42','House 24'),('House 24','House 26')]

def test_multi_issue_scope():
    s=process(Session(),REAL+' Drainage at house number fifty-six.')
    assert [i.location for i in s.issues]==['House 24','House 56']
    process(s,'Water actually house number thirty-one.')
    assert [i.location for i in s.issues]==['House 31','House 56']

def test_ambiguous_correction_needs_target():
    s=process(Session(),'Water house ten and drainage house eleven')
    process(s,'Sorry. House twenty-four.')
    assert [i.location for i in s.issues]==['House 10','House 11']
    assert all(i.blocked and not i.confirmed for i in s.issues)

def test_same_category_ambiguity():
    s=process(Session(),'Water house ten and water house eleven')
    process(s,'Water actually house twenty-four')
    assert [i.location for i in s.issues]==['House 10','House 11']
    assert all(i.blocked for i in s.issues)

@pytest.mark.parametrize('text',['Water at house number','Water sorry not forty-two','Water at house twenty four thousand','Water at house 24 thousand','Water house ippatnaalku'])
def test_incomplete_unsupported_never_inferred(text):
    i=process(Session(),text).issues[0]
    assert i.location is None and not i.confirmed

def test_number_normalization_does_not_change_time_or_other_issue():
    s=process(Session(),'Water at house twenty-four since two days and garbage near school')
    assert s.issues[0].time_reference=='Two Days'
    assert s.issues[1].location=='School'

def test_multiple_addresses_without_correction_stay_blocked():
    i=process(Session(),'Water house twenty-four or house forty-two').issues[0]
    assert i.blocked and not i.confirmed

def test_time_correction_does_not_authorize_multiple_locations():
    i=process(Session(),'Water sorry Monday not Sunday at house twenty-four and house forty-two').issues[0]
    assert i.location is None and i.blocked

def test_uncertain_correction_keeps_previous_location():
    s=process(Session(),'Water house ten')
    process(s,'Sorry house twenty-four or house forty-two')
    assert s.issues[0].location=='House 10' and s.issues[0].blocked
