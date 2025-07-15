# IPMI Auto Fan Control

🌡️ 智能的戴尔服务器 IPMI 自动风扇控制工具

一个专业的、跨平台的 IPMI 风扇控制解决方案，支持自定义温度策略、完善的错误处理和详细的日志记录。

## ✨ 特性

- 🔧 **配置化管理** - 通过 JSON 配置文件管理所有设置
- 🖥️ **跨平台支持** - 支持 Windows 和 Linux 系统
- 🔄 **智能重试** - 网络异常时自动重试，提高稳定性
- 📊 **详细日志** - 完整的操作日志，便于监控和调试
- ⚙️ **灵活策略** - 可自定义温度阈值和风扇转速策略
- 🧪 **测试模式** - 支持测试模式，验证配置和连接

## 🚀 快速开始

### 1. 环境要求

**Windows:**
- Python 3.7+
- 项目自带 ipmitool.exe

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install ipmitool

# CentOS/RHEL
sudo yum install ipmitool

# 或者使用项目自带的工具
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置设置

复制示例配置文件并修改：

```bash
cp config.example.json config.json
```

编辑 `config.json` 填入你的服务器信息：

```json
{
  "server": {
    "ip": "你的服务器IP",
    "username": "IPMI用户名", 
    "password": "IPMI密码"
  },
  "temperature_policy": {
    "thresholds": [
      {
        "min_temp": 79,
        "max_temp": 999,
        "fan_speed": 40,
        "description": "高温模式"
      }
    ]
  },
  "monitoring": {
    "interval_seconds": 30,
    "max_retries": 3,
    "retry_delay": 5,
    "log_level": "INFO"
  }
}
```

### 4. 运行

**测试连接：**
```bash
python main.py --test
```

**开始监控：**
```bash
python main.py
```

**使用自定义配置文件：**
```bash
python main.py -c /path/to/your/config.json
```

## 📋 配置说明

### 服务器配置
- `ip`: 服务器的 IPMI IP 地址
- `username`: IPMI 用户名
- `password`: IPMI 密码

### 温度策略配置
温度阈值按优先级排序，程序会使用第一个匹配的策略：

```json
{
  "min_temp": 最低温度,
  "max_temp": 最高温度,
  "fan_speed": 风扇转速百分比 (0-100),
  "description": "策略描述"
}
```

### 监控配置
- `interval_seconds`: 监控间隔（秒）
- `max_retries`: 命令失败时的最大重试次数
- `retry_delay`: 重试间隔（秒）
- `log_level`: 日志级别 (DEBUG, INFO, WARNING, ERROR)

## 📊 日志文件

程序会生成 `ipmi_fan_control.log` 日志文件，包含：
- 温度监控数据
- 风扇调节操作
- 错误和重试信息
- 系统状态变化

## 🔧 命令行选项

```bash
python main.py [选项]

选项:
  -c, --config CONFIG  指定配置文件路径 (默认: config.json)
  --test              测试模式，只获取一次温度信息
  -h, --help          显示帮助信息
```

## 🛠️ 故障排除

### 常见问题

**1. 无法连接到服务器**
- 检查 IP 地址是否正确
- 确认 IPMI 用户名和密码
- 验证网络连通性

**2. 找不到 ipmitool**
- Linux: 安装 ipmitool 包
- Windows: 确保 ipmi 目录下有 ipmitool.exe

**3. 权限错误**
- 确认 IPMI 用户有足够的权限
- 检查服务器 IPMI 设置

**4. 温度读取失败**
- 验证服务器支持温度传感器
- 检查传感器命名是否包含 'Temp'

### 调试模式

启用详细日志：
```json
{
  "monitoring": {
    "log_level": "DEBUG"
  }
}
```

## 🔒 安全注意事项

- 配置文件包含敏感信息，请妥善保管
- 建议为 IPMI 创建专用用户账户
- 定期更新 IPMI 密码
- 限制配置文件的访问权限

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 基于 ipmitool 工具
- 使用 APScheduler 进行任务调度

---

**注意**: 此工具专为戴尔服务器设计，其他品牌服务器可能需要调整 IPMI 命令。使用前请在测试环境中验证。
