from app.liquipedia_api import LiquipediaCatalog
from app.models import AssetRecord

def test_match_by_normalized_name(tmp_path):
    c=LiquipediaCatalog(tmp_path, print)
    c.maps['neutral_creeps']={'kobold soldier':AssetRecord('', 'Kobold Soldier','https://x','Liquipedia Commons')}
    assert c.find('neutral_creeps','Kobold Soldier') is not None
