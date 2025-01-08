from flask import Flask, request, abort
import re
import random
import logging
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = '4MCJd0jreXIagWo2jbHQbZhCuIxLVV0UtTMeF2956qAutxhNsgjJQNbF9iIWnKFpe2JAHfRcwTkkdkwHhdxRUMNyAHpdpRJMKsKn49fgOqNxORxDjDn9KFobKUUkNdkp8ncHwjQhJjSzhTztLpcdggdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = '16e040af937094b165e6d8806fb37225'

# 創建 LineBotApi 和 WebhookHandler 實例
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

logging.basicConfig(level=logging.INFO)

whitelist = ["egyywen0125", "egyythomto88", "egyy0944444444", "egyyvovo1226", "egyycola830908", "egyyagc525", "egyydavid8943", "egyyadonis149", "egyydj4719", "account3"]

user_state = {}

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logging.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_id = event.source.user_id
        text = event.message.text.strip()
        logging.info(f"Received message: {text} from user: {user_id}")

        if text == "結束":
            if user_id in user_state:
                del user_state[user_id]
            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="遊戲已結束，歡迎再來玩！")]
            )
            return

        if user_id not in user_state:
            user_state[user_id] = 'ask_account'
            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請輸入你的遊戲帳號。")]
            )
            return
        
        if user_state[user_id] == 'ask_account':
            if text in whitelist:
                user_state[user_id] = 'account_verified'
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text="帳號驗證成功，請輸入 '開始遊戲' 進行遊戲或 '結束' 結束遊戲。")]
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text="你的帳號不在名單中，無法使用此服務。")]
                )
                del user_state[user_id]
                
        elif user_state[user_id] == 'account_verified':
            if text == "開始遊戲":
                user_state[user_id] = 'ask_casino'
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text="請回答以下問題:\n【請問你目前遊玩的娛樂城?】")]
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text="請輸入 '開始遊戲' 或 '結束'。")]
                )
        elif user_state[user_id] in ['ask_casino', 'ask_game_type', 'ask_points']:
            handle_game_flow(user_id, text, event)

    except Exception as e:
        logging.error(f"Error in handle_message: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="發生錯誤，請稍後再試。")]
        )

def handle_game_flow(user_id, text, event):
    try:
        if user_state[user_id] == 'ask_casino':
            user_state[user_id] = 'ask_game_type'
            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="【請問遊戲類別?】")]
            )
        elif user_state[user_id] == 'ask_game_type':
            user_state[user_id] = 'ask_points'
            
            logging.
info("Starting connection...")
            line_bot_api.push_message(
                user_id, [
                    TextSendMessage(text="連線數據中..."),
                    TextSendMessage(text="數據連線完成"),
                    TextSendMessage(text="已設定成功"),
                    TextSendMessage(text="請輸入閒家莊家點數")
                ]
            )
        elif user_state[user_id] == 'ask_points':
            if re.match(r'^\d{2,3}\s+\d{2,3}$', text):
                points = text.split()
                supply_cards = calculate_supply_cards(points[0], points[1])
                prediction = predict(points[0], points[1], supply_cards)
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(
                        text=f"開始分析\n【預測結果】\n閒: {prediction['player']}%\n莊: {prediction['banker']}%\n和: {prediction['tie']}%\n推薦: {prediction['recommendation']}")
                    ]
                )
                line_bot_api.push_message(
                    user_id,
                    [TextSendMessage(text="請輸入閒家莊家點數")]
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text="請輸入有效的點數格式 (例如: 025 002 或 25 02)")]
                )
    except Exception as e:
        logging.error(f"Error in handle_game_flow: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="發生錯誤，請稍後再試。")]
        )

def calculate_tail_sum(points):
    total = sum(int(digit) for digit in points)
    tail_sum = total % 10
    return tail_sum

def calculate_supply_cards(player_points, banker_points):
    supply_cards = 0
    if len(player_points) == 3:
        supply_cards += 1
    if len(banker_points) == 3:
        supply_cards += 1
    return supply_cards

def predict(player_points, banker_points, supply_cards):
    player_tail_sum = calculate_tail_sum(player_points)
    banker_tail_sum = calculate_tail_sum(banker_points)
    diff = player_tail_sum - banker_tail_sum
    result = (diff / 2) + supply_cards
    result = int(result)

    if result % 2 == 0:
        banker_percentage = random.randint(60, 80)
        player_percentage = random.randint(20, 40)
    else:
        player_percentage = random.randint(60, 80)
        banker_percentage = random.randint(20, 40)

    total_percentage = player_percentage + banker_percentage
    tie_percentage = 100 - total_percentage
    if tie_percentage < 0:
        tie_percentage = 1
        adjust_factor = 99 / total_percentage
        player_percentage = int(player_percentage * adjust_factor)
        banker_percentage = int(banker_percentage * adjust_factor)

    recommendation = "閒" if result % 2 != 0 else "莊"

    return {
        'player': player_percentage,
        'banker': banker_percentage,
        'tie': tie_percentage,
        'recommendation': recommendation
    }

if __name__ == "__main__":
    app.run(port=3000)
