
import asyncio
import random
import os
import sys
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.types import PeerUser
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest
import json
import time

ACCOUNTS_FILE = "accounts.json"
MESSAGES_FILE = "messages.txt"
PHONES_FILE = "phones.txt"
SENT_LOG = "sent_log.txt"
ERROR_LOG = "error_log.txt"
FORWARD_LOG = "forward_sent_log.txt"
FORWARD_GROUP_NAME = "NHÓM CÀO DATA KANDES"

def load_accounts():
    with open(ACCOUNTS_FILE, 'r') as f:
        return json.load(f)

def load_messages():
    with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_phones():
    with open(PHONES_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def save_log(filename, text):
    with open(filename, 'a') as f:
        f.write(text + "\n")

def already_sent(phone):
    if not os.path.exists(SENT_LOG):
        return False
    with open(SENT_LOG, 'r') as f:
        return phone in f.read()

def already_sent_forward(user_id):
    if not os.path.exists(FORWARD_LOG):
        return False
    with open(FORWARD_LOG, 'r') as f:
        return str(user_id) in f.read()

async def send_from_file(account, messages):
    client = TelegramClient(f"sessions/{account['phone']}", account["api_id"], account["api_hash"])
    await client.start()
    phones = load_phones()
    count = 0
    for number in phones:
        if count >= 20:
            break
        if already_sent(number):
            continue
        try:
            # Bước 1: Thêm số điện thoại vào danh bạ
            contact = InputPhoneContact(client_id=0, phone=number, first_name="User", last_name="")
            result = await client(ImportContactsRequest([contact]))

            # Bước 2: Lấy user từ kết quả import hoặc get_entity fallback
            if result.users:
                user = result.users[0]
            else:
                user = await client.get_entity(number)

            # Bước 3: Gửi tin nhắn
            message = random.choice(messages)
            await client.send_message(user, message)
            print(f"[✓] Gửi thành công tới {number}")
            save_log(SENT_LOG, number)
            count += 1
            time.sleep(random.randint(5, 10))
        except Exception as e:
            print(f"[x] Lỗi gửi tới {number}: {e}")
            save_log(ERROR_LOG, f"{number} | {str(e)}")
    await client.disconnect()

async def send_from_forward(account, messages):
    client = TelegramClient(f"sessions/{account['phone']}", account["api_id"], account["api_hash"])
    await client.start()
    dialogs = await client(GetDialogsRequest(offset_date=None, offset_id=0,
                                             offset_peer=InputPeerEmpty(), limit=200, hash=0))
    group = next((d for d in dialogs.chats if d.title == FORWARD_GROUP_NAME), None)
    if not group:
        print(f"[!] Không tìm thấy nhóm '{FORWARD_GROUP_NAME}' trong tài khoản {account['phone']}")
        return
    messages_in_group = await client.get_messages(group, limit=100)
    sent = 0
    for msg in messages_in_group:
        if sent >= 20:
            break
        if msg.fwd_from and hasattr(msg.fwd_from, 'from_id'):
            user_id = msg.fwd_from.from_id.user_id
            if already_sent_forward(user_id):
                continue
            try:
                message = random.choice(messages)
                await client.send_message(user_id, message)
                print(f"[✓] Đã gửi tới user {user_id}")
                save_log(FORWARD_LOG, str(user_id))
                sent += 1
                time.sleep(random.randint(5, 10))
            except Exception as e:
                print(f"[x] Lỗi gửi tới user {user_id}: {e}")
                save_log(ERROR_LOG, f"{user_id} | {str(e)}")
    await client.disconnect()

async def main():
    if not os.path.exists("sessions"):
        os.makedirs("sessions")
    print("Chọn chức năng:")
    print("1. Gửi tin nhắn từ file số điện thoại (.txt)")
    print("2. Gửi tin từ nhóm chứa tin forward")
    choice = input("Nhập 1 hoặc 2: ").strip()
    if choice not in ['1', '2']:
        print("Lựa chọn không hợp lệ.")
        return

    accounts = load_accounts()
    messages = load_messages()

    for acc in accounts:
        print(f">> Đang xử lý tài khoản {acc['phone']}...")
        try:
            if choice == '1':
                await send_from_file(acc, messages)
            elif choice == '2':
                await send_from_forward(acc, messages)
        except Exception as e:
            print(f"[!] Lỗi kết nối tài khoản {acc['phone']}: {e}")
            save_log(ERROR_LOG, f"{acc['phone']} | {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
