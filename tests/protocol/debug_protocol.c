#include <stdio.h>
#include <string.h>
#include "protocol.h"

// 调试版本的解析函数
bool debug_protocol_parse_frame(uint8_t* buffer, uint16_t buffer_length, ProtocolFrame* frame) {
    printf("调试解析过程:\n");
    printf("缓冲区长度: %d\n", buffer_length);
    
    if (buffer_length < 8) { // 最小帧长度：2+1+2+0+1+2=8
        printf("失败: 缓冲区长度小于8字节\n");
        return false;
    }
    
    // 查找帧头
    int start_index = -1;
    for (int i = 0; i <= buffer_length - 8; i++) {
        if (buffer[i] == 0xAA && buffer[i+1] == 0x55) {
            start_index = i;
            printf("找到帧头在位置 %d: 0x%02X 0x%02X\n", i, buffer[i], buffer[i+1]);
            break;
        }
    }
    
    if (start_index == -1) {
        printf("失败: 未找到帧头\n");
        return false;
    }
    
    int current_index = start_index;
    
    // 命令码
    frame->cmd = buffer[++current_index];
    printf("命令码: 0x%02X\n", frame->cmd);
    
    // 数据长度
    frame->len = (buffer[++current_index] << 8) | buffer[++current_index];
    printf("数据长度: %d\n", frame->len);
    
    // 检查帧的总长度是否符合预期
    uint16_t expected_length = 8 + frame->len; // 7是固定部分，加上数据长度
    if (start_index + expected_length > buffer_length) {
        printf("失败: 预期帧长度 %d，实际 %d\n", start_index + expected_length, buffer_length);
        return false;
    }
    
    // 数据域
    if (frame->len > 0) {
        frame->data = &buffer[++current_index];
        current_index += frame->len;
        printf("数据域长度: %d字节\n", frame->len);
    } else {
        frame->data = NULL;
        printf("无数据域\n");
    }
    
    // 校验和
    uint8_t checksum = buffer[++current_index];
    printf("校验和: 0x%02X\n", checksum);
    
    uint8_t calculated_checksum = frame->cmd;
    calculated_checksum ^= (frame->len >> 8) & 0xFF;
    calculated_checksum ^= frame->len & 0xFF;
    if (frame->len > 0 && frame->data != NULL) {
        for (int i = 0; i < frame->len; i++) {
            calculated_checksum ^= frame->data[i];
        }
    }
    printf("计算的校验和: 0x%02X\n", calculated_checksum);
    
    if (checksum != calculated_checksum) {
        printf("失败: 校验和不匹配\n");
        return false;
    }
    
    // 帧尾
    if (buffer[++current_index] != 0x55 || buffer[++current_index] != 0xAA) {
        printf("失败: 帧尾不正确\n");
        return false;
    }
    
    printf("解析成功!\n");
    return true;
}

void test_parse_frame(uint8_t* buffer, uint16_t buffer_length) {
    ProtocolFrame frame;
    
    printf("解析缓冲区 (%d字节):\n", buffer_length);
    for (int i = 0; i < buffer_length; i++) {
        printf("%02X ", buffer[i]);
    }
    printf("\n\n");
    
    if (debug_protocol_parse_frame(buffer, buffer_length, &frame)) {
        printf("\n解析成功！\n");
        printf("命令码: 0x%02X\n", frame.cmd);
        printf("数据长度: %d字节\n", frame.len);
        
        if (frame.len > 0 && frame.data != NULL) {
            printf("数据内容:\n");
            for (int i = 0; i < frame.len; i++) {
                printf("%02X ", frame.data[i]);
            }
            printf("\n");
        }
    } else {
        printf("\n解析失败！\n");
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
