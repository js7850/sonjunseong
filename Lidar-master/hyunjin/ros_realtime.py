import rospy
from sensor_msgs.msg import PointCloud2, PointField
import sensor_msgs.point_cloud2 as pc2
from sensor_msgs.msg import Image as Img
from cv_bridge import CvBridge, CvBridgeError
import message_filters
from roslib import message
import pcl
from show import *
from rospy.numpy_msg import numpy_msg
import cv2
import numpy as np

bridge = CvBridge()
FusionPublisher = rospy.Publisher('Fusion/lidar_camera', Img , queue_size =1 )

def on_new_point_cloud(data,msg):
	global im
	global i
	pc = pc2.read_points(data, skip_nans=True, field_names=("x", "y", "z","intensity"))
	#print pc.type
	#print data.type
	cloud_points = []
	for p in pc:
		cloud_points.append(p)
	npc = np.array(cloud_points)
	savepath = './pic/depth/' + str(i) + '.png'
	imgIn=bridge.imgmsg_to_cv2(msg,"bgr8")
	im = lidar_to_2d_front_view(npc, v_res=VRES, h_res=HRES, v_fov=VFOV, val="reflectance", saveto = savepath , y_fudge=Y_FUDGE, image_data=imgIn)
	
	#lidar_to_2d_front_view(npc, v_res=VRES, h_res=HRES, v_fov=VFOV, val="height", y_fudge=Y_FUDGE)
	#lidar_to_2d_front_view(npc, v_res=VRES, h_res=HRES, v_fov=VFOV, val="reflectance", y_fudge=Y_FUDGE)
	#im = birds_eye_point_cloud(npc, side_range=(-10, 10), fwd_range=(-10, 10), res=0.1)
	'''
	point_cloud_to_panorama(npc,
                             v_res=VRES,
                             h_res=HRES,
                             v_fov=VFOV,
                             y_fudge=5,
	                             d_range=(0,100))
	'''	
	i += 1
	pubimg = bridge.cv2_to_imgmsg(im, 'bgr8')
	FusionPublisher.publish(pubimg)
	#cv2.namedWindow('image',cv2.WINDOW_NORMAL)
	#cv2.imshow('image',im)
	#cv2.waitKey(1)
	#height, width, rgb  = im.shape
	#frame_array.append(im)
	#plt.imshow(im,cmap='spectral')
	#plt.show()





if __name__ == '__main__' : 
	#HRES = 0.064        # horizontal resolution (assuming 20Hz setting)
	#VRES = 0.075          # vertical res
	HRES = 0.1
	VRES = 0.1136
	VFOV = (-15, 15) # Field of view (-ve, +ve) along vertical axis
	Y_FUDGE = 10         # y fudge factor for velodyne HDL 64E

	i = 0
	im=0

	rospy.init_node('listner',anonymous=True)
	image_raw = message_filters.Subscriber("/usb_cam/image_raw", Img)
	data = message_filters.Subscriber("/velodyne_points", PointCloud2)
	ts = message_filters.ApproximateTimeSynchronizer([data,image_raw],1,0.03)
	ts.registerCallback(on_new_point_cloud)
	#rospy.Subscriber('/usb_cam/image_raw', Img, image_raw )
	#rospy.Subscriber('/velodyne_points', numpy_msg(PointCloud2), on_new_point_cloud)
	rospy.spin()


