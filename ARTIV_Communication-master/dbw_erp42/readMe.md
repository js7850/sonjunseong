# ERP 42 Communication Code
_Author : Juho Song, Yeo HoYeong<br/>_
__Date : 2020.02.04.~__
## Languages
1. C++
2. Python 


!["test"](test.png)


## dbw_erp42_v2_release(2020)
### ERP42와 컴퓨터를 어떻게 연결할까?
1. ERP42에 가보면 RS232 to USB 케이블이 있을텐데 RS232는 ERP42에, USB는 컴퓨터에 연결한다. 
2. 터미널 창에 다음 명령어를 입력한다.
```
sudo chmod 666 /dev/ttyUSB0
```
3. ROS 파일을 실행한다. (ex.dbw_erp42_node.py, dbw_cmd_node.py ...)
4. 그 후에 자세한 송수신 정보는 [여기]()로
