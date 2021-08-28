/*******************************************************
 * Copyright (C) 2020-2021 김민종(Minjong Kim) <tlemsl@dgist.ac.kr or tlemsl8963@gmail.com>
 * Version 2.0.0
 * 
 * This file is part of DGIST ARTIV IMU team
 *
 * DGIST ARTIV can not be copied and/or distributed without the express
 * permission of 김민종(Minjong Kim)
 * 
 *******************************************************/

#include <bits/stdc++.h>

#include <ros/ros.h>
#include <std_msgs/Float64.h>
#include <std_msgs/Float32.h>
#include <sensor_msgs/Imu.h>
#include <geometry_msgs/PoseStamped.h>


ros::Publisher yaw_pub;
double alpha{1}, beta{1}, g{0.07};

using namespace std;
const double PI = acos(-1);
double threshold = 0.3;
int cali_time = 2;
string yaw_velocity_topic = "/imu/data_raw";
string yaw_topic = "imu/yaw";
string out_topic = "/imu_yaw";

int imu_type = 1; //type 0 : hwt, type 1 : 700000 manwon imu

double pi_2_pi(double angle) {
	while (angle < -180) angle += 360;
	while (angle > 180) angle -= 360;
	return angle;
}
class yaw_modification {
public:

	time_t time_now = time(NULL);
	time_t prev_time = time_now;
	double w = 0;
	double roll{0}, pitch{0};
	double yaw = 0;
	double hz = 100;
	double x{0}, y{0};
	double now_yaw = 0;
	double prev_yaw = 0;
	double delta_yaw= 0;
	double gps_yaw = 0;
	vector<double> gps_sample;
	vector< vector<double> > points;
	deque< vector<double> > auto_cali_points;
	
	double additional_yaw = 0;
	double calibration_yaw = 0;

	int cnt = 0;
	int auto_cali_flag = 0;

