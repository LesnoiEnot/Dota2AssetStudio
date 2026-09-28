from app.liquipedia_api import LiquipediaCatalog

def test_parse_gameasset_file():
    c = LiquipediaCatalog(__import__('pathlib').Path('/tmp/das-cache'), print)
    data = {
        'query': {'pages': {
            '1': {'title': 'File:Kobold Soldier icon dota2 gameasset.png',
                  'imageinfo': [{'url': 'https://upload.test/kobold.png'}]}
        }}
    }
    rows = c._parse(data)
    assert rows[0].source_name == 'Kobold Soldier'
    assert rows[0].url.endswith('kobold.png')
