import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient, events
import pytz
import json


load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME')
CHATS = os.getenv('CHATS')
DB = os.getenv('DB')

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


@client.on(events.NewMessage(chats=CHATS))
async def handler(event):
    local_tz = pytz.timezone('Europe/Moscow')
    local_date = event.message.date.astimezone(local_tz)

    result = {
        'message': event.message.message,
        'date': local_date.strftime('%d.%m.%y-%H:%M:%S'),
        'files': event.message.file,
    }

    day = result['date'].split('-')
    channel_id = str(event.message.peer_id.channel_id)
    if result['files']:
        path = f'{channel_id}/{day[0]}/files/{day[1]}'
        result['files'] = await client.download_media(event.message, path)

    if not os.path.isfile(DB):
        db = {}
    else:
        with open(DB, 'r') as file:
            db = json.load(file)

    with open(DB, 'w') as file:
        if channel_id in db.keys():
            db[channel_id].append(result)
        else:
            db[channel_id] = [result]
        json.dump(
            db, file, indent=4, separators=(',', ':'), ensure_ascii=False
        )

client.start()
client.run_until_disconnected()
