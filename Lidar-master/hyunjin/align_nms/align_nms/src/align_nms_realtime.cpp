// subscribe point cloud from /velodyne topics

#include <iostream>

#include <ros/ros.h>
#include <cmath>
#include <sensor_msgs/PointCloud2.h>
#include <visualization_msgs/MarkerArray.h>
#include <visualization_msgs/Marker.h>
#include <std_msgs/Int16MultiArray.h>

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
pcl::PointCloud<PointXYZ> global_cloud;

//--------------LIDAR PARAMETER----------------
float min_fov = -15;
float max_fov = 15;
float hres = 0.11;
float vres =0.1136 ;
int y_fudge = 33 ;


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
//Mat resultImg;


//-------------about yolo--------------
int yolo_bbox_n;

std::vector<std::string> COCO_CLASSES_LIST = {"person" , "bicycle" , "car" , "motorbike" , "aeroplane" , "bus" , "train" , "truck" , "boat" , "traffic light" , "fire hydrant" , "stop sign" , "parking meter" , "bench" , "bird" , "cat" , "dog" , "horse" , "sheep" , "cow" , "elephant" , "bear" , "zebra" , "giraffe" , "backpack" , "umbrella" , "handbag" , "tie" , "suitcase" , "frisbee" , "skis" , "snowboard" , "sports ball" , "kite" , "baseball bat" , "baseball glove" , "skateboard" , "surfboard" , "tennis racket" , "bottle" , "wine glass" , "cup" , "fork" , "knife" , "spoon" , "bowl" , "banana" , "apple" , "sandwich" , "orange" , "broccoli" , "carrot" , "hot dog" , "pizza" , "donut" , "cake" , "chair" , "sofa" , "pottedplant" , "bed" , "diningtable" , "toilet" , "tvmonitor" , "laptop" , "mouse" , "remote" , "keyboard" , "cell phone" , "microwave" , "oven" , "toaster" , "sink" , "refrigerator" , "book" , "clock" , "vase" , "scissors" , "teddy bear" , "hair drier" , "toothbrush", "unidentified"};


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

//-----------segment box coordinate struct-----

struct SegBox{
	std::vector<float> x;
	std::vector<float> y;
	std::vector<float> z;
	void reset(){
		x.clear();
		y.clear();
		z.clear();
	}
};

SegBox seg_box;

//----------segment rectangle points struct----

struct SegRect{
	std::vector<float> d_lidar;
	std::vector<float> x_rect_img;
	std::vector<float> y_rect_img;
	void reset(){
		d_lidar.clear();
		x_rect_img.clear();
		y_rect_img.clear();
	}
};

SegRect seg_rect;

//----------yolov3 bbox points struct-------
struct BboxPt{
	std::vector<int> x;
	std::vector<int> y;
	std::vector<int> class_id ;
	void reset(){
		x.clear();
		y.clear();
		class_id.clear();
	}
};

BboxPt bbox_pt;

//----------LIDAR Bbox points struct---------
struct LidarPt{
	std::vector<int> x ;
	std::vector<int> y ;
	std::vector<int> img_x ;
	std::vector<int> img_y ;
	std::vector<int> class_id ;
	void reset(){
		x.clear();
		y.clear();
		img_x.clear();
		img_y.clear();
		class_id.clear();
	}
};

LidarPt lidar_pt;


//---------------vector for store IOU values--------------
std::vector<float> IOU ;


//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
//------------------callback functions------------------
//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

void image_cb (const sensor_msgs::ImageConstPtr& msg_ptr){
	cv_ptr.reset();
	cv_ptr = cv_bridge::toCvCopy(msg_ptr,"bgr8")  ;
}




//------------calculate projection xyz from point cloud--------
void cloud_cb (const sensor_msgs::PointCloud2 msg){

	//ros_pcl2 to pcl2
	pcl::PCLPointCloud2 pcl_pc;
	pcl_conversions::toPCL(msg, pcl_pc);

	pcl::PointCloud<PointXYZ> input_cloud;
	pcl::fromPCLPointCloud2(pcl_pc, input_cloud);
	
	global_cloud = input_cloud;
	
}

