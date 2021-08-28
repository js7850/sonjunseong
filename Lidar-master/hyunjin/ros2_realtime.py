#!/usr/bin/env python3

import rclpy
from sensor_msgs.msg import PointCloud2
import message_filters
import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
import sensor_msgs.point_cloud2 as pc2
import pcl


bridge = CvBridge()                       

class rosPub:
	def __init__(self):
		rclpy.init()

		self.node = rclpy.create_node("lidar")
		self.subimage = self.node.create_subscription(Image, '/usb_cam/image_raw',image_callback)
		
		#self.node3 = rclpy.create_node("fusionimage")
		self.fusionPub = self.node.create_publisher(Image, '/Fusion/lidar_camera')

		#self.node = rclpy.create_node("camera")
		self.subpoint = self.node.create_subscription(PointCloud2, '/velodyne_points',point_callback)
def scale_to_1(a, min, max):
    return (((a-min)/float(max-min))*1)

def image_callback(msg : Image):
	global rosPublClass
	global image_data

	image_data =bridge.imgmsg_to_cv2(msg,'bgr8')


def point_callback(data : PointCloud2):
	global rosPubClass
	global image_data

	global HRES 
	global VRES
	global VFOV
	global Y_FUDGE

	v_res = VRES
	h_res = HRES
	v_fov = VFOV
	y_fudge = Y_FUDGE
	
	pc = pc2.read_points(data, skip_nans = True, field_names=("x", "y", "z", "intensity"))
	cloud_points = []
	for p in pc:
		cloud_points.append(p)
	points = np.array(cloud_points)
	x_lidar = points[:, 0]
	y_lidar = points[:, 1]
	z_lidar = points[:, 2]

	print(x_lidar)
	r_lidar = points[:, 3] # Reflectance
	# Distance relative to origin when looked from top
	#d_lidar = np.sqrt(x_lidar ** 2 + y_lidar ** 2)
	# Absolute distance relative to origin
	d_lidar = np.sqrt(x_lidar ** 2 + y_lidar ** 2, z_lidar ** 2)

	v_fov_total = -v_fov[0] + v_fov[1]

	# Convert to Radians
	v_res_rad = v_res * (np.pi/180)
	h_res_rad = h_res * (np.pi/180)

	# PROJECT INTO IMAGE COORDINATES
	x_img = np.arctan2(-y_lidar, x_lidar)/ h_res_rad
	y_img = np.arctan2(z_lidar, d_lidar)/ v_res_rad
	#x_img = x_lidar
	#y_img = z_lidar

	# SHIFT COORDINATES TO MAKE 0,0 THE MINIMUM
	x_min = -360.0 / h_res / 2  # Theoretical min x value based on sensor specs
	x_img -= x_min              # Shift
	x_max = 360.0 / h_res       # Theoretical max x value after shifting
	y_min = v_fov[0] / v_res    # theoretical min y value based on sensor specs
	y_img -= y_min              # Shift
	y_max = v_fov_total / v_res # Theoretical max x value after shifting

	#y_max += y_fudge            # Fudge factor if the calculations based on
                                # spec sheet do not match the range of
                                # angles collected by in the data.
	pixel_values=d_lidar
	# PLOT THE IMAGE

	h, w, d = image_data.shape
	image_data = cv2.resize(image_data, dsize = (821,460), interpolation=cv2.INTER_LINEAR)
	new_h, new_w, new_d = image_data.shape
	XONES = np.ones(len(x_img), dtype = 'float64') * (x_max/2 - new_w/2)
	YONES = np.ones(len(y_img), dtype = 'float64') * (new_h-y_fudge)


	min_values=min(pixel_values)
	max_values = max(pixel_values)
	c = scale_to_1(pixel_values, min_values, max_values)
    
	points =[]
	for i in range(len(x_img)):
		points.append((round(x_img[i]-x_max/2+new_w/2), round(new_h-y_img[i])))
		#points.append((x_img[i]-x_max/2+new_w/2, new_h-y_img[i]))
	for i in range(len(points)):
		color = (round((abs(6*c[i]-3)-1)*255), round((2-abs(6*c[i]-2))*255), round((2-abs(6*c[i]-4))*255))
		image_result = cv2.circle(image_data, points[i], 1,color,-1)

	pubimg = bridge.cv2_to_imgmsg(image_result,'bgr8')
	
	rosPubClass.fusionPub.publish(pubimg)



def main():
	global rosPubClass 
	global HRES 
	global VRES
	global VFOV
	global Y_FUDGE


	rosPubClass = rosPub()

	HRES = 0.1
	VRES = 0.1136
	VFOV = (-15,15)
	Y_FUDGE = 10

	rclpy.spin(rosPubClass.node)

	rosPubClass.node.destroy_node()
	rclpy.shutdown()


if __name__=="__main__":
	main()
