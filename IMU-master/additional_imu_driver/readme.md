---
version : 2.0.0(latest)
Author : 김민종(MinJong Kim)
Date : UNKNOWN
---
# Additional Imu Driver
지자기로 판단하는 HWT IMU의 각도가 차량 내부의 전자기기에 의해 이상해지는 문제를 해결하기위해 만든 pkg
YAW Accelation을 적분하여 각도를 추정한다.
Drift Error가 발생하기 때문에 auto calibration을 추가했다.

**artiv_hwtimu_driver에 있는 artiv_hwtimu_driver.launch 를 통해 켜는것을 권장한다.** 
## Dependency
1. ros1 melodic
2. gps
