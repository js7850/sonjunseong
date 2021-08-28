cmake_minimum_required(VERSION 3.0.2)
project(additional_imu_driver)

find_package(catkin REQUIRED)
include_directories(${catkin_INCLUDE_DIRS})
find_package(catkin REQUIRED COMPONENTS
  roscpp
  sensor_msgs
  std_msgs
  geometry_msgs
)
catkin_package(
CATKIN_DEPENDS roscpp std_msgs  sensor_msgs geometry_msgs
)

include_directories(${catkin_INCLUDE_DIRS})
add_executable(imu_driver src/imu.cpp)
target_link_libraries(imu_driver ${catkin_LIBRARIES})