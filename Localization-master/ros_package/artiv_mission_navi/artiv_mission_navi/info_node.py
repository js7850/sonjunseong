import os
import math
import artiv_mission_navi.map_parser
import artiv_mission_navi.OSMHandler
import artiv_mission_navi.haversine_distance
from shapely.geometry import Point, Polygon

cwd = os.getcwd()
cwd_lst = cwd.split('/')

map_dir = '/' + cwd_lst[1] + '/' + cwd_lst[2] + '/ARTIV_mapdata'

default = 'k_city'
dgist = "/osm_DGIST/"
k_city = "/osm_KCity/"


class infoNode(object):

    def __init__(self, global_path, distance, location=default):

        #Set the Map!
        if location == 'dgist':
            self.osm_data = artiv_mission_navi.OSMHandler.OSM_data(map_dir+ dgist + "A2_LINK.osm")
            self.loc = 'dgist'
        elif location == 'k_city':
            self.osm_data = artiv_mission_navi.OSMHandler.OSM_data(map_dir+ k_city + "A2_LINK.osm")
            self.loc = 'k_city'

        #Set the Global Path - Use Way ID!
        paths = global_path

        #Set the distance to noti! (meter)
        self.meter = distance

        all_ways = artiv_mission_navi.OSMHandler.ways(self.osm_data)
        self.all_nodes = artiv_mission_navi.OSMHandler.nodes(self.osm_data)

        self.path_way = [] #way information of paths

        for path in paths :
            for way in all_ways :
                if way[1] == path :
                    self.path_way.append(way)

        self.temp_node = [] #node information of all paths

        #Saving latitude and longitude information using node ID
        #Duplicate nodes are deleted
        for node in self.path_way[0][2]:
            for nd in self.all_nodes:
                if nd[1] == node :
                    self.temp_node.append([nd[1], Point(nd[3], nd[2])])

        for way in self.path_way[1:]:
            for node in way[2][1:]:
                for nd in self.all_nodes :
                    if nd[1] == node :
                        self.temp_node.append([nd[1], Point(nd[3], nd[2])])

        #ADD THE INFORMATION
        self.polygonSetting("protected_areas")
        self.polygonSetting("crosswalks")
        self.polygonSetting("bump_crosswalks")
        self.polygonSetting("bicycle_crosswalks")
        self.polygonSetting("speedbumps")
        self.missionSetting("mission_areas")
        self.linestringSetting("stoplines")

        self.final_nodes = self.all_nodes


    def missionSetting(self, mission):
        if mission == 'mission_areas' :
            missionzone = artiv_mission_navi.map_parser.mission_areas_polygons(self.loc)
        missionzone_dict = dict()

        for i in range(len(missionzone)) :
            within_lst = []
            for nd in self.temp_node:
                if nd[1].within(missionzone[i][0]):
                    within_lst.append(nd)

            if len(within_lst) != 0:
                missionzone_dict[int(missionzone[i][1])] = within_lst

        temp_keys_lst = missionzone_dict.keys()
        temp_keys_lst = [int(x) for x in temp_keys_lst]

        index_dict = dict()

        for i in temp_keys_lst:
            index_dict[i] = [missionzone_dict[i][0], missionzone_dict[i][-1]]

        #Add tag
        for i in temp_keys_lst:
            first_idx = self.temp_node.index(index_dict[i][0])
            last_idx = self.temp_node.index(index_dict[i][1])

            first_point = self.temp_node[first_idx][1]
            last_point = self.temp_node[last_idx][1]

            approaching_lst = self.temp_node[:first_idx]
            missionzone_lst = self.temp_node[first_idx:last_idx+1]
            leaving_lst = self.temp_node[last_idx+1:]

            for miss in missionzone:
                if int(miss[1]) == i : 
                    #Add the tags of approaching nodes
                    dist = 0

                    for idx in range(len(approaching_lst)):
                        if idx == 0:
                            d = approaching_lst[-(idx+1)][1].distance(miss[0]) * (40010040 / 360)

                        else :
                            d = approaching_lst[-(idx+1)][1].distance(approaching_lst[-idx][1]) * (40010040 / 360)
                        dist += d

                        if dist <= self.meter :
                            for nd in self.all_nodes :
                                if nd[1] == approaching_lst[-(idx+1)][0] :
                                    cnt = nd[4]
                                    cnt += 1
                                    nd[4] = cnt
                                    '''
                                    temp_dict = dict()
                                    temp_dict[mission + " " + str(i)] = round(dist,2)
                                    nd.append(temp_dict)
                                    '''
                                    temp_dict = nd[6]
                                    temp_dict[mission + " " + str(i)] = [round(dist,2), miss[2]]
                                    
                    #Add the tags of schoolzone nodes
                    dist = 0
                    for ms_nd in missionzone_lst:
                        for nd in self.all_nodes:
                            if nd[1] == ms_nd[0] :
                                cnt = nd[4]
                                cnt += 1
                                nd[4] = cnt
                                '''
                                temp_dict = dict()
                                temp_dict[mission + " " + str(i)] = dist
                                nd.append(temp_dict)
                                '''
                                temp_dict = nd[6]
                                temp_dict[mission + " " + str(i)] = [dist, miss[2]]
                                
                    #Add the tags of leaving nodes
                    dist = 0
                    for idx in range(len(leaving_lst)):
                        if idx == 0:
                            d = leaving_lst[idx][1].distance(miss[0]) * (40010040 / 360)
                        else :
                            d = leaving_lst[idx][1].distance(leaving_lst[idx-1][1]) * (40010040 / 360)
                        dist += d
                            
                        if dist <= self.meter :
                            for nd in self.all_nodes :
                                if nd[1] == leaving_lst[idx][0] :
                                    cnt = nd[4]
                                    cnt += 1
                                    nd[4] = cnt
                                    '''
                                    temp_dict = dict()
                                    temp_dict[mission + " " + str(i)] = round(-dist,2)
                                    nd.append(temp_dict)

                                    '''
                                    temp_dict = nd[6]
                                    temp_dict[mission + " " + str(i)] = [round(-dist,2), miss[2]]

           




            """
            #Add the tags of approaching nodes
            dist = 0

            for idx in range(len(approaching_lst)):
                if idx == 0:
                    for miss in missionzone:
                        if int(miss[1]) == i : 
                            d = approaching_lst[-(idx+1)][1].distance(miss[0]) * (40010040 / 360)

                else :
                    d = approaching_lst[-(idx+1)][1].distance(approaching_lst[-idx][1]) * (40010040 / 360)
                dist += d

                if dist <= self.meter :
                    for nd in self.all_nodes :
                        if nd[1] == approaching_lst[-(idx+1)][0] :
                            cnt = nd[4]
                            cnt += 1
                            nd[4] = cnt
                            '''
                            temp_dict = dict()
                            temp_dict[mission + " " + str(i)] = round(dist,2)
                            nd.append(temp_dict)
                            '''
                            temp_dict = nd[6]
                            temp_dict[mission + " " + str(i)] = round(dist,2)
                            
            #Add the tags of schoolzone nodes
            dist = 0
            for ms_nd in missionzone_lst:
                for nd in self.all_nodes:
                    if nd[1] == ms_nd[0] :
                        cnt = nd[4]
                        cnt += 1
                        nd[4] = cnt
                        '''
                        temp_dict = dict()
                        temp_dict[mission + " " + str(i)] = dist
                        nd.append(temp_dict)
                        '''
                        temp_dict = nd[6]
                        temp_dict[mission + " " + str(i)] = dist
                        
            #Add the tags of leaving nodes
            dist = 0
            for idx in range(len(leaving_lst)):
                if idx == 0:
                    for miss in missionzone:
                        if int(miss[1]) == i : 
                            d = leaving_lst[idx][1].distance(miss[0]) * (40010040 / 360)
                else :
                    d = leaving_lst[idx][1].distance(leaving_lst[idx-1][1]) * (40010040 / 360)
                dist += d
                    
                if dist <= self.meter :
                    for nd in self.all_nodes :
                        if nd[1] == leaving_lst[idx][0] :
                            cnt = nd[4]
                            cnt += 1
                            nd[4] = cnt
                            '''
                            temp_dict = dict()
                            temp_dict[mission + " " + str(i)] = round(-dist,2)
                            nd.append(temp_dict)

                            '''
                            temp_dict = nd[6]
                            temp_dict[mission + " " + str(i)] = round(-dist,2)
            """


        return self.all_nodes


    def polygonSetting(self, polygon):
        if polygon == "protected_areas":
            schoolzone = artiv_mission_navi.map_parser.protected_areas_polygons(self.loc)

        elif polygon == 'crosswalks' :
            schoolzone = artiv_mission_navi.map_parser.crosswalks_polygons(self.loc)

        elif polygon == 'bump_crosswalks' :
            schoolzone = artiv_mission_navi.map_parser.bump_crosswalks_polygons(self.loc)

        elif polygon == 'bicycle_crosswalks' :
            schoolzone = artiv_mission_navi.map_parser.bicycle_crosswalks_polygons(self.loc)

        elif polygon == 'speedbumps' :
            schoolzone = artiv_mission_navi.map_parser.speedbumps_polygons(self.loc)

        elif polygon == 'mission_areas' :
            schoolzone = artiv_mission_navi.map_parser.mission_areas_polygons(self.loc)

        schoolzone_dict = dict()

        for i in range(len(schoolzone)) :
            within_lst = []
            for nd in self.temp_node:
                if nd[1].within(schoolzone[i]):
                    within_lst.append(nd)
            
            if len(within_lst) != 0:
                schoolzone_dict[i+1] = within_lst
       
        temp_keys_lst = schoolzone_dict.keys()

        index_dict = dict()

        for i in temp_keys_lst:
            index_dict[i] = [schoolzone_dict[i][0], schoolzone_dict[i][-1]]

        #Add tag
        for i in temp_keys_lst:
            first_idx = self.temp_node.index(index_dict[i][0])
            last_idx = self.temp_node.index(index_dict[i][1])

            first_point = self.temp_node[first_idx][1]
            last_point = self.temp_node[last_idx][1]

            approaching_lst = self.temp_node[:first_idx]
            schoolzone_lst = self.temp_node[first_idx:last_idx+1]
            leaving_lst = self.temp_node[last_idx+1:]

            #Add the tags of approaching nodes
            dist = 0

            for idx in range(len(approaching_lst)):
                if idx == 0:
                    d = approaching_lst[-(idx+1)][1].distance(schoolzone[i-1]) * (40010040 / 360)

                else :
                    d = approaching_lst[-(idx+1)][1].distance(approaching_lst[-idx][1]) * (40010040 / 360)
                dist += d

                if dist <= self.meter :
                    for nd in self.all_nodes :
                        if nd[1] == approaching_lst[-(idx+1)][0] :
                            cnt = nd[4]
                            cnt += 1
                            nd[4] = cnt
                            
                            temp_dict = nd[5]
                            temp_dict[polygon + " " + str(i)] = round(dist,2)

            #Add the tags of schoolzone nodes
            dist = 0
            for sh_nd in schoolzone_lst:
                for nd in self.all_nodes:
                    if nd[1] == sh_nd[0] :
                        cnt = nd[4]
                        cnt += 1
                        nd[4] = cnt
                        
                        temp_dict = nd[5]
                        temp_dict[polygon + " " + str(i)] = dist

            #Add the tags of leaving nodes
            dist = 0
            for idx in range(len(leaving_lst)):
                if idx == 0:
                    d = leaving_lst[idx][1].distance(schoolzone[i-1]) * (40010040 / 360)
                else :
                    d = leaving_lst[idx][1].distance(leaving_lst[idx-1][1]) * (40010040 / 360)
                dist += d
                    
                if dist <= self.meter :
                    for nd in self.all_nodes :
                        if nd[1] == leaving_lst[idx][0] :
                            cnt = nd[4]
                            cnt += 1
                            nd[4] = cnt
                            
                            temp_dict = nd[5]
                            temp_dict[polygon + " " + str(i)] = round(-dist,2)

        return self.all_nodes

    def linestringSetting(self, linestring):
        if linestring == "stoplines":
            schoolzone = artiv_mission_navi.map_parser.stoplines_linestrings(self.loc)

        schoolzone_dict = dict()

        for i in range(len(schoolzone)) :
            within_lst = []
            for nd in self.temp_node:
                if nd[1].within(schoolzone[i]):
                    within_lst.append(nd)
            
            if len(within_lst) != 0:
                schoolzone_dict[i+1] = within_lst
       
        temp_keys_lst = schoolzone_dict.keys()

        index_dict = dict()

        for i in temp_keys_lst:
            index_dict[i] = [schoolzone_dict[i][0], schoolzone_dict[i][-1]]

        #Add tag
        for i in temp_keys_lst:
            first_idx = self.temp_node.index(index_dict[i][0])
            last_idx = self.temp_node.index(index_dict[i][1])

            first_point = self.temp_node[first_idx][1]
            last_point = self.temp_node[last_idx][1]

            approaching_lst = self.temp_node[:first_idx]
            schoolzone_lst = self.temp_node[first_idx:last_idx+1]
            leaving_lst = self.temp_node[last_idx+1:]

            #Add the tags of approaching nodes
            dist = 0

            for idx in range(len(approaching_lst)):
                if idx == 0:
                    d = approaching_lst[-(idx+1)][1].distance(schoolzone[i-1]) * (40010040 / 360)

                else :
                    d = approaching_lst[-(idx+1)][1].distance(approaching_lst[-idx][1]) * (40010040 / 360)
                dist += d

                if dist <= self.meter :
                    for nd in self.all_nodes :
                        if nd[1] == approaching_lst[-(idx+1)][0] :
                            cnt = nd[4]
                            cnt += 1
                            nd[4] = cnt
                            
                            temp_dict = nd[5]
                            temp_dict[linestring + " " + str(i)] = round(dist,2)

            #Add the tags of schoolzone nodes
            dist = 0
            for sh_nd in schoolzone_lst:
                for nd in self.all_nodes:
                    if nd[1] == sh_nd[0] :
                        cnt = nd[4]
                        cnt += 1
                        nd[4] = cnt
                        
                        temp_dict = nd[5]
                        temp_dict[linestring + " " + str(i)] = dist

            #Add the tags of leaving nodes
            dist = 0
            for idx in range(len(leaving_lst)):
                if idx == 0:
                    d = leaving_lst[idx][1].distance(schoolzone[i-1]) * (40010040 / 360)
                else :
                    d = leaving_lst[idx][1].distance(leaving_lst[idx-1][1]) * (40010040 / 360)
                dist += d
                    
                if dist <= self.meter :
                    for nd in self.all_nodes :
                        if nd[1] == leaving_lst[idx][0] :
                            cnt = nd[4]
                            cnt += 1
                            nd[4] = cnt
                            
                            temp_dict = nd[5]
                            temp_dict[linestring + " " + str(i)] = round(-dist,2)

        return self.all_nodes


def main():
    start = infoNode(test_paths, 20)
    

if __name__ == '__main__' :
    test_paths = [-102537,-103111,-102547,-103137,-102543,-103069,-102561,-103097,-102563,-103051,-102581]

    main()

