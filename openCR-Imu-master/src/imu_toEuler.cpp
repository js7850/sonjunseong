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


#include <ros/ros.h>
#include <sensor_msgs/Imu.h>
#include <std_msgs/Float64.h>
#include <string>

ros::Publisher imuYawCb;

#define _USE_MATH_DEFINES
#include <cmath>

struct Quaternion {
    double w, x, y, z;
};

struct EulerAngles {
    double roll, pitch, yaw;
};

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

void imuCallback(const sensor_msgs::Imu::ConstPtr & msg){
  Quaternion tempData;
  std_msgs::Float64 yaw_data;

  tempData.x = msg->orientation.x;
  tempData.y = msg->orientation.y;
  tempData.z = msg->orientation.z;
  tempData.w = msg->orientation.w;

  yaw_data.data = ToEulerAngles(tempData).yaw;

  imuYawCb.publish(yaw_data);
}


int main(int argc, char **argv)
{
  ros::init(argc, argv, "imu_yaw_callback");
  ros::NodeHandle nh;

  imuYawCb  = nh.advertise<std_msgs::Float64>("/opencr/imu_yaw", 10);

  ros::Subscriber imu         = nh.subscribe("/turtlebot3/imu", 10, imuCallback);

  while (ros::ok())
    ros::spinOnce();

  return 0;
}
