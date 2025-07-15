import json
import os
import logging
from typing import Dict, Any, List


class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在 请先创建配置文件")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise Exception(f"读取配置文件失败: {e}")
    
    def _validate_config(self):
        required_fields = ['server', 'temperature_policy', 'monitoring']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"配置文件缺少必需字段: {field}")
        
        server_config = self.config['server']
        required_server_fields = ['ip', 'username', 'password']
        for field in required_server_fields:
            if field not in server_config:
                raise ValueError(f"服务器配置缺少必需字段: {field}")
        
        if not server_config['ip'] or not server_config['username']:
            raise ValueError("服务器IP和用户名不能为空")
    
    @property
    def server_ip(self) -> str:
        return self.config['server']['ip']
    
    @property
    def server_username(self) -> str:
        return self.config['server']['username']
    
    @property
    def server_password(self) -> str:
        return self.config['server']['password']
    
    @property
    def interval_seconds(self) -> int:
        return self.config['monitoring'].get('interval_seconds', 30)
    
    @property
    def temperature_thresholds(self) -> List[Dict[str, Any]]:
        return self.config['temperature_policy']['thresholds']
    
    @property
    def use_fan_curve(self) -> bool:
        return self.config['temperature_policy'].get('use_fan_curve', False)
    
    @property
    def fan_curve_points(self) -> List[Dict[str, Any]]:
        return self.config['temperature_policy'].get('fan_curve_points', [])
    
    @property
    def max_retries(self) -> int:
        return self.config['monitoring'].get('max_retries', 3)
    
    @property
    def retry_delay(self) -> int:
        return self.config['monitoring'].get('retry_delay', 5)
    
    @property
    def log_level(self) -> str:
        return self.config['monitoring'].get('log_level', 'INFO')
