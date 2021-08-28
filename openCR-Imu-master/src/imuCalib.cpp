/*******************************************************************************
* Copyright 2020 ARTIV
* Shinkansan
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/

#define PI 3.14159265
#include <ros/ros.h>
#include <sensor_msgs/Imu.h>
#include <std_msgs/Float64.h>
#include <string>
#include <time.h>
#include <vector>
#include <numeric>

ros::Publisher imuYawCb;

#define _USE_MATH_DEFINES
#include <cmath>

struct Quaternion {
    double w, x, y, z;
};

struct EulerAngles {
    double roll, pitch, yaw;
};

std_msgs::Float64 gps_yaw_data;
//gps_yaw_data->data = 0.0;
std::vector<float> gps_sample;
double yawInDeg;
double caliOffset;
bool isCalib = 0;

EulerAngles ToEulerAngles(Quaternion q) {
    EulerAngles angles;

    // roll (x-axis rotation)
    double sinr_cosp = 2 * (q.w * q.x + q.y * q.z);
    double cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y);
    angles.roll = std::atan2(sinr_cosp, cosr_cosp);

    // pitch (y-axis rotation)
    double sinp = 2 * (q.w * q.y - q.z * q.x);
    if (std::abs(sinp) >= 1)
        angles.pitch = std::copysign(M_PI / 2, sinp); // use 90 degrees if out of range
    else
        angles.pitch = std::asin(sinp);

    // yaw (z-axis rotation)
    double siny_cosp = 2 * (q.w * q.z + q.x * q.y);
    double cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z);
    angles.yaw = std::atan2(siny_cosp, cosy_cosp);


    return angles;
}


double rad2deg(double radian)
{
    return radian*180/PI;
}


void imuCallback(const sensor_msgs::Imu::ConstPtr & msg){
  Quaternion tempData;
  std_msgs::Float64 yaw_data;

  tempData.x = msg->orientation.x;
  tempData.y = msg->orientation.y;
  tempData.z = msg->orientation.z;
  tempData.w = msg->orientation.w;



  if (isCalib){
    yaw_data.data = rad2deg(ToEulerAngles(tempData).yaw) + caliOffset;
  }else{
    yaw_data.data = rad2deg(ToEulerAngles(tempData).yaw);
  }

  imuYawCb.publish(yaw_data);
}

void gpsCallBack(const std_msgs::Float64::ConstPtr & msg){
  gps_yaw_data.data = msg->data;
}


int main(int argc, char **argv)
{
  ros::init(argc, argv, "imu_yaw_callback");
  ros::NodeHandle nh;

  imuYawCb  = nh.advertise<std_msgs::Float64>("/opencr/imu_yaw", 10);
  ros::Subscriber imu         = nh.subscribe("/turtlebot3/imu", 10, imuCallback);
  ros::Subscriber gps_yaw         = nh.subscribe("/gps_yaw", 10, gpsCallBack);

  std::cout << "/-------------------------------------/" << std::endl;
  std::cout << "*      ARTIV IMU Calibration          /" << std::endl;
  std::cout << "/-------------------------------------/" << std::endl;
  std::cout << std::endl;
  std::cout << "Make sure gps_yaw is published before hit enter" << std::endl;
  std::cout << "press any key to start calib" << std::endl;
  std::cin.clear();
  std::cin;
  std::cout << "수평 평지에서 차량을 3초간 직진하십시오 \n 3초후 시작합니다." << std::endl;
  sleep(1);
  std::cout << "3" << std::endl;
  sleep(1);
  std::cout << "2" << std::endl;
  sleep(1);
  std::cout << "1" << std::endl;
  float gps_float_average = 0.0f;
  time_t start, iter, end;
  start = time(NULL);
  while (ros::ok()){
    ros::spinOnce();
    iter = time(NULL);

    if ( (double)(iter - start) > 3 ){
      auto n_of_sample = gps_sample.size();
      if (n_of_sample != 0){
        gps_float_average = std::accumulate( gps_sample.begin(), gps_sample.end(), 0.0) / n_of_sample;
      }
      std::cout << "Calibration is done with " <<  n_of_sample << std::endl;
      break;
    }
    //continue when gps data is not loaded
    if (gps_yaw_data.data == 0.0){
      std::cout << "Oops, GPS data is not recived" << std::endl;
      continue;}
    if ((double)(iter - start) > 1){
      //std::cout << "Calibration is working" << std::endl;}
      gps_sample.push_back(gps_yaw_data.data);
    }

  sleep(0.001);
  }
  //get diff between
  //auto temp = yawInDeg - 180;
  caliOffset = gps_float_average - yawInDeg;
  std::cout << "sample value is " << gps_float_average << "\ncali offset " << caliOffset << "\nyaw in deg " << yawInDeg << std::endl;
  isCalib = 1;

  while (ros::ok())
    ros::spinOnce();



  return 0;
}
