import artiv_mission_navi.info_node
import artiv_mission_navi.OSMHandler
from operator import itemgetter
import os
from shapely.geometry import Point, Polygon, LineString, MultiPoint
from shapely.ops import nearest_points

cwd = os.getcwd()
cwd_lst = cwd.split('/')

map_dir = '/' + cwd_lst[1] + '/' + cwd_lst[2] + '/ARTIV_mapdata'

dgist = "/osm_DGIST/"
k_city = "/osm_KCity/"
guidance_line_file = "A2_LINK.osm"

node_idx = 0
prev_target_node = []

def get_nearest_path_idx(path_idx, paths, latitude, longitude):
    current_point = Point(longitude, latitude)
    dist_idx_lst = [None, float('inf')]

    if path_idx == None :
        for i in range(len(paths)):
            temp_dist = current_point.distance(paths[i])
            if dist_idx_lst[1] > temp_dist :
                dist_idx_lst = [i, temp_dist]

    else :
        #현재 path의 앞뒤로 2개씩만 탐색
        for i in range(path_idx-2, path_idx+3):
            temp_dist = current_point.distance(paths[i])
            if dist_idx_lst[1] > temp_dist :
                dist_idx_lst = [i, temp_dist]
    return dist_idx_lst[0]


def get_node_from_node_id(nodes, node_id):
    global node_idx
    global prev_target_node

    taget_node = []  
  
    for item in nodes:
        if item[1] == node_id:
            target_node = [item[1],item[2],item[3],item[5],item[6]]
    index = node_idx

    if target_node != prev_target_node :
        prev_target_node = target_node
        node_idx+=1

    return target_node

    
def find_nearest_node(path_idx, paths, path_node, nodes_lst, latitude, longitude):
    #path_idx is current path index
    #paths is set of MultiPoint
    #path_node is set of node(id and Point)
    #nodes_lst is list with tag

    current_point = Point(longitude, latitude)
    current_path = paths[path_idx]
    np = nearest_points(current_path, current_point)[0]
    
    for path in path_node:
        if path[1] == np:
            current_node_id = path[0]

    node_info = get_node_from_node_id(nodes_lst, current_node_id)
    return node_info



class DGIST_Guidance_Line:
    def __init__(self, global_path, distance, count):
        #import info_node
        add_info_node = artiv_mission_navi.info_node.infoNode(global_path, distance, 'dgist')
        self.final_nodes = add_info_node.final_nodes

        #constance variables
        self.file_name = map_dir+ dgist + guidance_line_file
        self.file_data = artiv_mission_navi.OSMHandler.OSM_data(self.file_name)
        self.nodes = self.final_nodes
        self.ways = artiv_mission_navi.OSMHandler.ways(self.file_data)
        self.count = count

        self.for_path_node = add_info_node.temp_node
        self.current_path_idx = None

        #changeable variables
        self.current_node = None
        self.prev_node = None

        #global path를 바탕으로 path way생성
        self.path_ways = []
        point_lst = []

        for p in self.for_path_node :
            point_lst.append(p[1])

        for i in range(len(point_lst)//count):
            self.path_ways.append(MultiPoint(point_lst[i*count:(i+1)*count]))
        self.path_ways.append(MultiPoint(point_lst[(len(point_lst)//count)*count:]))


    def update(self, latitude, longitude):
        nearest_path = get_nearest_path_idx(self.current_path_idx, self.path_ways, latitude, longitude)
        self.current_path_idx = nearest_path

        temp_nearest_node = find_nearest_node(self.current_path_idx, self.path_ways, self.for_path_node, self.nodes, latitude, longitude)
        current_node = temp_nearest_node

        if self.current_node == None and self.prev_node == None: #boundary case - first case
            self.current_node = current_node

        elif self.current_node != None and self.prev_node == None: #boundary case - second case
            self.prev_node = self.current_node
            self.current_node = current_node
            if self.prev_node == self.current_node: # 업데이트 속도가 빨라서
                self.prev_node = None

        else: #general case
            if current_node != self.current_node:
                self.prev_node = self.current_node
                self.current_node = current_node

    def get_current_node(self):
        return self.current_node

    def get_prev_node(self):
        return self.prev_node

    def get_forward_path(self):
        global node_idx

        if (node_idx+1) % self.count == 0:
            final_forward_path = self.path_ways[self.current_path_idx+1]
        else :
            final_forward_path = self.path_ways[self.current_path_idx]
        
        return final_forward_path



class KCity_Guidance_Line:
    def __init__(self, global_path, distance, count):
        #import info_node
        add_info_node = artiv_mission_navi.info_node.infoNode(global_path, distance, 'k_city')
        self.final_nodes = add_info_node.final_nodes

        #constance variables
        self.file_name = map_dir+ k_city + guidance_line_file
        self.file_data = artiv_mission_navi.OSMHandler.OSM_data(self.file_name)
        self.nodes = self.final_nodes
        self.ways = artiv_mission_navi.OSMHandler.ways(self.file_data)
        self.count = count

        self.for_path_node = add_info_node.temp_node
        self.current_path_idx = None

        #changeable variables
        self.current_node = None
        self.prev_node = None

        #global path를 바탕으로 path way생성
        self.path_ways = []
        point_lst = []

        for p in self.for_path_node :
            point_lst.append(p[1])

        for i in range(len(point_lst)//count):
            self.path_ways.append(MultiPoint(point_lst[i*count:(i+1)*count]))
        self.path_ways.append(MultiPoint(point_lst[(len(point_lst)//count)*count:]))


    def update(self, latitude, longitude):
        nearest_path = get_nearest_path_idx(self.current_path_idx, self.path_ways, latitude, longitude)
        self.current_path_idx = nearest_path

        temp_nearest_node = find_nearest_node(self.current_path_idx, self.path_ways, self.for_path_node, self.nodes, latitude, longitude)
        current_node = temp_nearest_node

        if self.current_node == None and self.prev_node == None: #boundary case - first case
            self.current_node = current_node

        elif self.current_node != None and self.prev_node == None: #boundary case - second case
            self.prev_node = self.current_node
            self.current_node = current_node
            if self.prev_node == self.current_node: # 업데이트 속도가 빨라서
                self.prev_node = None

        else: #general case
            if current_node != self.current_node:
                self.prev_node = self.current_node
                self.current_node = current_node

    def get_current_node(self):
        return self.current_node

    def get_prev_node(self):
        return self.prev_node

    def get_forward_path(self):
        global node_idx

        if (node_idx+1) % self.count == 0:
            final_forward_path = self.path_ways[self.current_path_idx+1]
        else :
            final_forward_path = self.path_ways[self.current_path_idx]
        
        return final_forward_path


if __name__ == '__main__':
    pass