	ros::Subscriber gps_raw_sub, yaw_sub, gps_yaw_sub, utm_sub;
	yaw_modification(ros::NodeHandle *NodeHandle){
		ros::NodeHandle nh(*NodeHandle);
		ROS_INFO("start driver");
		yaw_sub = nh.subscribe(yaw_topic.c_str(), 1, &yaw_modification::yaw_callback, this);
		gps_raw_sub = nh.subscribe(yaw_velocity_topic.c_str(), 1, &yaw_modification::vel_callback, this);
		gps_yaw_sub = nh.subscribe("/gps_yaw", 1, &yaw_modification::gps_yaw_callback, this);
		utm_sub = nh.subscribe("/utm_fix", 1, &yaw_modification::utm_callback, this);

		yaw_pub = nh.advertise<std_msgs::Float64>(out_topic.c_str(), 1);
	}
	void gps_yaw_callback(const std_msgs::Float64::ConstPtr & msg){
		gps_yaw = msg->data;
	}
	void utm_callback(const geometry_msgs::PoseStamped::ConstPtr & msg){
		x = msg -> pose.position.x;
		y = msg -> pose.position.y;
		int size = auto_cali_points.size();
		time_now = time(NULL);
		if(auto_cali_flag){
			if(size<20){
				vector<double> t;
				t.push_back(x);
				t.push_back(y);
				auto_cali_points.push_back(t);
			}
			else{
				vector<double> slope;
				double l = sqrt((auto_cali_points[0][0]-auto_cali_points[size-1][0])*(auto_cali_points[0][0]-auto_cali_points[size-1][0]) + (auto_cali_points[0][1]-auto_cali_points[size-1][1])*(auto_cali_points[0][1]-auto_cali_points[size-1][1]));
				for(int i=0; i<size; i++){
					//cout<<(auto_cali_points[i][1] - y)<<","<<(auto_cali_points[i][0] - x)<<", "<<y<<endl;
					double temp = atan((auto_cali_points[i][1] - y)/(auto_cali_points[i][0] - x))*180/PI;
					//cout<<temp<<endl;
					slope.push_back(temp);
				}
				double average=accumulate(slope.begin(), slope.end(), 0.0)/double(size);
				vector<double> Variance;
				
				for(double islope : slope){
					double temp = islope - average;
					Variance.push_back(temp*temp);
				}
				double v = accumulate(Variance.begin(), Variance.end(), 0.0)/double(size);
				v = sqrt(v);
				cout<<"standard deviation :"<<v<<"average : "<<average<<"time : "<<double(time_now - prev_time)<<"len : "<<l<<endl;
				if(v < threshold && double(time_now - prev_time) >cali_time&&l>3){
					if(gps_yaw>90){calibration_yaw = average+180 - yaw;}
					else if(gps_yaw<-90){calibration_yaw = average-180 - yaw;}
					else{calibration_yaw = average - yaw;}
					std::cout << "/-------------------------------------/" << std::endl;
  					std::cout << "*      ARTIV IMU Calibration          /" << std::endl;
				  	std::cout << "/-------------------------------------/" << std::endl;
					
					prev_time = time(NULL);
				}
				auto_cali_points.pop_front();
				vector<double> t;
				t.push_back(x);
				t.push_back(y);
				auto_cali_points.push_back(t);
			}
		}
	}
	void yaw_callback(const std_msgs::Float32::ConstPtr & msg){
		if (!cnt){
			now_yaw = msg->data;
			prev_yaw = now_yaw;
			cnt = 1;
			return;
		}
		now_yaw = msg->data;
		if(abs(now_yaw - prev_yaw)>90){
			prev_yaw = now_yaw;
			return;	
		}
		delta_yaw = now_yaw - prev_yaw;// + additional_yaw;
		prev_yaw = now_yaw;
		//cout<<now_yaw<<", "<<prev_yaw<<", "<<additional_yaw<<endl;
		
		return;
	}
	void vel_callback(const sensor_msgs::Imu::ConstPtr& msg){
		w = double(msg->angular_velocity.z);
		if(imu_type){
			if(-0.004<w && w<0.004){w = 0;}
			double filter = sqrt(msg->angular_velocity.x*msg->angular_velocity.x + msg->angular_velocity.y*msg->angular_velocity.x);
			std_msgs::Float64 yaw_data;
			//yaw += delta_time*w;
			yaw += (w*alpha + delta_yaw*hz*beta)/(alpha+beta)/hz/max(1.0, filter*g);
			yaw_data.data = pi_2_pi(yaw*180/PI + calibration_yaw);
			yaw_pub.publish(yaw_data);
			cout<<yaw_data.data<<", "<<delta_yaw*hz<<", "<<w<<", "<<filter*g<<endl;
			//usleep(1000);
			//cout<<"w ,"<<w<<endl;
			return;
		}
		else{
			double filter = sqrt(msg->angular_velocity.x*msg->angular_velocity.x + msg->angular_velocity.y*msg->angular_velocity.x);
			std_msgs::Float64 yaw_data;
			//yaw += delta_time*w;
			yaw += (w*alpha + delta_yaw*hz*beta)/(alpha+beta)/hz/max(1.0, filter*g);
			yaw_data.data = pi_2_pi(yaw + calibration_yaw);
			yaw_pub.publish(yaw_data);
			//cout<<yaw_data.data<<", "<<", "<<calibration_yaw<<", "<<filter*g<<endl;
			//usleep(1000);
			//cout<<"w ,"<<w<<endl;
			return;
		}
	}
	void yaw_calibration(){
		time_t start, iter, end;
  		start = time(NULL);
		while (ros::ok()){
		    ros::spinOnce();
		    iter = time(NULL);
		    if ( (double)(iter - start) > 3 ){
				auto n_of_sample = gps_sample.size();
				if (n_of_sample != 0){
					calibration_yaw = std::accumulate( gps_sample.begin(), gps_sample.end(), 0.0) / n_of_sample - yaw;
				}
				std::cout << "Calibration is done with " <<  n_of_sample << std::endl;
				double temp{0};
				for(int i=0; i<n_of_sample; i++){
					temp = atan((points[i][1] - y)/(points[i][0] - x))*180/PI - calibration_yaw ;
					cout << temp <<endl;
					additional_yaw += temp;

				}
				additional_yaw = 0;
				auto_cali_flag = 1;
				ROS_INFO("additional_yaw : %lf, calibration_yaw : %lf", additional_yaw, calibration_yaw);
				return;
		    }
		    //continue when gps data is not loaded
		    if (gps_yaw == 0.0){
		     	std::cout << "Oops, GPS data is not recived" << std::endl;
		    	continue;
		  	}
		    if ((double)(iter - start) > 1){
				//std::cout << "Calibration is working" << std::endl;}
				gps_sample.push_back(gps_yaw);
				std::vector<double> t;
				t.push_back(x);
				t.push_back(y);
				points.push_back(t);
		    }
			sleep(0.001);
		}
	}
	
};

int main(int argc, char* argv[]) {
	ros::init(argc, argv, "additional_imu_driver");
	ros::NodeHandle nh;
	ros::param::get("~alpha", alpha);
	ros::param::get("~beta", beta);
	ros::param::get("~gamma", g);
	ros::param::get("~yaw_velocity_topic", yaw_velocity_topic);
	ros::param::get("~yaw_topic", yaw_topic);
	ros::param::get("~out_topic", out_topic);

	ros::param::get("~imu_type", imu_type);

	ros::param::get("~threshold", threshold);
	ros::param::get("~cali_time", cali_time);
	ROS_INFO("Alpha : %lf Beta : %lf gamma : %lf", alpha, beta, g);
	ROS_INFO("Imu type : %d", imu_type);
	ROS_INFO("Cali param %lf %d",threshold, cali_time);
	yaw_modification test(&nh);
	sleep(1);
	/*std::cout << "/-------------------------------------/" << std::endl;
  	std::cout << "*      ARTIV IMU Calibration          /" << std::endl;
  	std::cout << "/-------------------------------------/" << std::endl;
  	std::cout << std::endl;
  	std::cin.clear();
  	std::cin.get();
 	std::cout << "3" << std::endl;
	sleep(1);
	std::cout << "2" << std::endl;
	sleep(1);
	std::cout << "1" << std::endl;

  	test.yaw_calibration();
	*/
	ros::spin();
}
