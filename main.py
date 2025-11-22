import os
import time
import yaml
import logging
import tempfile
from src.log import Log
from src.Push import Push
from src.Miui import Miui
from src.SkyWingsCloud import Cloud
from src.aliyundrive import Aliyundrive
from src.raincloud import RainCloud
from src.hykb import HaoYouKuaiBao
from src.arknights import Arknights
from src.Sign import XiaoHeiHe, JiaoYiMao, wyyyx

# 创建日志记录器
def setup_logger():
    # 创建日志记录器
    log = logging.getLogger("MainLogger")
    log.setLevel(logging.INFO)

    # 获取临时目录中的日志文件路径
    log_directory = tempfile.gettempdir()
    log_file = os.path.join(log_directory, 'app_log.txt')

    # 设置日志输出格式
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

    # 输出到文件
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    # 输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    return log, log_file

# 获取配置
def getconfig():
    path = os.path.dirname(os.path.realpath(__file__))
    with open(f'{path}/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def run():
    log, log_file = setup_logger()  # 初始化日志
    log.info("程序开始运行")
    log.info(f"日志文件路径: {log_file}")

    # 开始时间
    Begin = time.time()
    # 程序主体
    config = getconfig()
    SignToken = config['SignToken']
    data = "今日签到结果: \n"  # 使用 \n 进行换行

    # miui历史版本签到
    if SignToken.get('MiUI', {}).get('switch'):
        body = Miui(SignToken['MiUI'])
        result = body.Sign().replace("\n", "<br>")
        log.info(f"MIUI签到结果: {result}")
        data += "MIUI历史版本:\n" + result

    # --------------------------------------------------------
    # 好游快爆签到 (已修改为支持多账号列表遍历)
    # --------------------------------------------------------
    hykb_config = SignToken.get('Hykb')
    
    # 兼容处理：如果是单个字典(旧配置)，转为列表；如果是列表，直接使用
    if isinstance(hykb_config, dict):
        hykb_list = [hykb_config]
    elif isinstance(hykb_config, list):
        hykb_list = hykb_config
    else:
        hykb_list = []

    # 遍历执行
    hykb_results = ""
    for index, user_config in enumerate(hykb_list):
        if user_config.get('switch'):
            note = user_config.get('note', f'账号{index+1}')
            try:
                log.info(f"正在运行好游快爆: {note}")
                body = HaoYouKuaiBao(user_config)
                # 注意：这里调用的是 sgin() 还是 sgin() 取决于你的 src/hykb.py 里的定义
                # 假设原方法名是 sgin
                res = body.sgin().replace("\n", "<br>")
                log.info(f"好游快爆[{note}]签到结果: {res}")
                hykb_results += f"【{note}】:<br>{res}<br>"
            except Exception as e:
                log.info(f"好游快爆[{note}]运行出错: {e}")
                hykb_results += f"【{note}】: 运行出错<br>"
    
    if hykb_results:
        data += "\n\n好游快爆:\n" + hykb_results
    # --------------------------------------------------------

    if SignToken.get('XiaoHeiHe', {}).get('switch'):
        body = XiaoHeiHe(SignToken)
        result = body.Sgin().replace("\n", "<br>")
        log.info(f"小黑盒签到结果: {result}")
        data += "\n\n小黑盒:\n" + result

    if SignToken.get('JiaoYiMao', {}).get('switch'):
        body = JiaoYiMao(SignToken)
        result = body.Sgin().replace("\n", "<br>")
        log.info(f"交易猫签到结果: {result}")
        data += "\n\n交易猫:\n" + result

    # 天翼云盘签到
    if SignToken.get('Tyyp', {}).get('switch'):
        body = Cloud(SignToken['Tyyp'])
        result = body.sgin().replace("\n", "<br>")
        log.info(f"天翼云盘签到结果: {result}")
        data += "\n天翼云盘:\n" + result

    if SignToken.get('wyyyx', {}).get('switch'):
        body = wyyyx(SignToken)
        result = body.Sgin().replace("\n", "<br>")
        log.info(f"网易云游戏签到结果: {result}")
        data += "\n\n网易云游戏:\n" + result

    # 阿里云盘
    if SignToken.get('Aliyundrive', {}).get('switch'):
        body = Aliyundrive(SignToken['Aliyundrive'])
        result = body.sgin().replace("\n", "<br>")
        log.info(f"阿里云盘签到结果: {result}")
        data += "\n\n阿里云盘:\n" + result

    # 雨云签到
    if SignToken.get('Raincloud', {}).get('switch'):
        body = RainCloud(SignToken['Raincloud'])
        result = body.sgin().replace("\n", "<br>")
        log.info(f"雨云签到结果: {result}")
        data += "\n\n雨云:\n" + result

    if SignToken.get('Arknights', {}).get('switch'):
        body = Arknights(SignToken['Arknights'])
        result = body.sgin().replace("\n", "<br>")
        log.info(f"明日方舟签到结果: {result}")
        data += "\n\n明日方舟:\n" + result

    # 结束时间
    end = time.time()
    runtime_summary = f"本次运行时间: {round(end - Begin, 3)}秒"
    log.info(runtime_summary)
    data += "\n\n" + runtime_summary.replace("\n", "<br>")

    # 推送消息
    ts = Push(data, config['Push'])
    ts.push()

    log.info("签到完成，推送消息已发送")
    log.info(f"完整签到结果:\n{data}")

if __name__ == '__main__':
    run()
