from prohibited_area import nearest_point_to_prohibited_area
from haversine_distance import GeoUtil

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_default
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import String

NODENAME = "school_zone"
topic_Warning = '/school_zone_warning'
topic_GPS = '/gps_fix'

file_name = "A3_DRIVEWAYSECTION.osm"

class School_Zone(Node):

    def __init__(self):
        super().__init__(NODENAME)

        # Initializing publisher
        self.WarningPub = self.create_publisher(String, topic_Warning, qos_profile_default)

        # Initializing subscriber
        self.GPSSub = self.create_subscription(NavSatFix, topic_GPS, self.gps_callback, qos_profile_default)
        self.GPSSub

    def gps_callback(self, msg):
        latitude, longitude = msg.latitude, msg.longitude
        self.get_logger().info(f"current latitude: {msg.latitude}, current longitude: {msg.longitude}")
        school_zone_nearest_node = nearest_point_to_prohibited_area(file_name,latitude,longitude)
        lat_node, long_node = school_zone_nearest_node[2], school_zone_nearest_node[3]
        min_distance = GeoUtil.get_harversion_distance(longitude, latitude, long_node, lat_node) * 1000 # 단위 : m
        warning = String()
        warning.data = f'Distance from school zone is {min_distance}m.'
        self.get_logger().info(f"Distance from school zone is {min_distance}m.")
        self.WarningPub.publish(warning)

def main(args=None):
    rclpy.init(args=args)

    school_zone_warning = School_Zone()
    rclpy.spin(school_zone_warning)
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    school_zone_warning.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
