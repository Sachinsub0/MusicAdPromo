from shared.alignment_v7 import preserve_alignment_on_edit
from backend.main import MAX_BYTES

def test_limit():
    assert MAX_BYTES==200*1024*1024

def test_held_word_and_correction_preserved():
    original=[{'word':'I','start':0.0,'end':0.3}, {'word':'loooove','start':0.3,'end':2.8}, {'word':'you','start':2.8,'end':3.2}]
    result=preserve_alignment_on_edit(original,'I love you',10)
    assert result[1]=={'word':'love','start':0.3,'end':2.8}
    assert result[2]['start']==2.8

def test_insert_keeps_existing_words():
    original=[{'word':'hello','start':0.2,'end':0.8},{'word':'world','start':1.4,'end':2.0}]
    result=preserve_alignment_on_edit(original,'hello beautiful world',10)
    assert result[0]['end']==0.8
    assert result[2]['start']==1.4
    assert result[1]['start']>=0.8 and result[1]['end']<=1.4
