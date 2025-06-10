import os
import time
import random
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import PeerUser, MessageActionChatAddUser
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, UserIsBlockedError

# ==== Cấu hình chung ====
API_ID = 22359020           # Thay bằng api_id của bạn
API_HASH = '6dbb9685d5fcb675affaa37ce5018d12'  # Thay bằng api_hash
GROUP_ID = -1002550301382  # ID nhóm dùng chung (cho chức năng 2)
MAX_PER_ACCOUNT = 20
DELAY_RANGE = (5, 10)

# ==== Thư mục ====
BASE = os.path.dirname(__file__)
ACC_DIR = os.path.join(BASE, "accounts")
DATA_DIR = os.path.join(BASE, "data")
PHONE_LIST = os.path.join(DATA_DIR, "phone_list.txt")
SENT_LOG = os.path.join(DATA_DIR, "sent_log.txt")
FAILED_LOG = os.path.join(DATA_DIR, "failed_log.txt")

# ==== Tiện ích ====
def read_lines(path):
    return set(open(path, encoding='utf-8').read().splitlines()) if os.path.exists(path) else set()

def append_line(path, line):
    with open(path, "a", encoding='utf-8') as f:
        f.write(line + "\n")

def delay():
    time.sleep(random.randint(*DELAY_RANGE))

def get_accounts():
    return [name for name in os.listdir(ACC_DIR) if os.path.isdir(os.path.join(ACC_DIR, name))]

def get_random_message():
    return random.choice([
        "Chào bạn",
    "Xin chào",
    "Nay khoẻ không b",
    "Dạo này bạn thế nào rồi",
    "Mình chào b nhé",
    "Hi",
    "Hello",
    "Dạo này còn chơi trên trang không ạ?",
    "Dạo nay ổn không b",
    "Nay tình hình như nào rồi b",
    ])

# ==== Chức năng 1: gửi từ file .txt ====
def send_from_phone_list(client, sent):
    to_send = []
    all_phones = read_lines(PHONE_LIST)
    for phone in all_phones:
        if phone not in sent:
            to_send.append(phone)
        if len(to_send) >= MAX_PER_ACCOUNT:
            break

    for phone in to_send:
        try:
            print(f"Gửi {phone}")
            entity = client.get_entity(phone)
            client.send_message(entity, get_random_message())
            append_line(SENT_LOG, phone)
        except (UserPrivacyRestrictedError, UserIsBlockedError, ValueError) as e:
            append_line(FAILED_LOG, f"{phone} - {str(e)}")
        except FloodWaitError as e:
            print(f"FloodWait {e.seconds}s")
            time.sleep(e.seconds)
        delay()

# ==== Chức năng 2: gửi từ nhóm forward ====
def send_from_group(client, sent):
    messages = client.get_messages(GROUP_ID, limit=100)
    to_send = []

    for msg in messages:
        if msg.forward and msg.forward.sender_id:
            uid = str(msg.forward.sender_id)
            if uid not in sent and uid not in to_send:
                to_send.append(uid)
            if len(to_send) >= MAX_PER_ACCOUNT:
                break

    for uid in to_send:
        try:
            print(f"Gửi user {uid}")
            entity = PeerUser(int(uid))
            client.send_message(entity, get_random_message())
            append_line(SENT_LOG, uid)
        except (UserPrivacyRestrictedError, UserIsBlockedError) as e:
            append_line(FAILED_LOG, f"{uid} - {str(e)}")
        except FloodWaitError as e:
            print(f"FloodWait {e.seconds}s")
            time.sleep(e.seconds)
        delay()

# ==== Chạy chương trình ====
def main():
    print("Chọn chức năng:")
    print("1. Gửi tin nhắn từ file số điện thoại (.txt)")
    print("2. Gửi tin từ nhóm chứa tin forward")
    choice = input("Nhập 1 hoặc 2: ").strip()

    accounts = get_accounts()
    if not accounts:
        print("Không tìm thấy tài khoản.")
        return

    for acc in accounts:
        acc_path = os.path.join(ACC_DIR, acc)
        print(f"\n>> Đang xử lý tài khoản {acc}...")
        client = TelegramClient(acc_path, API_ID, API_HASH)
        try:
            client.connect()
            if not client.is_user_authorized():
                print(f"Tài khoản {acc} chưa đăng nhập.")
                continue

            sent_set = read_lines(SENT_LOG)
            if choice == "1":
                send_from_phone_list(client, sent_set)
            elif choice == "2":
                send_from_group(client, sent_set)
            else:
                print("Lựa chọn không hợp lệ.")
                break

        finally:
            client.disconnect()

    print("\n✅ Đã hoàn tất toàn bộ.")

if __name__ == "__main__":
    main()
