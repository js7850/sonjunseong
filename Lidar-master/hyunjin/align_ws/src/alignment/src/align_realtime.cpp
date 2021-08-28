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
#define _USE_MATH_DEFINES

#include <opencv2/opencv.hpp>

#include <algorithm>

#include <time.h>

#include <image_transport/image_transport.h>
#include <opencv/cvwimage.h>
#include <opencv/highgui.h>
#include <cv_bridge/cv_bridge.h>

using namespace cv ;
using namespace std ;

sensor_msgs::Image image;
image_transport::Publisher pub;

typedef pcl::PointXYZ	PointXYZ;

//--------------LIDAR PARAMETER----------------
float min_fov = -15;
float max_fov = 15;
float hres = 0.11;
float vres =0.1136 ;
int y_fudge = 20 ;


int v_fov_total = -min_fov+max_fov ;

float pi = M_PI;

float v_res_rad = vres * (pi/180) ;
float h_res_rad = hres * (pi/180) ;

//-------------IMAGE parameter-----------------

float x_min = - 360.0/hres/2 ;
float x_max = 360.0/hres ;
float y_min = min_fov / vres;
float y_max = v_fov_total / vres ;

int height = 300 ;
int width = 3600 ;


cv_bridge::CvImagePtr cv_ptr;

int h = 460;
int w = 821;
Mat resultImg;
Mat resizeImg(w, h, CV_8UC3) ;

//------------image coordinate struct-----------

struct XYZ{
	std::vector<float> x_lidar;
	std::vector<float> y_lidar;
	std::vector<float> z_lidar;
	std::vector<float> d_lidar;
	void reset() {
		x_lidar.clear();
		y_lidar.clear();
		z_lidar.clear();
		d_lidar.clear();
	}
};

struct IMGXY{
	std::vector<float> x_img ;
	std::vector<float> y_img ;

	void reset(){
		x_img.clear();
		y_img.clear();
	}
};


XYZ xyz;
//xyz.reset()

IMGXY img;
//img.reset();



void image_cb (const sensor_msgs::ImageConstPtr& msg_ptr){
	cv_ptr = cv_bridge::toCvCopy(msg_ptr,"bgr8")  ;

}

//------------calculate projection xyz from point cloud--------
void cloud_cb (const sensor_msgs::PointCloud2 msg){

	clock_t begin, end;
	begin = clock();

	//ros_pcl2 to pcl2
	pcl::PCLPointCloud2 pcl_pc;
	pcl_conversions::toPCL(msg, pcl_pc);

	//pcl2 to pclxyz
	pcl::PointCloud<PointXYZ> input_cloud;
	pcl::fromPCLPointCloud2(pcl_pc, input_cloud);

	//XYZ xyz;
	xyz.reset()

	//IMGXY img;
	img.reset();

	std::vector<float> c ;

	for(int i=0; i<input_cloud.size(); i++){
		xyz.x_lidar.push_back(input_cloud[i].x);
		xyz.y_lidar.push_back(input_cloud[i].y);
		xyz.z_lidar.push_back(input_cloud[i].z);
		xyz.d_lidar.push_back(sqrt(pow(input_cloud[i].x,2)+pow(input_cloud[i].y,2)+pow(input_cloud[i].z,2)));
		
		img.x_img.push_back(atan2(-xyz.y_lidar[i],xyz.x_lidar[i])/h_res_rad - x_min) ;
		img.y_img.push_back(atan2(xyz.z_lidar[i],xyz.d_lidar[i])/v_res_rad - y_min) ;
	}

	float min_values = *min_element(xyz.d_lidar.begin(),xyz.d_lidar.end()) ;
	float maX_values = *max_element(xyz.d_lidar.begin(),xyz.d_lidar.end()) ;
	for(int i=0; i<xyz.d_lidar.size(); i++){
		c.push_back((xyz.d_lidar[i]-min_values)/(maX_values-min_values));
	}

	
	
	resize(cv_ptr->image, resizeImg, Size(w,h));
	for(int i=0; i<img.x_img.size(); i++){
		circle(resizeImg, Point(round(img.x_img[i]-x_max/2 + w/2) , round(h-img.y_img[i])-y_fudge ), 1, Scalar( round((abs(6*c[i]-3)-1)*255), round((2-abs(6*c[i]-2))*255), round((2-abs(6*c[i]-4))*255) ), -1);
	}

	end = clock();
	std::cout <<"seconds : "<<double(end-begin)/CLOCKS_PER_SEC<<"\n";

	//imshow("result", resizeImg);
	//waitKey(1);

	sensor_msgs::ImagePtr output = cv_bridge::CvImage(std_msgs::Header(), "bgr8", resizeImg).toImageMsg();
	pub.publish(output);
}

//void alignment(const sensor_msgs::PointCloud2 pc, const sensor_msgs::Image image){
	// consider  implment as Thread if this ops time take longer thnt cloud cb

//}

int main(int argc, char** argv){
	//initialize ROS
	ros::init (argc, argv, "align_camera_lidar");
	ros::NodeHandle nh;
	image_transport::ImageTransport it(nh);
	ros::AsyncSpinner spiner(1);
	

	//Create a Ros subscriber for the input point cloud 
	ros::Subscriber lidarsub = nh.subscribe ("/velodyne_points",1,cloud_cb);
	ros::Subscriber imagesub = nh.subscribe ("/usb_cam/image_raw",1,image_cb);
	pub = it.advertise("/fusion/lidar_camera",1);
    
    spiner.start();
    ROS_INFO("alignment started...");

    ros::waitForShutdown();
    ROS_INFO("alignment exited...");


}