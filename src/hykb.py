# -*- coding: utf-8 -*-
# @Time    : 2025/11/22
# @Author  : Jyf0214
# @Fixed   : Jyf0214 (修复加密算法、动态Token获取及登录逻辑)
# @Format  : Gemini 3 (代码格式化、注释优化及语法规范化)
# 
# 【安全声明】
# 1. HTTP请求头中的 'Cookie' 仅用于模拟真实浏览器行为，看似不影响核心业务鉴权。
# 2. 账号的核心安全鉴权完全依赖于 POST 请求体中的 'scookie' 和 'device' (设备ID)。
# 3. 请务必保管好您的 scookie，切勿泄露给他人。

import requests
import random
import time
import re
import urllib.parse
from src.log import Log

log = Log()

class HaoYouKuaiBao:
    """
    好游快爆自动签到/种玉米脚本 (修复版)
    """
    def __init__(self, config):
        # 基础配置
        self.cookie = config.get('cookie', '')
        self.device_id = config.get('device_id', '')
        
        # 数美风控ID (Shumei Device ID)
        # 理论上该ID可以通过算法(类似森空岛脚本)计算生成，但涉及复杂的JS逆向。
        # 这里优先读取配置，如果配置为空，则使用抓包获取的一个通用值兜底。
        self.smdeviceid = config.get('smdeviceid', '')
        if not self.smdeviceid:
            # 每个人的id都不一样。不要随意使用别人的！
            self.smdeviceid = ""

        # 自动处理 scookie 编码 (兼容 URL 编码格式 %7C 或原始格式 |)
        raw_scookie = config.get('scookie', '')
        if '%' in raw_scookie:
            self.scookie = urllib.parse.unquote(raw_scookie)
        else:
            self.scookie = raw_scookie

        self.base_url = "https://huodong3.3839.com/n/hykb/cornfarm/index.php?imm=0"
        # 动态拼接 URL
        self.ajax_url = "https://huodong3.3839.com/n/hykb/cornfarm/ajax{}.php"
        
        self.headers = {
            "Host": "huodong3.3839.com",
            "Connection": "keep-alive",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; M2012K11AC Build/TKQ1.220829.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/115.0.5790.166 Mobile Safari/537.36Androidkb/1.5.7.807(android;M2012K11AC;13;1080x2320;WiFi);@4399_sykb_android_activity@",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://huodong3.3839.com",
            "Referer": self.base_url,
            "Cookie": self.cookie
        }

        # 页面动态参数缓存 (必须从页面获取，不可硬编码)
        self.dynamic_params = {
            "token": "default",
            "page_token": "",
            "random_str": ""
        }
        self.timeout = 15

    def fetch_page_params(self):
        """
        初始化：访问主页，正则提取隐藏的加密 Token
        """
        try:
            # log.info("正在获取页面初始化参数...")
            response = requests.get(self.base_url, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            html = response.text
            
            # 正则提取关键参数
            page_token_match = re.search(r'pageToken\s*=\s*[\'"](.*?)[\'"]', html)
            random_str_match = re.search(r'pageRandomStr\s*=\s*[\'"](.*?)[\'"]', html)
            token_val_match = re.search(r'token_value\s*=\s*[\'"](.*?)[\'"]', html)

            if page_token_match:
                self.dynamic_params['page_token'] = page_token_match.group(1)
            if random_str_match:
                self.dynamic_params['random_str'] = random_str_match.group(1)
            if token_val_match and token_val_match.group(1) != 'default':
                self.dynamic_params['token'] = token_val_match.group(1)

            if self.dynamic_params['page_token']:
                return True
            
            log.info("初始化失败：无法获取 PageToken，请检查 Header Cookie 是否有效")
            return False
        except Exception as e:
            log.info(f"网络请求异常: {e}")
            return False

    def build_data(self, ac):
        """
        构造加密请求体 (核心签名算法)
        """
        current_time = int(time.time() * 1000)
        # 核心签名算法: (时间戳 % 7) + 21
        # 此算法由 Jyf0214 逆向 JS 获得
        token_sign = (current_time % 7) + 21 
        
        data = {
            "ac": ac,
            "smdeviceid": self.smdeviceid, # 数美风控ID
            "verison": "1.5.7.807", # 官方拼写错误 verison，需保持一致
            "OpenAutoSign": "close",
            "r": str(random.random()),
            "token": self.dynamic_params['token'],
            "token_version": "v1", 
            "page_token": self.dynamic_params['page_token'],
            "token_time": str(current_time),
            "token_sign": str(token_sign),
            "random_str": self.dynamic_params['random_str'],
            "device": self.device_id,
            "scookie": self.scookie # 关键身份凭证
        }
        return data

    def _post(self, url_suffix, ac):
        """通用 POST 请求封装"""
        url = self.ajax_url.format(url_suffix)
        data = self.build_data(ac)
        try:
            res = requests.post(url, headers=self.headers, data=data, timeout=self.timeout)
            return res.json()
        except Exception as e:
            log.info(f"请求 {ac} 失败: {e}")
            return {"key": "error"}

    def login(self):
        """登录接口：获取真实 Token"""
        res = self._post("", "login") # ajax.php
        if res.get('key') == 'ok':
            # 登录成功后，服务端会返回一个新的 token，后续操作必须使用此 token
            new_token = res.get('config', {}).get('token_value')
            if new_token:
                self.dynamic_params['token'] = new_token
        return res

    def plant(self):
        """播种"""
        # 这里的 _plant 对应 ajax_plant.php，具体视服务端接口而定
        res = self._post("_plant", "Plant")
        if res.get('key') == 'ok':
            return "✅ 播种成功", 1
        elif str(res.get('seed')) == '0':
            return "❎ 播种失败：种子已用完", -1
        else:
            return f"❎ 播种失败: {res.get('key', 'unknown')}", 0

    def harvest(self):
        """收获"""
        res = self._post("_plant", "Harvest")
        if res.get('key') == 'ok':
            return "✅ 收获成功", True
        return f"❎ 收获失败: {res.get('key', 'unknown')}", False

    def watering(self):
        """浇水 (签到)"""
        # 这里的 _sign 对应 ajax_sign.php
        res = self._post("_sign", "Sign")
        if res.get('key') == 'ok':
            add = res.get('add_baomihua', 0)
            return f"✅ 浇水成功，获得 {add} 爆米花", 1
        elif str(res.get('key')) == '1001':
            return "☕ 今日已浇水", 0
        else:
            return f"❎ 浇水失败: {res}", -1

    def sgin(self):
        """
        执行主逻辑：初始化 -> 登录 -> 判断状态 -> 收获/播种/浇水
        """
        msg_list = []
        
        # 0. 检查配置完整性
        if not self.scookie or not self.device_id:
            return "❌ 配置文件错误：缺少 scookie 或 device_id，无法运行！"

        # 1. 初始化页面参数
        if not self.fetch_page_params():
            return "❌ 初始化失败，可能是 Cookie 失效或网络问题"

        # 2. 登录
        data = self.login()
        
        if data.get('key') == 'ok':
            config = data.get('config', {})
            nickname = config.get('nickname', '未知')
            csd_jdt = config.get('csd_jdt', '0%') # 成熟度
            grew = str(config.get('grew')) # 生长状态：-1未种植，1生长中
            
            status_msg = f"用户: {nickname} | 成熟度: {csd_jdt} | 状态: {grew}"
            log.info(f"登录成功: {nickname}")
            msg_list.append(status_msg)
            
            # 3. 根据状态执行动作
            if csd_jdt == "100%":
                # 成熟 -> 收获 -> 播种 -> 浇水
                h_msg, h_res = self.harvest()
                msg_list.append(h_msg)
                if h_res:
                    p_msg, p_res = self.plant()
                    msg_list.append(p_msg)
                    if p_res == 1:
                        w_msg, _ = self.watering()
                        msg_list.append(w_msg)
                        
            elif grew == '-1': 
                # 未种植 -> 播种 -> 浇水
                p_msg, p_res = self.plant()
                msg_list.append(p_msg)
                if p_res == 1:
                    w_msg, _ = self.watering()
                    msg_list.append(w_msg)
                    
            else:
                # 生长中 -> 浇水
                w_msg, _ = self.watering()
                msg_list.append(w_msg)
        else:
            err_key = data.get('key', 'unknown')
            msg_list.append(f"❌ 登录失败: {err_key}")
            log.info(f"登录失败详情: {data}")

        return "\n".join(msg_list)
