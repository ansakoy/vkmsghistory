import datetime
import os
from pathlib import Path

import vk_api

from secrets import PARTICIPANTS, BASE_PEER_ID, TOKEN, CHAT_ID_XV, CHAT_ID_XX

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = os.path.join(BASE_DIR, "data")


def process_attachments(attachments):
    result = ""
    for attachment in attachments:
        atch_type = attachment.get("type")
        if atch_type == "photo":
            sizes = attachment.get("sizes", [{}])
            url = sizes[-1].get("url")
            if url:
                result += f"\nПрикрепленное изображение: {url}"
        elif atch_type == "audio":
            info = attachment.get("audio", {})
            artist = info.get("artist")
            title = info.get("title")
            phrase = ""
            if artist:
                phrase += f"{artist}"
            if title:
                if artist:
                    phrase += f" - {title}"
                else:
                    phrase += f"{title}"
            result += f"\nПрикрепленное аудио: {phrase}"
        elif atch_type == "link":
            info = attachment.get("link", {})
            url = info.get("url")
            if url:
                result += f"\nПрикрепленная ссылка: {url}"
    if len(result):
        return f"\n{result}"


def get_chunk_data(vk, peer_id, start_message_id, offset, count):
    """Collect data from one page"""
    print(f"OFFSET: {offset}")
    data = vk.messages.getHistory(peer_id=peer_id, start_message_id=start_message_id, offset=offset, count=count)
    items = data["items"]
    chunk_length = len(items)
    if chunk_length <= 0:
        print(f"OVER. TOTAL ITEMS: {count}")
        return None, None, None
    return items, -chunk_length, -1


def collect_history(title, peer_id, subject_dir="noname", token=TOKEN):
    """Collect history from messenger"""
    vk_session = vk_api.VkApi(token=token)

    vk = vk_session.get_api()

    fname = f"{title}_{datetime.date.today().strftime("%Y_%m_%d")}.txt"
    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)
    subject_dir_path = os.path.join(DATA_DIR, subject_dir)
    if not os.path.isdir(subject_dir_path):
        os.mkdir(subject_dir_path)
    fpath = os.path.join(subject_dir_path, fname)

    with open(fpath, "w", encoding="utf-8") as handler:
        count = 0
        offset = -200
        step = 200
        while offset < 0:
            items, last_idx, idx = get_chunk_data(
                vk=vk, peer_id=peer_id, start_message_id=1, offset=offset, count=step,
            )
            if items is None:
                break
            while last_idx <= idx:
                item = items[idx]
                text = item["text"]

                count += 1
                print(item["conversation_message_id"])
                date = datetime.datetime.fromtimestamp(item["date"]).strftime("%d.%m.%Y, %H:%M")
                print(date)
                print(text[:100])
                idx -= 1

                from_id = item["from_id"]
                author = PARTICIPANTS.get(from_id, "UNKNOWN")
                message = f"\n\n\n{author} - {date}\n\n{text}"
                attachments = item["attachments"]
                if len(attachments):
                    attached = process_attachments(attachments)
                    if attached:
                        print(attached)
                        message += attached
                if len(text):
                    handler.write(message)
            offset -= step
        print(count)


# if __name__ == '__main__':
#     collect_history(token=TOKEN, title="vkmsghist")