//------------subscribe the segmented box points-----------
void seg_cb (const visualization_msgs::MarkerArray seg_points){
	
	if(seg_points.markers.size()>1){
		seg_box.reset();
		for(int i =0; i<seg_points.markers.size(); i++){

			if(seg_points.markers[i].type==5){
				//std::cout<<seg_points.markers[i].type<<"\n";
				//std::cout<<seg_points.markers[i].points<<"\n";
				seg_box.x.push_back(seg_points.markers[i].points[0].x);	
				seg_box.y.push_back(seg_points.markers[i].points[0].y);
				seg_box.z.push_back(seg_points.markers[i].points[0].z);
				for(int j=1; j<8; j++){
					seg_box.x.push_back(seg_points.markers[i].points[2*j+1].x);		
					seg_box.y.push_back(seg_points.markers[i].points[2*j+1].y);
					seg_box.z.push_back(seg_points.markers[i].points[2*j+1].z);	
				}
			}	
		}
	}

}


//-----------subscribe the Bbox points-----------------------

void bbox_cb (const std_msgs::Int16MultiArray pt) {
	yolo_bbox_n = pt.layout.dim.size();
	if(pt.layout.dim.size()>0){
		bbox_pt.reset();
		
		//std::cout<<bbox_pt.layout.dim.size()<<"\n";
		for(int i=0; i<pt.layout.dim.size(); i++){
			bbox_pt.x.push_back(round(pt.data[i*6+2]*0.76)-70);
			bbox_pt.y.push_back(round(pt.data[i*6+3]*0.64));

			bbox_pt.x.push_back(round(pt.data[i*6+4]*0.76)-70);
			bbox_pt.y.push_back(round(pt.data[i*6+5]*0.64));

			bbox_pt.class_id.push_back(pt.data[6*i]);
		}

	}

}





