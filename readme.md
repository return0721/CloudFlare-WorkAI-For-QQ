# CloudFlare WorkAI For QQ
## 如何使用?
### 环境要求:
#### PyCharm(不是必须的)
#### QQ:
QQNT 9.0+  
QQNTLoader 版本不限  
LLOneBot插件
#### Python:
Python 3.12.2  
websocket 版本不限  
flask 版本不限
### 使用教程:
#### 1. 你需要按照下面的说明来更改代码中 10 ~ 17 行的变量  
API_BASE_URL = [你的CloudFlare WorkAI API链接]  
headers = {"Authorization": "Bearer [你的CloudFlare WorkAI API Key]"}  
ROBOT_QQ = "[你机器人的QQ]"  
model_name = "[你想使用的模型名 例如: @cf/qwen/qwen1.5-14b-chat-awq]"
#### 2.把LLOneBot里的正向 WebSocket 服务器端口更改为 3001
#### 3.开始使用
## 如何跟AI聊天?
@机器人 内容