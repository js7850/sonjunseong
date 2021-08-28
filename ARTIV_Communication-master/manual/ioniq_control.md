# IONIQ 컨트롤하기!
Date : 2020.07.08    
Author : 여호영

현재 ioniq과 통신을 하는 프로그램이 개발되어 있어 정보를 수신하고 명령을 송신하는 것이 가능하다.    
그렇다면 ioniq과는 어떻게 통신할까?    
해당 글은 큰 흐름만을 다루며 상세한 코드 및 명령어는 이전에 작성된 글로 대체할 것이다.    

## 1. SocketCAN을 이용해 ioniq과 컴퓨터를 연결하자.
SocketCAN으로 차량과 연결하는 과정은 이전에 메뉴얼로 작성되어 있으며 간단하니 천천히 따라가면 된다.    
[여기](https://github.com/DGIST-ARTIV/ARTIV_Communication/blob/master/manual/socket_can_connect.md)에 있는 과정 중에서 '2. 컴퓨터와 CAN 장치 연결'에 sudo ifconfig~ 명령어까지만 따라하자.    
그리고 ```candump can0``` 명령어로 연결이 잘 되어있는지만 확인해보자.    

## 2. Communication Package
여기서는 ROS 기반의 ioniq 통신 코드 구성과 설명이 나타나 있다.    

### 파일 구성
1. dbw_ioniq_node
+ dbw_ioniq_node.py    
-> can_msgs/Frame으로 들어오는 CAN data를 Float32MultiArray로 처리하여 ROS Publish.    

2. dbw_cmd_node
+ dbw_cmd_node.py    
-> dbw_cmd/Accel, ... 등의 이름으로 ROS Publish 되는 것을 Subscribe해서 명령값을 업데이트함.
+ can_communication.py
-> dbw_cmd_node에서 업데이트된 값을 바탕으로 차량에 can_msgs/Frame 형식으로 ROS Publish. (차량으로 그대로 입력됨.)

3. dbw_ioniq_bridge
+ dbw_ioniq_bridge.launch    
-> dbw_ioniq_node, dbw_cmd_node의 bridge 역할을 하며 이 파일을 실행하면 정보 송수신 기능이 동시에 가능하다.    
(*가끔 명령 송신에 문제가 생겨서 해결 중에 있음. 해결 된다면 업데이트될 예정.)

## 3. 직접 정보를 수신하고 명령을 송신하자!

### 정보 수신
1. roscore, source 등을 완료하고 dbw_ioniq_node.py를 실행한다.    
2. '/Ioniq_info' topic의 'std_msgs/Float32MultiArray' msg 형태로 ROS Subscribe한다.    
3. [통신 프로토콜 매뉴얼](https://docs.google.com/document/d/1Mvyvs1Tt20U99uA4o_h4c2-KB7s64NOQz6vd_-SGwh4/edit)을 참고해 정보를 Parsing에서 사용한다.    

### 명령 송신
1. roscore, source 등을 완료하고 dbw_cmd_node.py를 실행한다.    
2. 'dbw_cmd/Accel', ... topic의 'std_msgs/Int16' msg형태로 ROS Publish 한다.    
3. [통신 프로토콜 매뉴얼](https://docs.google.com/document/d/1Mvyvs1Tt20U99uA4o_h4c2-KB7s64NOQz6vd_-SGwh4/edit)을 참고해 각 데이터마다 알맞은 범위의 값을 입력한다.    

### 두 가지를 동시에!
1. source를 완료하고 다음 명령어를 입력한다.     
```
roslaunch dbw_ioniq_bridge dbw_ioniq_bridge.launch
```
2. '/Ioniq_info' topic의 'std_msgs/Float32MultiArray' msg 형태로 ROS Subscribe한다.    
3. 'dbw_cmd/Accel', ... topic의 'std_msgs/Int16' msg형태로 ROS Publish 한다.    
(*가끔 발신 오류 발생. 케이블 연결을 해체, 연결하면 됨.)
