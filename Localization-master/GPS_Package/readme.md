# ARTIV NMEA DRIVER 마스터!
## RTK-GNSS를 사용해봅시다.
버전 기준 : 1.6.1

### 1.어디서 다운받을 수 있나요?
DGIST-ARTIV/Localization의 Release에 있습니다.

귀찮다면 [여기](https://github.com/DGIST-ARTIV/Localization/releases)를 누르세요.
#
### 2.어떻게 사용하나요?
a. 다운받은 zip파일의 압축을 해제하고, `artiv_nmea_driver` 폴더를 `~/catkin_ws(or another catkin workspace)/src`로 옮깁니다.

b. 터미널을 여시고 `~/catkin_ws/src(or your path)/artiv_nmea_driver/scripts`로 들어가셔서 `chmod +x nmea_serial_driver.py`로 권한을 줍니다.

c. 우리에게 너무나도 익숙한 ros1 실행, `catkin_make` and `source devel/setup.bash`!

d. `roslaunch artiv_nmea_driver nmea_serial_driver`로 launch하시면 실행됩니다.
#
### 3.어떤 정보를 받을 수 있나요?
|<center>Topic Name<center>|<center>Message Type<center>|<center>Unit<center>|<center>Information<center>|
|:------------------------:|:--------------------------:|:------------------:|:-------------------------:|
|`/gps_deg`|Float64|°(deg)|차량의 heading 각을 표현 / 0° to 360° / 북쪽 0°, 동쪽 90°, 남쪽 180°, 서쪽 270°|
|`/gps_fix`|NavSatFix|°(deg)|현재 위치를 위도(latitude), 경도(longitude), 고도(altitude) 형태로 제공|
|`/gps_spd`|Float64|km/h|현재 차량의 speed를 제공|
|`/gps_vel`|TwistStamped|m/s|twist/linear의 x, y에 각각 x축 방향 속도와 y축 방향 속도를 제공|
|`/gps_yaw`|Float64|°(deg)|차량의 heading 각을 주행제어에서 사용하는 형태로 표현 / -180° to 180° / 동쪽 0°, 북쪽 90°, 남쪽 -90°, 서쪽 180° or -180° / +x축을 기준으로 위쪽 양수, 아래쪽 음수|
|`/utm_fix`|PoseStamped|m|현재 위치를 utm형태로 제공 / pose/position의 x, y로 표현|
