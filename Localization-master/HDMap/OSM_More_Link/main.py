# OSM Modify with Handler               

import OSMHandler
import haversine_distance
import math

meter_cut = 1


w = open("A2_MORE_LINK_cut.osm", mode='wt')

if __name__ == '__main__':
    file_name = "A2_LINK_cut.osm"
    osm_data = OSMHandler.OSM_data(file_name)
    #print(osm_data)

    nodes = []
    ways = []
    new_nodes = []
    new_ways = []

    for data in osm_data:
        if data[0] == 'node' :
            nodes.append(data)

        elif data[0] == 'way' :
            ways.append(data)

    nodes_num = OSMHandler.OSM_nodes_num(file_name)
    ways_num = OSMHandler.OSM_ways_num(file_name)

    temp = ways[0]
    test = []
    test.append(temp)
    id_count = 1

    for way in ways:
        t_n = way[2]
        cnt = 0
        t_n_n = len(t_n)
        every_nodes_for_each_way = []
        while cnt < t_n_n - 1:
            id1, id2 = t_n[cnt], t_n[cnt+1]
            temp_nodes = dict()

            for node in nodes:
                if node[1] == id1:
                    temp_nodes['id1'] = [node[2],node[3]]

                elif node[1] == id2:
                    temp_nodes['id2'] = [node[2],node[3]]

            temp_d = 1000 * haversine_distance.GeoUtil.get_harversion_distance(temp_nodes['id1'][1],temp_nodes['id1'][0],temp_nodes['id2'][1],temp_nodes['id2'][0])
            n = math.ceil((1/meter_cut)*temp_d + 1)
            temp_new_nodes = []

            temp_point_x = (temp_nodes['id1'][0])
            temp_point_y = (temp_nodes['id1'][1])
            temp_new_nodes.append([id1, temp_point_x,temp_point_y])

            for k in range(1,n-1):
                temp_point_x = (temp_nodes['id1'][0]*(n-1-k) + temp_nodes['id2'][0]*k)/(n-1)
                temp_point_y = (temp_nodes['id1'][1]*(n-1-k) + temp_nodes['id2'][1]*k)/(n-1)
                temp_new_nodes.append([0, temp_point_x,temp_point_y])
            every_nodes_for_each_way.extend(temp_new_nodes)
            cnt += 1
            if cnt == t_n_n - 1:
                every_nodes_for_each_way.append([id2, temp_nodes['id2'][0],temp_nodes['id2'][1]])
        
            for w_node in every_nodes_for_each_way:
                if w_node[0] == 0:
                    w_node[0] = -id_count
                    id_count +=1
        
        temp_nodes_id_list = []
        for node in every_nodes_for_each_way:
            temp_nodes_id_list.append(node[0])

        temp_new_way = way
        temp_new_way[2] = temp_nodes_id_list
        new_ways.append(temp_new_way)

        for w_node in every_nodes_for_each_way:
            new_nodes.append(['node', w_node[0], w_node[1], w_node[2], 0, {}])

    new_new_nodes=[]
    for v in new_nodes:
        if v not in new_new_nodes:
            new_new_nodes.append(v)


    text = ["<?xml version='1.0' encoding='UTF-8'?>\n", "<osm version='0.6' upload='false' generator='JOSM'>\n"]

    for nd in new_new_nodes:
        text.append("  <node id='{0}' lat='{1}' lon='{2}' />\n".format(nd[1], nd[2], nd[3]))

    for way in new_ways:
        text.append("  <way id='{0}' action='modify'>\n".format(way[1]))
        for nd in way[2]:
            text.append("    <nd ref='{0}' />\n".format(nd))
        keys=[]
        keys = way[4].keys()
        for key in keys:
            text.append("    <tag k='{0}' v='{1}' />\n".format(key, way[4][key]))
        text.append("  </way>\n")

                        
    text.append("</osm>")


    for line in text:
        w.write(line)


w.close()
