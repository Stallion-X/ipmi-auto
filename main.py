import os
import sys
import time
import logging
import argparse
import platform
import subprocess
from typing import List, Optional
from apscheduler.schedulers.background import BlockingScheduler
from config import Config


class IPMIFanController:
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self.setup_logging()
        self.ipmitool_path = self._get_ipmitool_path()
        self.logger.info(f"IPMI风扇控制器启动 服务器: {self.config.server_ip}")
    
    def setup_logging(self):
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ipmi_fan_control.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _get_ipmitool_path(self) -> str:
        system = platform.system().lower()
        if system == "windows":
            return os.path.join(".", "ipmi", "ipmitool.exe")
        else:
            ipmitool_path = subprocess.run(['which', 'ipmitool'], 
                                         capture_output=True, text=True)
            if ipmitool_path.returncode == 0:
                return ipmitool_path.stdout.strip()
            else:
                self.logger.warning("系统中未找到ipmitool 尝试使用相对路径")
                return "ipmitool"
    
    def _execute_ipmi_command(self, command: str, retries: Optional[int] = None) -> Optional[str]:
        max_retries = retries if retries is not None else self.config.max_retries
        
        full_command = f'{self.ipmitool_path} -I lanplus -H {self.config.server_ip} -U {self.config.server_username} -P {self.config.server_password} {command}'
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"执行IPMI命令 (尝试 {attempt + 1}/{max_retries + 1}): {command}")
                result = subprocess.run(full_command, shell=True, capture_output=True, 
                                      text=True, timeout=30)
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    self.logger.warning(f"IPMI命令执行失败 (尝试 {attempt + 1}): {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.logger.warning(f"IPMI命令超时 (尝试 {attempt + 1})")
            except Exception as e:
                self.logger.error(f"IPMI命令执行异常 (尝试 {attempt + 1}): {e}")
            
            if attempt < max_retries:
                self.logger.info(f"等待 {self.config.retry_delay} 秒后重试...")
                time.sleep(self.config.retry_delay)
        
        self.logger.error(f"IPMI命令执行失败 已重试 {max_retries} 次: {command}")
        return None
    
    def disable_auto(self) -> bool:
        result = self._execute_ipmi_command('raw 0x30 0x30 0x01 0x00')
        if result is not None:
            self.logger.debug("已禁用自动风扇控制")
            return True
        return False
    
    def enable_auto(self) -> bool:
        result = self._execute_ipmi_command('raw 0x30 0x30 0x01 0x01')
        if result is not None:
            self.logger.debug("已启用自动风扇控制")
            return True
        return False
    
    def set_speed(self, percent: int) -> bool:
        if not (0 <= percent <= 100):
            self.logger.error(f"风扇转速百分比无效: {percent} (应在0-100之间)")
            return False
        
        if not self.disable_auto():
            return False
        
        hex_speed = hex(percent)
        result = self._execute_ipmi_command(f'raw 0x30 0x30 0x02 0xff {hex_speed}')
        if result is not None:
            self.logger.info(f"风扇转速设置为 {percent}%")
            return True
        return False
    
    def get_temp(self) -> List[float]:
        result = self._execute_ipmi_command('sensor')
        if result is None:
            self.logger.error("无法获取传感器数据")
            return []
        
        try:
            sensor_list = result.replace("\r\n", "\n").split('\n')
            temp_list = []
            
            for sensor in sensor_list:
                if 'Temp' in sensor and '|' in sensor:
                    try:
                        temp_str = sensor.split('|')[1].strip()
                        if temp_str and temp_str != 'na':
                            temp_value = float(temp_str)
                            temp_list.append(temp_value)
                    except (IndexError, ValueError) as e:
                        self.logger.debug(f"跳过无效温度传感器数据: {sensor}")
                        continue
            
            if temp_list:
                self.logger.debug(f"获取到温度数据: {temp_list}")
            else:
                self.logger.warning("未找到有效的温度传感器数据")
            
            return temp_list
            
        except Exception as e:
            self.logger.error(f"解析温度数据时出错: {e}")
            return []
    
    def get_fan_speed_for_temp(self, temp: float) -> Optional[int]:
        if self.config.use_fan_curve and self.config.fan_curve_points:
            return self._calculate_fan_speed_from_curve(temp)
        else:
            return self._get_fan_speed_from_thresholds(temp)
    
    def _calculate_fan_speed_from_curve(self, temp: float) -> int:
        curve_points = sorted(self.config.fan_curve_points, key=lambda x: x['temp'])
        
        if temp <= curve_points[0]['temp']:
            speed = curve_points[0]['fan_speed']
            self.logger.debug(f"温度 {temp}°C 低于曲线起点 使用最低转速 {speed}%")
            return speed
        
        if temp >= curve_points[-1]['temp']:
            speed = curve_points[-1]['fan_speed']
            self.logger.debug(f"温度 {temp}°C 高于曲线终点 使用最高转速 {speed}%")
            return speed
        
        for i in range(len(curve_points) - 1):
            point1 = curve_points[i]
            point2 = curve_points[i + 1]
            
            if point1['temp'] <= temp <= point2['temp']:
                temp_range = point2['temp'] - point1['temp']
                speed_range = point2['fan_speed'] - point1['fan_speed']
                temp_offset = temp - point1['temp']
                
                interpolated_speed = point1['fan_speed'] + (speed_range * temp_offset / temp_range)
                final_speed = round(interpolated_speed)
                
                self.logger.debug(f"温度 {temp}°C 在 {point1['temp']}-{point2['temp']}°C 区间 "
                                f"插值计算转速: {final_speed}% (从 {point1['fan_speed']}% 到 {point2['fan_speed']}%)")
                return final_speed
        
        self.logger.warning(f"风扇曲线计算异常 温度 {temp}°C 使用默认值")
        return 20
    
    def _get_fan_speed_from_thresholds(self, temp: float) -> int:
        for threshold in self.config.temperature_thresholds:
            if threshold['min_temp'] <= temp <= threshold['max_temp']:
                return threshold['fan_speed']
        
        self.logger.warning(f"未找到温度 {temp}°C 对应的风扇策略 使用默认值")
        return 20
    
    def auto_config(self):
        try:
            temp_list = self.get_temp()
            if not temp_list:
                self.logger.error("无法获取温度数据 跳过本次调节")
                return
            
            max_temp = max(temp_list)
            avg_temp = sum(temp_list) / len(temp_list)
            
            self.logger.info(f"当前温度 - 最高: {max_temp}°C 平均: {avg_temp:.1f}°C")
            
            target_speed = self.get_fan_speed_for_temp(max_temp)
            if target_speed is not None:
                if self.set_speed(target_speed):
                    curve_mode = "风扇曲线" if self.config.use_fan_curve else "阶梯模式"
                    self.logger.info(f"根据最高温度 {max_temp}°C 设置风扇转速为 {target_speed}% ({curve_mode})")
                else:
                    self.logger.error("设置风扇转速失败")
            
        except Exception as e:
            self.logger.error(f"自动配置过程中发生错误: {e}")
    
    def start_monitoring(self):
        try:
            self.logger.info(f"开始监控 间隔: {self.config.interval_seconds}秒")
            scheduler = BlockingScheduler()
            scheduler.add_job(self.auto_config, 'interval', 
                            seconds=self.config.interval_seconds)
            scheduler.start()
        except KeyboardInterrupt:
            self.logger.info("收到停止信号 正在关闭...")
        except Exception as e:
            self.logger.error(f"监控过程中发生错误: {e}")


def main():
    parser = argparse.ArgumentParser(description='IPMI自动风扇控制工具')
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    parser.add_argument('--test', action='store_true',
                       help='测试模式 只获取一次温度信息')
    
    args = parser.parse_args()
    
    try:
        controller = IPMIFanController(args.config)
        
        if args.test:
            controller.logger.info("测试模式 获取当前温度信息...")
            temp_list = controller.get_temp()
            if temp_list:
                max_temp = max(temp_list)
                avg_temp = sum(temp_list) / len(temp_list)
                print(f"温度信息 - 最高: {max_temp}°C 平均: {avg_temp:.1f}°C")
                target_speed = controller.get_fan_speed_for_temp(max_temp)
                print(f"建议风扇转速: {target_speed}%")
            else:
                print("无法获取温度信息")
        else:
            controller.start_monitoring()
            
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请先复制 config.example.json 为 config.json 并填入正确的服务器信息")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
