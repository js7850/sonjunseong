cmake_minimum_required(VERSION 3.0.2)
project(dbw_erp42)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  message_generation
)

catkin_install_python(PROGRAMS
  scripts/dbw_cmd_erp42.py
  scripts/dbw_erp42_node.py
  DESTINATION
  ${CATKIN_PACKAGE_SHARE_DESTINATION}/dbw_erp42
)

install(FILES
  scripts/dbw_erp42.launch
  scripts/run_serial.sh
  DESTINATION
  ${CATKIN_PACKAGE_SHARE_DESTINATION}/dbw_erp42
)

add_message_files(
  FILES
  ERPmsg.msg
)

generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS 
  message_runtime
  std_msgs
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)
