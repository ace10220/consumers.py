import json
import random

from channels.generic.websocket import AsyncWebsocketConsumer

USERNAME_SYSTEM = "ace10220（管理人）"


class ChatConsumer(AsyncWebsocketConsumer):
    rooms = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if ChatConsumer.rooms is None:
            ChatConsumer.rooms = {}
        self.group_name = ""
        self.username = ""
        self.usericon = ""

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        await self.leave_chat()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        if text_data_json.get("data_type") == "join":
            self.username = text_data_json["username"]
            self.usericon = text_data_json["usericon"]
            await self.join_chat(text_data_json["roomname"])

        elif text_data_json.get("data_type") == "leave":
            await self.leave_chat()

        else:
            data = {
                "type": "chat_message",
                "message": text_data_json["message"],
                "username": self.username,
                "usericon": self.usericon,
                "count": ChatConsumer.rooms[self.group_name]["participants_count"],
                "random": random.random(),
            }
            await self.channel_layer.group_send(self.group_name, data)

    async def chat_message(self, data):
        data_json = {
            "message": data["message"],
            "username": data["username"],
            "usericon": data["usericon"],
            "count": data["count"],
            "random": data["random"],
        }
        await self.send(text_data=json.dumps(data_json))

    async def join_chat(self, room_name):
        self.group_name = f"chat_{room_name}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        if ChatConsumer.rooms.get(self.group_name) == None:
            ChatConsumer.rooms[self.group_name] = {"participants_count": 1}
        else:
            ChatConsumer.rooms[self.group_name]["participants_count"] += 1

        room = ChatConsumer.rooms[self.group_name]

        if self.format == "hiroba":
            message = "今" + str(room["participants_count"]) + "人が参加してるよ〜"
        elif self.format == "taimen":
            if room["participants_count"] == 1:
                message = "今もう１人のチャット相手を探し中だよ〜"
            else:
                message = "おっ、相手が見つかったよ〜、話しかけてみたら？"
        else:
            message = ""

        data = {
            "type": "chat_message",
            "message": message,
            "username": USERNAME_SYSTEM,
            "usericon": "https://pics.prcm.jp/e89879b4bd0cf/85770789/jpeg/85770789_480x480.jpeg",
            "count": room["participants_count"],
            "random": random.random(),
        }
        await self.channel_layer.group_send(self.group_name, data)

    async def leave_chat(self):
        if self.group_name == "":
            return
        
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

        room = ChatConsumer.rooms[self.group_name]

        room["participants_count"] -= 1

        if self.format == "hiroba":
            message = "今１人広場から抜けたよ〜"
        elif self.format == "taimen":
            message = "どうやら相手が帰ってしまったみたいだね、ボタンを押してもう１回お話ししよ〜"
        else:
            message = ""

        data = {
            "type": "chat_message",
            "message": message,
            "username": USERNAME_SYSTEM,
            "usericon": "https://pics.prcm.jp/e89879b4bd0cf/85770789/jpeg/85770789_480x480.jpeg",
            "count": room["participants_count"],
            "random": random.random(),
        }
        await self.channel_layer.group_send(self.group_name, data)

        self.group_name = ""