#!/usr/bin/env python3

import rclpy
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import NavSatFix
from geometry_msgs.msg import PointStamped, PoseArray
import time

import osmnx as ox, networkx as nx, geopandas as gpd, matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, LineString
from descartes import PolygonPatch
import requests
import matplotlib.cm as cm
import matplotlib.colors as colors
ox.config(use_cache=True, log_console=True)

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from haversine import haversine


class navigation:
    def __init__(self):
    
        #Choose the map file
        self.selected_map = 'A2_LINK.osm'

        self.orig_lat = 0
        self.orig_lon = 0
        #self.dest_lat = 0
        #self.dest_lon = 0
        self.dest_lat = 35.7030221
        self.dest_lon = 128.4578677
        
        #import the map
        self.G = ox.graph_from_xml(self.selected_map, simplify=False)
        
        #Plot the map        
        #fig, ax = ox.plot_graph(self.G, node_zorder=2, node_color='deeppink', bgcolor='k')

        self.G_proj = ox.project_graph(self.G)

        #self.orig_node = ox.get_nearest_node(self.G, (35.7072807, 128.4529979)) #E5 주차장
        self.dest_node = ox.get_nearest_node(self.G, (self.dest_lat, self.dest_lon)) #학교 정문

    def createDestination(self, dlat, dlon):
        self.dest_node = ox.get_nearest_node(self.G, (dlat, dlon))

    def createRoute(self, olat, olon):
        self.orig_node = ox.get_nearest_node(self.G, (olat, olon))
        self.route = nx.shortest_path(self.G, self.orig_node, self.dest_node, weight='length')
        #fig, ax = ox.plot_graph_route(G, route, node_size=0)
        return self.route


class routeNavi:
    def __init__(self):

        self.node = rclpy.create_node("navi_route")

        self.sub_fix = self.node.create_subscription(NavSatFix, "/gps_fix", self.gps_callback)
        self.sub_dest = self.node.create_subscription(PointStamped, "/mapviz/clicked_point", self.destination_callback)

        self.navi = navigation()

        self.pub_lat = self.node.create_publisher(Float64MultiArray, "/route_latitude")
        self.pub_lon = self.node.create_publisher(Float64MultiArray, "/route_longitude")

        #self.pub_pose = self.node.create_publisher(PoseArray, "/route_pose")
        #self.pose_msg = PoseArray()
        #self.pose_msg.poses = [0.0]*5
        #self.pose_msg.poses.postion.x = 0
        #self.pose_msg.poses.postion.y = 0
        #self.pose_msg.poses.postion.z = 0


        self.lat_msg = Float64MultiArray()
        self.lat_msg.data = [-1.0] * 100
        self.lon_msg = Float64MultiArray()
        self.lon_msg.data = [-1.0] * 100

        #self.current_time = self.node.get_clock().now()
        #self.last_time = self.node.get_clock().now()

        self.node.get_logger().info("Ready for publishing route data")

        while rclpy.ok():
            #self.current_time = self.node.get_clock().now()
            rclpy.spin_once(self.node)
            time.sleep(0.1)
            #self.navi_dest = self.navi.createDestination(self.dest_lat, self.dest_lon)
            self.navi_route = self.navi.createRoute(self.gps_lat, self.gps_lon)
            self.lat_now = self.gps_lat
            self.lon_now = self.gps_lon
            self.publish_info(self.navi_route)

    def gps_callback(self, data):
        self.gps_lat = data.latitude
        self.gps_lon = data.longitude

    def destination_callback(self, data):
        self.dest_lat = data.point.x
        self.dest_lon = data.point.y

    def publish_info(self, route):
        #현재 위치로 부터 400m 떨어진 노드까지 PUBLISH
        #BUT 그 노드가 100개 이상이면 100개 까지만

        dist = 0

        for i in range(min(len(route), 100)):
            if i==0:
                dist = haversine((self.lat_now, self.lon_now), (self.navi.G.nodes[route[i]]['y'], self.navi.G.nodes[route[i]]['x']))*1000
                if dist <= 400 :
                    self.lat_msg.data[i] = self.navi.G.nodes[route[i]]['y']
                    self.lon_msg.data[i] = self.navi.G.nodes[route[i]]['x']
                else:
                    break

            else:
                dist += haversine((self.navi.G.nodes[route[i-1]]['y'], self.navi.G.nodes[route[i-1]]['x']), (self.navi.G.nodes[route[i]]['y'], self.navi.G.nodes[route[i]]['x']))*1000 
                if dist <= 400 :
                    self.lat_msg.data[i] = self.navi.G.nodes[route[i]]['y']
                    self.lon_msg.data[i] = self.navi.G.nodes[route[i]]['x']
                else:
                    break

        '''
        self.lat_msg.data[0] = self.navi.G.nodes[route[0]]['y']
        self.lat_msg.data[1] = self.navi.G.nodes[route[1]]['y']
        self.lat_msg.data[2] = self.navi.G.nodes[route[2]]['y']
        self.lat_msg.data[3] = self.navi.G.nodes[route[3]]['y']
        self.lat_msg.data[4] = self.navi.G.nodes[route[4]]['y']

        self.lon_msg.data[0] = self.navi.G.nodes[route[0]]['x']
        self.lon_msg.data[1] = self.navi.G.nodes[route[1]]['x']
        self.lon_msg.data[2] = self.navi.G.nodes[route[2]]['x']
        self.lon_msg.data[3] = self.navi.G.nodes[route[3]]['x']
        self.lon_msg.data[4] = self.navi.G.nodes[route[4]]['x']
        '''
        '''
        self.pose_msg.poses[0].postion.x = self.navi.G.nodes[route[0]]['y']
        self.pose_msg.poses[1].postion.x = self.navi.G.nodes[route[1]]['y']
        self.pose_msg.poses[2].postion.x = self.navi.G.nodes[route[2]]['y']
        self.pose_msg.poses[3].postion.x = self.navi.G.nodes[route[3]]['y']
        self.pose_msg.poses[4].postion.x = self.navi.G.nodes[route[4]]['y']

        self.pose_msg.poses[0].postion.y = self.navi.G.nodes[route[0]]['x']
        self.pose_msg.poses[1].postion.y = self.navi.G.nodes[route[1]]['x']
        self.pose_msg.poses[2].postion.y = self.navi.G.nodes[route[2]]['x']
        self.pose_msg.poses[3].postion.y = self.navi.G.nodes[route[3]]['x']
        self.pose_msg.poses[4].postion.y = self.navi.G.nodes[route[4]]['x']
        '''
        self.pub_lat.publish(self.lat_msg)
        self.pub_lon.publish(self.lon_msg)
        #self.pub_pose.publish(self.pose_msg)

def main():
    rclpy.init()
    start = routeNavi()

if __name__ == '__main__':
    main()

