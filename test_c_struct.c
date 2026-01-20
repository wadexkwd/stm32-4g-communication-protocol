#include <stdio.h>
#include "protocol.h"

int main() {
    // 打印 SensorData 结构体的大小
    printf("SensorData struct size: %zu bytes\n", sizeof(SensorData));
    
    // 检查各个字段的偏移量
    printf("packet_seq offset: %zu\n", offsetof(SensorData, packet_seq));
    printf("acc_x offset: %zu\n", offsetof(SensorData, acc_x));
    printf("acc_y offset: %zu\n", offsetof(SensorData, acc_y));
    printf("acc_z offset: %zu\n", offsetof(SensorData, acc_z));
    printf("gyro_x offset: %zu\n", offsetof(SensorData, gyro_x));
    printf("gyro_y offset: %zu\n", offsetof(SensorData, gyro_y));
    printf("gyro_z offset: %zu\n", offsetof(SensorData, gyro_z));
    printf("angle_x offset: %zu\n", offsetof(SensorData, angle_x));
    printf("angle_y offset: %zu\n", offsetof(SensorData, angle_y));
    printf("angle_z offset: %zu\n", offsetof(SensorData, angle_z));
    printf("pressure offset: %zu\n", offsetof(SensorData, pressure));
    printf("longitude offset: %zu\n", offsetof(SensorData, longitude));
    printf("latitude offset: %zu\n", offsetof(SensorData, latitude));
    
    return 0;
}
