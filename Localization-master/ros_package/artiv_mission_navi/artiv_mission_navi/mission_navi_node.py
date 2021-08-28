#dependence
#pip3 install utm
#pip3 install shapely
#pip3 install osmium
#-------------------------------------------------------------------------------------------

import artiv_mission_navi.map_parser
import artiv_mission_navi.guidance_line
import utm
from artiv_mission_navi.haversine_distance import GeoUtil
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_default
from sensor_msgs.msg import NavSatFix, JointState
from std_msgs.msg import Header, Float32MultiArray

#--------------------------------------------------------------------------------------------
#TODO pre-set
''' K-City or DGIST'''
location = 'k_city'
#location = 'dgist'

'''publihsing 할 path의 노드 개수 설정 (path)'''
num = 30

'''publihsing 할 노드 거리 설정 (node_info)'''
meter = 20
#---------------------------------------------------------------------------------------------


#topic_pub = '/hdmap/mission_info'
topic_path = '/hdmap/path'
topic_node = '/hdmap/node_info'
topic_miss = '/hdmap/mission_info'

topic_GPS = '/gps_fix'



class Mission_Navi(Node):

    def __init__(self):
        self.node = rclpy.create_node("MissionNavi")
        self.node.get_logger().info("Start Preprocessing!")

        #Set the global path!
        
        #DGIST
        #self.paths = [-104155, -108467]
        
        #self.paths = [-108467,-103565, -103775, -104547, -104359, -104361, -104061, -103531, -103627, -104019, -103683, -104035, -104545, -103401, -103841, -104401, -104587, -104103, -103997, -103779, -104135, -103457, -108445, -104715, -103579, -108451, -104303, -104601, -104279, -103921, -104725, -104837, -103325, -103699, -103555, -104883, -104711, -104869, -103307, -108187, -103849, -104333, -104155]

        #self.paths = [-101782, -101783, -101784]
        


        #K-CITY
        self.paths = [-112158, -112183, -112161, -112185, -112160, -112180, -112163, -112182, -112164, -112178, -112166, -112167, -112174, -112168, -112169, -112170, -112171, -112176, -112177, -112172, -112156, -112155, -112173, -112175, -112165, -112179, -112162, -112181, -112159, -112184, -112157]

        if location == 'k_city' :
            self.node_info = artiv_mission_navi.guidance_line.KCity_Guidance_Line(self.paths, meter, num)

        elif location == 'dgist' :
            self.node_info = artiv_mission_navi.guidance_line.DGIST_Guidance_Line(self.paths, meter, num)

        self.node.get_logger().info("Preprocessing is DONE!")
        

        # Initializing publisher
        self.pathPub = self.node.create_publisher(JointState, topic_path)
        self.nodePub = self.node.create_publisher(Float32MultiArray, topic_node)
        self.missPub = self.node.create_publisher(Float32MultiArray, topic_miss)

        self.node_info_msg = Float32MultiArray()
        self.miss_info_msg = Float32MultiArray()

        self.path_info = JointState()
        self.path_info.header = Header()
        self.path_info.header.stamp = self.node.get_clock().now().to_msg()
        self.path_info.name = []
        self.path_info.position = [0.0]*num
        self.path_info.velocity = [0.0]*num

        # Initializing subscriber
        self.GPSSub = self.node.create_subscription(NavSatFix, topic_GPS, self.gps_callback)
        #self.GPSSub

        while rclpy.ok():
            rclpy.spin_once(self.node)
            self.publishNavi()

    def gps_callback(self, msg):
        self.latitude, self.longitude = msg.latitude, msg.longitude



    def publishNavi(self):

        self.node_info.update(self.latitude, self.longitude)

        temp_node_info = self.node_info.get_current_node()

        info_len = len(temp_node_info[3])
        miss_len = len(temp_node_info[4])

        self.node_info_msg.data = [0.0, 0.0, 0.0] * info_len
        self.miss_info_msg.data = [0.0, 0.0, 0.0] * miss_len

        for key, val in temp_node_info[3].items():
            for i in range(info_len):
                idx = i*3
                if key.find('crosswalks') == 0:
                    self.node_info_msg.data[idx] = 1.0
                    self.node_info_msg.data[idx+1] = float(key[10:])
                    self.node_info_msg.data[idx+2] = float(val)

                elif key.find('speedbumps') == 0:
                    self.node_info_msg.data[idx] = 3.0
                    self.node_info_msg.data[idx+1] = float(key[10:])
                    self.node_info_msg.data[idx+2] = float(val)

                elif key.find('protected_areas') == 0:
                    self.node_info_msg.data[idx] = 6.0
                    self.node_info_msg.data[idx+1] = float(key[15:])
                    self.node_info_msg.data[idx+2] = float(val)     

                elif key.find('stoplines') == 0:
                    self.node_info_msg.data[idx] = 20.0
                    self.node_info_msg.data[idx+1] = float(key[9:])
                    self.node_info_msg.data[idx+2] = float(val)   


        for key, val in temp_node_info[4].items():
            for i in range(miss_len):
                idx = i*3
                if key.find('mission_areas') == 0:
                    self.miss_info_msg.data[idx] = float(key[13:])
                    self.miss_info_msg.data[idx+1] = float(val[1])    
                    self.miss_info_msg.data[idx+2] = float(val[0])     


        temp_forward_nodes = self.node_info.get_forward_path()

        temp_x = []
        temp_y = []

        forward_len = len(temp_forward_nodes)

        if forward_len == num :
            for i in range(forward_len):
                lat = temp_forward_nodes[i].y
                lon = temp_forward_nodes[i].x
                temp_utm = utm.from_latlon(lat, lon)
                temp_x.append(temp_utm[0])
                temp_y.append(temp_utm[1])

        else :
            diff = num - forward_len
            for i in range(forward_len):
                lat = temp_forward_nodes[i].y
                lon = temp_forward_nodes[i].x
                temp_utm = utm.from_latlon(lat, lon)
                temp_x.append(temp_utm[0])
                temp_y.append(temp_utm[1])

            for j in range(diff):
                temp_x.append(0.0)
                temp_y.append(0.0)


        self.path_info.header.stamp = self.node.get_clock().now().to_msg()
        self.path_info.position = temp_x
        self.path_info.velocity = temp_y
        
        
        self.nodePub.publish(self.node_info_msg)
        self.missPub.publish(self.miss_info_msg)
        self.pathPub.publish(self.path_info)

def main(args=None):
    rclpy.init(args=args)
    mission_navi = Mission_Navi()


if __name__ == '__main__':
    main()
