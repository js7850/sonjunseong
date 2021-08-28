cmake_minimum_required(VERSION 2.8.3)
project(alignment)

find_package(catkin REQUIRED COMPONENTS
    # ROS core
    roscpp
    pcl_conversions
    pcl_ros
    # 3rd modules for ROS, like Eigen
    cmake_modules
    # local packages
    std_msgs
	sensor_msgs

)

catkin_package(
    CATKIN_DEPENDS  roscpp
                    pcl_conversions
                    pcl_ros
    LIBRARIES ${PROJECT_NAME}
)

include_directories(
    include
    ${catkin_INCLUDE_DIRS}
)

add_executable(${PROJECT_NAME}
    src/align_realtime.cpp
)

add_dependencies(${PROJECT_NAME}
	sensor_msgs
)
target_link_libraries(${PROJECT_NAME}
    ${catkin_LIBRARIES}
)
