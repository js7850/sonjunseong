#!/usr/bin/env python

# CAN Command Sender : Ros Sub -> can_comms_erp42.py -> Serial Command Send
# Author : Yeo Ho Yeong (ARTIV), hoyeong23@dgist.ac.kr
# Date : 2020.07.07

import rclpy
import can_comms_erp42

from std_msgs.msg import Int16


NODENAME = "dbw_cmd"
rootname = '/dbw_cmd'

subAccel = '/Accel'
subBrake = '/Brake'
subSteer = '/Steer'
subGear = '/Gear'


class subNode():
    def __init__(self):
        rclpy.init()
        node = rclpy.create_node(NODENAME)
        accelSub = node.create_subscription(Int16, rootname+subAccel, self.accelCallback)
        brakeSub = node.create_subscription(Int16, rootname+subBrake, self.brakeCallback)
        steerSub = node.create_subscription(Int16, rootname+subSteer, self.steerCallback)
        gearSub = node.create_subscription(Int16, rootname+subGear, self.gearCallback)

        self.canSender = can_comms_erp42.control("/dev/ttyUSB0")

        print("-----Command Node Subscriber is Ready...-----")

        try:
            rclpy.spin(node)
        except:
            print("-------------------Error Detected!-------------------")


    def accelCallback(self, msg):
        self.canSender.setAccelCMD(int(msg.data))
        pass

    def brakeCallback(self, msg):
        self.canSender.setBrakeCMD(int(msg.data))
        pass

    def steerCallback(self, msg):
        self.canSender.setSteerCMD(int(msg.data))
        pass

    def gearCallback(self, msg):
        self.canSender.setGearCMD(int(msg.data))
        pass

if __name__ == "__main__":
    dbw_control = subNode()
    dbw_control.canSender.open_serial()
