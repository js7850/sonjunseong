# 어린이보호구역으로부터의 최단거리를 구하는 함수 구현            

import OSMHandler

def find_Prohibited_Areas(osm_file):
    osm_data = OSMHandler.OSM_data(osm_file)

    prohibited_way = []
    for item in osm_data:
        if item[0] == 'way' and item[4]['Kind'] == '7':
            prohibited_way.append(item)

    node_list = []
    for item in osm_data:
        if item[0] == 'node':
            node_list.append([item[1],item[2],item[3]])

    prohibited_node = []
    for way in prohibited_way:
        temp_node_id_list = way[2]
        for node_id in temp_node_id_list:
            for node in node_list:
                if node[0] == node_id:
                    prohibited_node.append(node)

    prohibited_points = []
    for node in prohibited_node:
        prohibited_points.append([node[1],node[2]])
    
    return prohibited_points

def find_nearest_point(points, latitude, longitude):
    nearest_distance = abs(points[0][0] - latitude) + abs(points[0][1] - longitude)
    nearest_point = points[0]
    for i in range(1,len(points)):
        temp_distance = abs(points[i][0] - latitude) + abs(points[i][1] - longitude)
        if nearest_distance > temp_distance:
            nearest_distance = temp_distance
            nearest_point = points[i]

    return nearest_point                     

def get_complete_node(osm_file,latitude, longitude):
    osm_data = OSMHandler.OSM_data(osm_file)
    
    for item in osm_data:
        if item[0] == 'node' and item[2] == latitude and item[3] == longitude:
            return item

def nearest_point_to_prohibited_area(file_name,latitude,longitude):
    prohibited_area = find_Prohibited_Areas(file_name)

    nearest_point = find_nearest_point(prohibited_area, latitude, longitude)
    return get_complete_node(file_name,nearest_point[0],nearest_point[1])

if __name__ == '__main__':
    file_name = "A3_DRIVEWAYSECTION.osm"
    latitude , longitude = 35.70812994, 128.454553428   
    a = nearest_point_to_prohibited_area(file_name,latitude,longitude)
    print(a)