//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
//fusion 
//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
int alignment(){
	//pcl2 to pclxyz

	if (global_cloud.size() < 1){
		return 0;
	}
	if (seg_box.x.size() <1){

		return 0;
	}
	if (bbox_pt.x.size()<1){
		return 0;
	}
	clock_t begin, end;
	begin = clock();
	//XYZ xyz;
	xyz.reset();

	//IMGXY img;
	img.reset();
	
	seg_rect.reset();
			
	lidar_pt.reset();


	std::vector<float> c ;

	Mat resizeImg(w, h, CV_8UC3) ;

	//projection every lidar point to 2D image

	for(int i=0; i<seg_box.x.size(); i++){
		seg_rect.d_lidar.push_back(sqrt(pow(seg_box.x[i],2)+pow(seg_box.y[i],2)));
		//calculate segmented box 8 points --> 2D projection points
		seg_rect.x_rect_img.push_back(atan2(-seg_box.y[i], seg_box.x[i])/h_res_rad - x_min);
		seg_rect.y_rect_img.push_back(atan2(seg_box.z[i], seg_rect.d_lidar[i])/v_res_rad - y_min);

	}

	for(int i=0; i<seg_rect.x_rect_img.size(); i++){
		for(int j=0; j<seg_rect.x_rect_img.size()/8; j++){
			float min_x = *min_element(seg_rect.x_rect_img.begin()+8*i, seg_rect.x_rect_img.begin()+8*i+8);
			float max_x = *max_element(seg_rect.x_rect_img.begin()+8*i, seg_rect.x_rect_img.begin()+8*i+8);
			float min_y = *min_element(seg_rect.y_rect_img.begin()+8*i, seg_rect.y_rect_img.begin()+8*i+8);
			float max_y = *max_element(seg_rect.y_rect_img.begin()+8*i, seg_rect.y_rect_img.begin()+8*i+8);
			lidar_pt.x.push_back(round(min_x)-x_max/2 + w/2+13) ;
			lidar_pt.y.push_back(round(h - max_y)-120) ;
			lidar_pt.x.push_back(round(max_x)-x_max/2+w/2+13) ;
			lidar_pt.y.push_back(round(h - min_y)-120) ;
			//rectangle(resizeImg, Point(round(min_x)-x_max/2 + w/2+13,round(h-max_y)-120), Point(round(max_x)-x_max/2+w/2, round(h-min_y)-120), Scalar(255,0,255),2) ;

		}
		//circle(resizeImg, Point(round(seg_rect.x_rect_img[i]-x_max/2+w/2), round(h-seg_rect.y_rect_img[i])-90), 5, Scalar(255,255,255), -1);	
	}

	
	//for(int i=0; i<yolo_bbox_n; i++){
	//	for(int j=0; j<lidar_pt.x.size()/2; j++){
	//		//이 for문 한 번이 lidar 박스 하나! 
	//		if((lidar_pt.x[2*j+1]<bbox_pt.x[2*i]) || (lidar_pt.x[2*j]>bbox_pt.x[2*i+1]) || (lidar_pt.y[2*j+1]>bbox_pt.y[2*i]) || (lidar_pt.y[2*j]<bbox_pt.y[2*i+1]) ){
	//			lidar_pt.img_x.push_back(lidar_pt.x[2*j]) ;
	//			lidar_pt.img_y.push_back(lidar_pt.y[2*j]) ;
	//			lidar_pt.img_x.push_back(lidar_pt.x[2*j+1]) ;
	//			lidar_pt.img_y.push_back(lidar_pt.y[2*j+1]) ;
	//			lidar_pt.class_id.push_back(COCO_CLASSES_LIST.size()-1) ;
	//		}
	//
	//	}
	//
	//}

	for(int i =0; i<lidar_pt.x.size()/2; i++){
		for(int j=0; j<yolo_bbox_n; j++){
			//std::cout << ((lidar_pt.x[2*i+1]<bbox_pt.x[2*j]) || (lidar_pt.x[2*i]>bbox_pt.x[2*j+1]) || (lidar_pt.y[2*i+1]<bbox_pt.y[2*j]) || (lidar_pt.y[2*i]>bbox_pt.y[2*j+1])) <<"\n";
			if( (lidar_pt.x[2*i+1]<bbox_pt.x[2*j]) || (lidar_pt.x[2*i]>bbox_pt.x[2*j+1]) || (lidar_pt.y[2*i+1]<bbox_pt.y[2*j]) || (lidar_pt.y[2*i]>bbox_pt.y[2*j+1]) ){	
				if(j==(yolo_bbox_n-1)){
					lidar_pt.img_x.push_back(lidar_pt.x[2*i]) ;
					lidar_pt.img_y.push_back(lidar_pt.y[2*i]) ;
					lidar_pt.img_x.push_back(lidar_pt.x[2*i+1]) ;
					lidar_pt.img_y.push_back(lidar_pt.y[2*i+1]) ;
					lidar_pt.class_id.push_back(COCO_CLASSES_LIST.size()-1);
 				}		
			}
			else{
				break ;			
			}
		
		}	
	}


	resize(cv_ptr->image, resizeImg, Size(w,h));

	for(int j= 0; j<lidar_pt.img_x.size()/2; j++ ){
		rectangle(resizeImg, Point(lidar_pt.img_x[2*j], lidar_pt.img_y[2*j]), Point(lidar_pt.img_x[2*j+1], lidar_pt.img_y[2*j+1]),Scalar(255,0,255), 1) ;
		putText(resizeImg,COCO_CLASSES_LIST[lidar_pt.class_id[j]], Point(lidar_pt.img_x[2*j], lidar_pt.img_y[2*j]-6), FONT_HERSHEY_SIMPLEX, 0.5, Scalar(255,0,255),1) ;

	}

	for(int i=0; i<yolo_bbox_n; i++){
		rectangle(resizeImg, Point(bbox_pt.x[i*2],bbox_pt.y[i*2]), Point(bbox_pt.x[i*2+1],bbox_pt.y[i*2+1]), Scalar(255,212,0),1);
		putText(resizeImg,  COCO_CLASSES_LIST[bbox_pt.class_id[i]], Point(bbox_pt.x[i*2],bbox_pt.y[i*2]-6), FONT_HERSHEY_SIMPLEX, 0.5, Scalar(255,212,0),1);
	}



	end = clock();
	//std::cout <<"seconds : "<<double(end-begin)/CLOCKS_PER_SEC<<"\n";

	//imshow("result", resizeImg);
	//waitKey(1);

	sensor_msgs::ImagePtr output = cv_bridge::CvImage(std_msgs::Header(), "bgr8", resizeImg).toImageMsg();
	pub.publish(output);

}


int main(int argc, char** argv){
	//initialize ROS
	ros::init (argc, argv, "align_camera_lidar");
	ros::Time::init();
	ros::Rate r(10);
	ros::NodeHandle nh;

	image_transport::ImageTransport it(nh);
	//ros::AsyncSpinner spiner(1);
	

	//Create a Ros subscriber for the input point cloud 
	ros::Subscriber imagesub = nh.subscribe ("/image",0,image_cb);
	ros::Subscriber lidarsub = nh.subscribe ("/velodyne_points",0,cloud_cb);
	ros::Subscriber segsub = nh.subscribe ("/segmenter/objects_segmented",0, seg_cb);
	ros::Subscriber Bboxsub = nh.subscribe ("/TRT_yolov3/Bbox", 0, bbox_cb);

	
	pub = it.advertise("/fusion_nms/lidar_camera",0);
    
    
    //spiner.start();
    //ROS_INFO("alignment started...");

    //ros::waitForShutdown();
    //ROS_INFO("alignment exited...");
	while(ros::ok()){



		
		//Fuck!
		alignment();

		ros::spinOnce();
	}


}
