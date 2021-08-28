## OSM Handler

* 모든 osm 관련 파일(osm,xml,pbf) 등을 넣으면 node, way, relation 3가지 오브젝트를 구분하여 데이터를 받아오는 OSMHandler

* dependecy : `pip3 install osmium`

###
##

`test_michigan.osm` 파일과 module화 되어있는 `OSMHandler.py` 파일, 간단한 test를 진행한 `main.py` 파일 첨부

__세 파일을 같은 디렉토리에 넣고, main.py만 돌리면 됨__

[reference](https://docs.osmcode.org/pyosmium/latest/ref_osm.html#osmium.osm.RelationMember)
