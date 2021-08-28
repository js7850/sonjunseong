# ARTIV IMU repository

HWT IMU를 위한 Repository 이다. 

Yaw Velocity를 적분하여 Yaw 값을 추정했으며, GPS를 이용하여 Auto calibration을 진행하였다.

Roll Pitch도 있지만, 개발중인 단계에 불과하다.

## How to??

```
roslaunch artiv_hwtimu_driver artiv_hwtimu_driver.launch
```