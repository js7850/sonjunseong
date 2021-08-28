// subscribe point cloud from /velodyne topics

#include <iostream>

#include <ros/ros.h>
#include <cmath>
#include <sensor_msgs/PointCloud2.h>

#include <pcl/conversions.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl_conversions/pcl_conversions.h>

#include <vector>
ros::Publisher pub;

sensor_msgs::Image image;

typedef pcl::PointXYZ	PointXYZ;

vector<float> FOV ={1, 2} ;

FOV.push_back(-15);
FOV.push_back(15);

void cloud_cb (const sensor_msgs::PointCloud2 msg){
	//ros_pcl2 to pcl2
	pcl::PCLPointCloud2 pcl_pc;
	pcl_conversions::toPCL(msg, pcl_pc);

	//pcl2 to pclxyz
	pcl::PointCloud<PointXYZ> input_cloud;
	pcl::fromPCLPointCloud2(pcl_pc, input_cloud);

	vector<float> x_lidar;
	vector<float> y_lidar;
	vector<float> z_lidar;
	vector<float> d_lidar;

	for(i=0; i<len(input_cloud), i++){
		x_lidar.push_back(input_cloud[i][0]);
		y_lidar.push_back(input_cloud[i][1]);
		z_lidar.push_back(input_cloud[i][2]);
		d_lidar.push_back(pow(input_cloud[i][0],2)+pow(input_cloud[i][1],2)+pow(input_cloud[i][2],2));

		v_fov_total = 
	}

	


	sensor_msgs::PointCloud2 output;
	output = msg;
	pub.publish (output);
}

//void alignment(const sensor_msgs::PointCloud2 pc, const sensor_msgs::Image image){
	// consider  implment as Thread if this ops time take longer thnt cloud cb

//}

int main(int argc, char** argv){
	//initialize ROS
	ros::init (argc, argv, "align_camera_lidar");
	ros::NodeHandle nh;
	ros::AsyncSpinner spiner(1);

	//Create a Ros subscriber for the input point cloud 
	ros::Subscriber lidarsub = nh.subscribe ("/velodyne_points",1,cloud_cb);

	pub = nh.advertise<sensor_msgs::PointCloud2> ("output",1);
    spiner.start();
    ROS_INFO("alignment started...");

    ros::waitForShutdown();
    ROS_INFO("alignment exited...");


}