import websocket
import json
import re
import requests
from flask import Flask, request, jsonify

# Flask 服务器
app = Flask(__name__)

API_BASE_URL = "your cloudflare worker ai api link"
headers = {"Authorization": "Bearer ur cloudflare worker ai api key"}

# 机器人的 QQ 号
ROBOT_QQ = "ur robot's qq number"

# 模型名
model_name = "@cf/qwen/qwen1.5-14b-chat-awq"

def get_sender_info(message_data):
    """
    从消息数据中提取 sender 的 user_id 和 nickname。

    :param message_data: 包含消息信息的字典
    :return: 一个包含 user_id 和 nickname 的元组
    """
    sender = message_data.get('sender', {})
    user_id = sender.get('user_id')
    nickname = sender.get('nickname')
    return user_id, nickname


def run(model, inputs):
    input_data = {"messages": inputs}
    response = requests.post(f"{API_BASE_URL}{model}", headers=headers, json=input_data)
    return response.json()


def extract_message_info(data):
    at_info = None
    text_content = ""

    for message_part in data.get('message', []):
        if message_part['type'] == 'at':
            at_info = message_part['data']  # 提取 at 信息
        elif message_part['type'] == 'text':
            text_content = message_part['data']['text']  # 提取文本内容

    # 如果没有找到 at 信息，返回 False
    if at_info is None:
        return False

    return at_info, text_content


@app.route('/run', methods=['POST'])
def run_model():
    global model_name
    data = request.json
    inputs = data.get("inputs")

    if not inputs:
        return jsonify({"error": "Inputs are required"}), 400

    output = run(model_name, inputs)  # 默认使用 llama-3-8b-instruct
    return jsonify(output)


@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    group_id = data.get("group_id")
    message = data.get("message")

    if not group_id or not message:
        return jsonify({"error": "Group ID and message are required"}), 400

    # OneBot 的 HTTP 接口地址
    url = "http://localhost:3000/send_group_msg"

    # 构造请求体
    payload = {
        "group_id": group_id,
        "message": message
    }

    # 设置 headers 为 application/json
    headers = {
        "Content-Type": "application/json"
    }

    # 发送 POST 请求
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    return jsonify({
        "status_code": response.status_code,
        "response": response.json()  # 返回 OneBot 的响应
    })


def on_message(ws, message):
    try:
        parsed_data = json.loads(message)
        # print(parsed_data)
        raw_message = parsed_data.get("raw_message", "")
        user_id = parsed_data.get("user_id")
        group_id = parsed_data.get("group_id")  # 获取群组 ID
        ac, bc = get_sender_info(parsed_data)
        print("user_id: " + str(ac))
        # 提取消息信息
        extract_result = extract_message_info(parsed_data)
        if extract_result is False:
            print("没有at")
            # 确保 sender 存在
            sender_nickname = parsed_data.get("sender", {}).get("nickname", "未知用户")
            print("发送人: " + ac)  # 使用 sender.nickname
            print("内容: " + raw_message)  # 使用 raw_message
        else:
            a, b = extract_result  # 解包提取的结果
            name = a["name"]
            if name == "return 1;":
                # 发送到提到机器人的人的群组
                aioutput = send_to_http_server(b)  # 发送内容到 HTTP 服务器
                nameoutput = str(user_id)
                ac, bc = get_sender_info(parsed_data)
                output = f"[CQ:at,qq={ac},name={bc}] {aioutput}"  # 格式化输出
                send_message_to_onebot(group_id, output)
            else:
                print("没有at机器人.")
    except json.JSONDecodeError:
        print("Error decoding JSON")
    except Exception as e:
        print(e)


def send_to_http_server(content):
    http_url = "http://localhost:5000/run"  # 假设 Flask 服务器运行在本地
    payload = {
        "inputs": [
            {"role": "system", "content": "你是一个中国AI，请使用中文回答问题。"},
            {"role": "user", "content": content}
        ]
    }

    try:
        response = requests.post(http_url, json=payload)
        response_data = response.json()  # 假设服务器返回 JSON 格式
        print("Response from HTTP server:", json.dumps(response_data, indent=4, ensure_ascii=False))

        # 提取 AI 的响应内容
        if response_data.get('success'):
            return response_data['result']['response']  # 提取正确的响应内容
        else:
            return "AI did not return a valid response."
    except requests.RequestException as e:
        print("HTTP request failed:", e)
        return "Error occurred while contacting AI"


def send_message_to_onebot(group_id, message):
    url = "http://localhost:3000/send_group_msg"
    payload = {
        "group_id": group_id,
        "message": message
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Message sent to OneBot: {response.status_code}, {response.text}")


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("Connection closed")


def on_open(ws):
    print("Connection opened")
    # 发送一条消息（可选）
    ws.send(json.dumps({"type": "greeting", "message": "Hello, server!"}))


# 启动 Flask 服务器
if __name__ == '__main__':
    from threading import Thread

    # 启动 Flask 服务器
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    flask_thread.start()
    # 连接到 WebSocket 服务器
    websocket_url = "ws://127.0.0.1:3001/"  # 替换为你的 WebSocket 服务器地址
    ws = websocket.WebSocketApp(websocket_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    # 绑定打开连接时的回调函数
    ws.on_open = on_open

    # 开始连接并运行 WebSocket 客户端
    ws.run_forever()
