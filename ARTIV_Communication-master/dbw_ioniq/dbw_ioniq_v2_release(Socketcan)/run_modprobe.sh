#!/bin/bash

echo "First Setup for IONIQ(ROS1)..."

echo 'ALL ALL=(ALL) NOPASSWD:/bin/chmod'>>/etc/sudoers
echo 'ALL ALL=(ALL) NOPASSWD:/sbin/ip'>>/etc/sudoers
echo 'ALL ALL=(ALL) NOPASSWD:/sbin/ifconfig'>>/etc/sudoers

sudo modprobe can
sudo modprobe kvaser_usb
sudo ip link set can0 type can bitrate 500000
sudo ifconfig can0 up

sudo chmod +x ~/catkin_ws/src/dbw_ioniq_ros1/dbw_ioniq_node/scripts/dbw_ioniq_node.py
sudo chmod +x ~/catkin_ws/src/dbw_ioniq_ros1/dbw_cmd_node/scripts/dbw_cmd_node.py

echo "First Setup Complete!"
