#include <stdio.h>
#include <string.h>
#include "protocol.h"

void test_parse_frame(uint8_t* buffer, uint16_t buffer_length) {
    ProtocolFrame frame;
    
    printf("解析缓冲区 (%d字节):\n", buffer_length);
    for (int i = 0; i < buffer_length; i++) {
        printf("%02X ", buffer[i]);
    }
    printf("\n\n");
    
    if (protocol_parse_frame(buffer, buffer_length, &frame)) {
        printf("解析成功！\n");
        printf("命令码: %02X\n", frame.cmd);
        printf("数据长度: %d字节\n", frame.len);
        
        if (frame.len > 0 && frame.data != NULL) {
            printf("数据内容:\n");
            for (int i = 0; i < frame.len; i++) {
                printf("%02X ", frame.data[i]);
            }
            printf("\n");
        }
    } else {
        printf("解析失败！\n");
    }
    
    printf("====================================\n");
}

void test_heartbeat_frame() {
    uint8_t buffer[] = {0xAA, 0x55, 0x04, 0x00, 0x01, 0x00, 0x05, 0x55, 0xAA};
    printf("测试心跳包解析:\n");
    test_parse_frame(buffer, sizeof(buffer));
}

void test_config_frame() {
    uint8_t buffer[] = {0xAA, 0x55, 0x02, 0x00, 0x05, 0x64, 0x00, 0x05, 0x00, 0x01, 0x67, 0x55, 0xAA};
    printf("测试配置帧解析:\n");
    test_parse_frame(buffer, sizeof(buffer));
}

void calculate_checksum_test() {
    uint8_t cmd = 0x04;
    uint16_t len = 0x01;
    uint8_t data[] = {0x00};
    
    uint8_t checksum = cmd;
    checksum ^= (len >> 8) & 0xFF;
    checksum ^= len & 0xFF;
    checksum ^= data[0];
    
    printf("测试校验和计算:\n");
    printf("命令码: %02X\n", cmd);
    printf("数据长度: %04X\n", len);
    printf("数据: %02X\n", data[0]);
    printf("计算的校验和: %02X\n", checksum);
    
    printf("====================================\n");
}

int main() {
    printf("=== 协议解析调试测试 ===\n\n");
    
    calculate_checksum_test();
    test_heartbeat_frame();
    test_config_frame();
    
    return 0;
}
