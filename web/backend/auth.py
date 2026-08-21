#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应急跌落事件监控系统 - Web会话认证
功能：
- 基于密码登录 + HMAC签名的会话令牌（HttpOnly Cookie）
- 令牌格式: "过期时间戳.签名"，签名 = HMAC-SHA256(密钥, 过期时间戳)
- 纯标准库实现，无额外依赖
"""

import hashlib
import hmac
import time

COOKIE_NAME = "dwdl_session"


def create_token(secret, ttl_hours):
    """生成会话令牌"""
    expiry = str(int(time.time() + ttl_hours * 3600))
    sig = hmac.new(secret.encode('utf-8'), expiry.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{expiry}.{sig}"


def verify_token(secret, token):
    """校验会话令牌，通过返回 True"""
    if not token or not secret:
        return False
    try:
        expiry, sig = token.split('.', 1)
        expected = hmac.new(secret.encode('utf-8'), expiry.encode('utf-8'), hashlib.sha256).hexdigest()
        # 常数时间比较防时序攻击
        if hmac.compare_digest(sig, expected) and int(expiry) > time.time():
            return True
    except (ValueError, AttributeError):
        pass
    return False
