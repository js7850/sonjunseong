- vision 과 lidar의 segmentation box 가 겹치는 경우는 vision만 나타내었다. (어자피 이미지 상에서 안보이는 lidar의 segmentation box는 결국 이미지에서 보이는 객체 보다 뒤에 있다는 것이므로 삭제해도 무방)
- vision과 겹치지 않는 lidar segmentation box는 나타내었음 (class_id로 

개선해야 할 사항
- lidar의 segmentation box 끼리 겹치는 경우에 대해서 가장 가까운 이미지만 남기고 다 지워야 함. 
