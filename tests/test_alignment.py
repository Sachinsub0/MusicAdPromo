from shared.alignment_v7 import validate_words,approximate_alignment

def test_draft():
    w=approximate_alignment('hello दुनिया',10)
    assert len(w)==2 and w[-1]['end']==10

def test_validation():
    assert validate_words([{'word':'hola','start':0,'end':1}],10)[0]['word']=='hola'
