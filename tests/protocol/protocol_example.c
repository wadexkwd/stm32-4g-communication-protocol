#include "protocol.h"
#include <stdio.h>
#include <string.h>

void test_data_upload() {
    printf("=== 测试传感器数据上传帧 ===\n");

    // 创建多个传感器数据样本
    int sample_count = 2;
    SensorData sensor_data[sample_count];
    for (int i = 0; i < sample_count; i++) {
        sensor_data[i].packet_seq = i;
        sensor_data[i].acc_x = 1234 + i * 10;
        sensor_data[i].acc_y = -567 - i * 5;
        sensor_data[i].acc_z = 9876 + i * 20;
        sensor_data[i].gyro_x = 123 + i * 2;
        sensor_data[i].gyro_y = -45 - i;
        sensor_data[i].gyro_z = 67 + i * 3;
        sensor_data[i].angle_x = 10 + i;
        sensor_data[i].angle_y = -5 - i;
        sensor_data[i].angle_z = 3 + i * 2;
        sensor_data[i].pressure = 101325 + i * 100;
        sensor_data[i].longitude = 116.3974 + i * 0.0001;
        sensor_data[i].latitude = 39.9093 + i * 0.0001;
    }

    ProtocolFrame frame;
    frame.cmd = CMD_DATA_UPLOAD;
    frame.len = sizeof(SensorData) * sample_count;
    frame.data = (uint8_t*)&sensor_data;

    uint8_t buffer[512];
    uint16_t pack_len = protocol_pack_frame(&frame, buffer, sizeof(buffer));
    if (pack_len > 0) {
        printf("打包成功，长度：%d bytes\n", pack_len);
        printf("数据包：");
        for (int i = 0; i < pack_len; i++) {
            printf("%02X ", buffer[i]);
        }
        printf("\n");

        ProtocolFrame parse_frame;
        if (protocol_parse_frame(buffer, pack_len, &parse_frame)) {
            printf("解析成功\n");
            printf("命令码：0x%02X\n", parse_frame.cmd);
            printf("数据长度：%d bytes\n", parse_frame.len);

            if (parse_frame.cmd == CMD_DATA_UPLOAD && parse_frame.len % sizeof(SensorData) == 0) {
                int parsed_sample_count = parse_frame.len / sizeof(SensorData);
                printf("样本数量：%d\n", parsed_sample_count);

                SensorData* parsed_data = (SensorData*)parse_frame.data;
                for (int i = 0; i < parsed_sample_count; i++) {
                    printf("\n样本 %d：\n", i);
                    printf("包序：%d\n", parsed_data[i].packet_seq);
                    printf("加速度X：%d mg\n", parsed_data[i].acc_x);
                    printf("加速度Y：%d mg\n", parsed_data[i].acc_y);
                    printf("加速度Z：%d mg\n", parsed_data[i].acc_z);
                    printf("角速度X：%d °/s\n", parsed_data[i].gyro_x);
                    printf("角速度Y：%d °/s\n", parsed_data[i].gyro_y);
                    printf("角速度Z：%d °/s\n", parsed_data[i].gyro_z);
                    printf("角度X：%d °\n", parsed_data[i].angle_x);
                    printf("角度Y：%d °\n", parsed_data[i].angle_y);
                    printf("角度Z：%d °\n", parsed_data[i].angle_z);
                    printf("气压：%d Pa\n", parsed_data[i].pressure);
                    printf("经度：%.4f\n", parsed_data[i].longitude);
                    printf("纬度：%.4f\n", parsed_data[i].latitude);
                }
            }
        } else {
            printf("解析失败\n");
        }
    } else {
        printf("打包失败\n");
    }
    printf("\n");
}

void test_config_set() {
    printf("=== 测试配置参数设置帧 ===\n");

    ConfigParams config_params;
    config_params.sample_interval = 100;
    config_params.upload_interval = 5;
    config_params.data_format = 0x01;

    ProtocolFrame frame;
    frame.cmd = CMD_CONFIG_SET;
    frame.len = sizeof(ConfigParams);
    frame.data = (uint8_t*)&config_params;

    uint8_t buffer[256];
    uint16_t pack_len = protocol_pack_frame(&frame, buffer, sizeof(buffer));
    if (pack_len > 0) {
        printf("打包成功，长度：%d bytes\n", pack_len);
        printf("数据包：");
        for (int i = 0; i < pack_len; i++) {
            printf("%02X ", buffer[i]);
        }
        printf("\n");

        ProtocolFrame parse_frame;
        if (protocol_parse_frame(buffer, pack_len, &parse_frame)) {
            printf("解析成功\n");
            printf("命令码：0x%02X\n", parse_frame.cmd);
            printf("数据长度：%d bytes\n", parse_frame.len);

            if (parse_frame.cmd == CMD_CONFIG_SET && parse_frame.len == sizeof(ConfigParams)) {
                ConfigParams* parsed_params = (ConfigParams*)parse_frame.data;
                printf("采样间隔：%d ms\n", parsed_params->sample_interval);
                printf("上报间隔：%d s\n", parsed_params->upload_interval);
                printf("数据格式：0x%02X\n", parsed_params->data_format);
            }
        } else {
            printf("解析失败\n");
        }
    } else {
        printf("打包失败\n");
    }
    printf("\n");
}

void test_heartbeat() {
    printf("=== 测试心跳包 ===\n");

    HeartbeatData heartbeat_data;
    heartbeat_data.status = 0x00;

    ProtocolFrame frame;
    frame.cmd = CMD_HEARTBEAT;
    frame.len = sizeof(HeartbeatData);
    frame.data = (uint8_t*)&heartbeat_data;

    uint8_t buffer[256];
    uint16_t pack_len = protocol_pack_frame(&frame, buffer, sizeof(buffer));
    if (pack_len > 0) {
        printf("打包成功，长度：%d bytes\n", pack_len);
        printf("数据包：");
        for (int i = 0; i < pack_len; i++) {
            printf("%02X ", buffer[i]);
        }
        printf("\n");

        ProtocolFrame parse_frame;
        if (protocol_parse_frame(buffer, pack_len, &parse_frame)) {
            printf("解析成功\n");
            printf("命令码：0x%02X\n", parse_frame.cmd);
            printf("数据长度：%d bytes\n", parse_frame.len);

            if (parse_frame.cmd == CMD_HEARTBEAT && parse_frame.len == sizeof(HeartbeatData)) {
                HeartbeatData* parsed_data = (HeartbeatData*)parse_frame.data;
                printf("设备状态：0x%02X\n", parsed_data->status);
            }
        } else {
            printf("解析失败\n");
        }
    } else {
        printf("打包失败\n");
    }
    printf("\n");
}

int main() {
    printf("STM32与4G模块通信协议测试\n");
    printf("==========================\n\n");

    test_data_upload();
    test_config_set();
    test_heartbeat();

    return 0;
}
