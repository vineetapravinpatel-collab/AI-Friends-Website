import os
import json
import uuid
import threading
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from google import genai


# ============================================================
# SETTINGS
# ============================================================

APP_NAME = "AI Friends"

CHAT_FOLDER = os.path.join(
    os.path.expanduser("~"),
    "AI_Friends_Chats"
)


# ============================================================
# AI TEAM
# ============================================================

AI_INFO = {
    "Astra": {
        "avatar": "🌟",
        "model": "gemini-3.7-flash",
        "personality": (
            "You are Astra, the friendly and supportive AI Friend. "
            "You are especially good at studying, school subjects, "
            "learning and clear explanations."
        )
    },

    "Nova": {
        "avatar": "🔥",
        "model": "gemini-3.6-flash",
        "personality": (
            "You are Nova, the energetic and creative AI Friend. "
            "You are especially good at coding, technology, ideas "
            "and fun conversations."
        )
    },

    "Orion": {
        "avatar": "🧠",
        "model": "gemini-3.5-flash-lite",
        "personality": (
            "You are Orion, the analytical AI Friend. "
            "Think carefully, check reasoning and give clear, "
            "structured explanations."
        )
    }
}


# ============================================================
# ROUNDED BOX
# ============================================================

class RoundedBox(BoxLayout):

    def __init__(
        self,
        bg=(0.95, 0.95, 0.97, 1),
        radius=18,
        **kwargs
    ):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*bg)

            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(radius)]
            )

        self.bind(
            pos=self.update_rect,
            size=self.update_rect
        )

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# ============================================================
# MESSAGE BUBBLE
# ============================================================

class MessageBubble(RoundedBox):

    def __init__(
        self,
        name,
        avatar,
        message,
        is_user=False,
        **kwargs
    ):

        super().__init__(
            orientation="vertical",
            spacing=dp(5),
            padding=dp(12),
            size_hint_y=None,
            bg=(
                (0.78, 0.88, 1, 1)
                if is_user
                else (0.94, 0.94, 0.97, 1)
            ),
            **kwargs
        )

        header = Label(
            text=f"{avatar}  {name}",
            font_size=dp(17),
            bold=True,
            color=(0.08, 0.08, 0.12, 1),
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle"
        )

        header.text_size = (None, dp(28))

        body = Label(
            text=message,
            font_size=dp(16),
            color=(0.08, 0.08, 0.10, 1),
            size_hint_y=None,
            halign="left",
            valign="top"
        )

        body.bind(
            width=lambda obj, width:
            setattr(
                obj,
                "text_size",
                (width, None)
            )
        )

        body.bind(
            texture_size=lambda obj, size:
            setattr(
                obj,
                "height",
                size[1]
            )
        )

        self.add_widget(header)
        self.add_widget(body)

        self.bind(
            minimum_height=self.setter("height")
        )


# ============================================================
# MAIN APP
# ============================================================

class AIFriendsApp(App):

    def build(self):

        self.title = APP_NAME

        os.makedirs(
            CHAT_FOLDER,
            exist_ok=True
        )

        self.current_chat = None

        self.ai_enabled = {
            "Astra": True,
            "Nova": True,
            "Orion": True
        }

        self.ai_buttons = {}

        # ONE GEMINI CLIENT
        self.gemini = None

        self.setup_gemini()

        # ====================================================
        # ROOT
        # ====================================================

        root = BoxLayout(
            orientation="horizontal"
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        sidebar = RoundedBox(
            orientation="vertical",
            size_hint_x=None,
            width=dp(280),
            padding=dp(12),
            spacing=dp(8),
            bg=(0.95, 0.95, 0.98, 1)
        )

        title = Label(
            text="🤖 AI FRIENDS",
            font_size=dp(25),
            bold=True,
            color=(0.05, 0.05, 0.08, 1),
            size_hint_y=None,
            height=dp(55)
        )

        sidebar.add_widget(title)

        # ====================================================
        # NEW CHAT
        # ====================================================

        new_button = Button(
            text="＋  New Chat",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(50)
        )

        new_button.bind(
            on_press=self.new_chat
        )

        sidebar.add_widget(new_button)

        # ====================================================
        # AI TEAM
        # ====================================================

        sidebar.add_widget(
            Label(
                text="AI TEAM",
                font_size=dp(14),
                bold=True,
                color=(0.35, 0.35, 0.4, 1),
                size_hint_y=None,
                height=dp(35)
            )
        )

        for name, info in AI_INFO.items():

            button = Button(
                text=f"{info['avatar']}  {name}     ✓",
                font_size=dp(17),
                size_hint_y=None,
                height=dp(47)
            )

            button.bind(
                on_press=lambda instance, n=name:
                self.toggle_ai(n)
            )

            self.ai_buttons[name] = button

            sidebar.add_widget(button)

        # ====================================================
        # CHATS
        # ====================================================

        sidebar.add_widget(
            Label(
                text="CHATS",
                font_size=dp(14),
                bold=True,
                color=(0.35, 0.35, 0.4, 1),
                size_hint_y=None,
                height=dp(35)
            )
        )

        self.chat_list = BoxLayout(
            orientation="vertical",
            spacing=dp(5),
            size_hint_y=None
        )

        self.chat_list.bind(
            minimum_height=self.chat_list.setter("height")
        )

        chat_scroll = ScrollView(
            do_scroll_x=False
        )

        chat_scroll.add_widget(
            self.chat_list
        )

        sidebar.add_widget(chat_scroll)

        root.add_widget(sidebar)

        # ====================================================
        # MAIN AREA
        # ====================================================

        main = BoxLayout(
            orientation="vertical"
        )

        self.header = Label(
            text=APP_NAME,
            font_size=dp(26),
            bold=True,
            color=(0.05, 0.05, 0.08, 1),
            size_hint_y=None,
            height=dp(65)
        )

        main.add_widget(self.header)

        # ====================================================
        # CHAT AREA
        # ====================================================

        self.chat_box = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(12),
            size_hint_y=None
        )

        self.chat_box.bind(
            minimum_height=self.chat_box.setter("height")
        )

        self.chat_scroll = ScrollView(
            do_scroll_x=False
        )

        self.chat_scroll.add_widget(
            self.chat_box
        )

        main.add_widget(self.chat_scroll)

        # ====================================================
        # INPUT BAR
        # ====================================================

        input_bar = RoundedBox(
            orientation="horizontal",
            spacing=dp(8),
            padding=dp(8),
            size_hint_y=None,
            height=dp(70),
            bg=(0.94, 0.94, 0.97, 1)
        )

        self.input_box = TextInput(
            hint_text="Message AI Friends...",
            multiline=False,
            font_size=dp(18),
            foreground_color=(0.05, 0.05, 0.08, 1),
            background_color=(0, 0, 0, 0)
        )

        self.input_box.bind(
            on_text_validate=self.send_message
        )

        input_bar.add_widget(
            self.input_box
        )

        send_button = Button(
            text="➤",
            font_size=dp(25),
            size_hint_x=None,
            width=dp(65)
        )

        send_button.bind(
            on_press=self.send_message
        )

        input_bar.add_widget(
            send_button
        )

        main.add_widget(input_bar)

        root.add_widget(main)

        # ====================================================
        # START
        # ====================================================

        self.refresh_chats()

        chats = self.get_chats()

        if chats:

            self.open_chat(
                chats[0]["id"]
            )

        else:

            self.create_new_chat()

        return root


    # ========================================================
    # GEMINI SETUP
    # ========================================================

    def setup_gemini(self):

        print()
        print("========================================")
        print("        AI FRIENDS GEMINI SETUP")
        print("========================================")

        api_key = os.environ.get(
            "GEMINI_API_KEY"
        )

        if not api_key:

            print("GEMINI_API_KEY NOT FOUND")
            print("========================================")

            return

        try:

            self.gemini = genai.Client(
                api_key=api_key
            )

            print("Gemini connected successfully.")
            print("One API key will be used by all 3 AIs.")
            print("Astra :", AI_INFO["Astra"]["model"])
            print("Nova  :", AI_INFO["Nova"]["model"])
            print("Orion :", AI_INFO["Orion"]["model"])
            print("========================================")

        except Exception as error:

            print(
                "Gemini setup error:",
                error
            )

            print("========================================")


    # ========================================================
    # CHAT PATH
    # ========================================================

    def chat_path(self, chat_id):

        return os.path.join(
            CHAT_FOLDER,
            chat_id,
            "chat.json"
        )


    # ========================================================
    # CREATE CHAT
    # ========================================================

    def create_new_chat(self):

        chat_id = (
            datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            + "_"
            + uuid.uuid4().hex[:6]
        )

        now = datetime.now().isoformat()

        chat = {
            "id": chat_id,
            "title": "New Chat",
            "created": now,
            "updated": now,
            "messages": []
        }

        self.save_chat(chat)

        self.open_chat(chat_id)

        self.refresh_chats()


    # ========================================================
    # NEW CHAT
    # ========================================================

    def new_chat(self, instance):

        self.create_new_chat()


    # ========================================================
    # SAVE CHAT
    # ========================================================

    def save_chat(self, chat):

        folder = os.path.join(
            CHAT_FOLDER,
            chat["id"]
        )

        os.makedirs(
            folder,
            exist_ok=True
        )

        with open(
            self.chat_path(chat["id"]),
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                chat,
                file,
                indent=2,
                ensure_ascii=False
            )


    # ========================================================
    # LOAD CHAT
    # ========================================================

    def load_chat(self, chat_id):

        path = self.chat_path(chat_id)

        if not os.path.exists(path):
            return None

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except Exception as error:

            print(
                "Load chat error:",
                error
            )

            return None


    # ========================================================
    # GET CHATS
    # ========================================================

    def get_chats(self):

        chats = []

        if not os.path.exists(
            CHAT_FOLDER
        ):
            return chats

        for folder_name in os.listdir(
            CHAT_FOLDER
        ):

            folder = os.path.join(
                CHAT_FOLDER,
                folder_name
            )

            if not os.path.isdir(folder):
                continue

            path = os.path.join(
                folder,
                "chat.json"
            )

            if not os.path.exists(path):
                continue

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as file:

                    chats.append(
                        json.load(file)
                    )

            except Exception as error:

                print(
                    "Chat read error:",
                    error
                )

        chats.sort(
            key=lambda chat:
            chat.get("updated", ""),
            reverse=True
        )

        return chats


    # ========================================================
    # REFRESH CHAT LIST
    # ========================================================

    def refresh_chats(self):

        self.chat_list.clear_widgets()

        for chat in self.get_chats():

            chat_id = chat["id"]

            row = BoxLayout(
                orientation="horizontal",
                spacing=dp(3),
                size_hint_y=None,
                height=dp(45)
            )

            open_button = Button(
                text="💬 " + chat.get(
                    "title",
                    "New Chat"
                ),
                font_size=dp(14)
            )

            open_button.bind(
                on_press=lambda instance, cid=chat_id:
                self.open_chat(cid)
            )

            delete_button = Button(
                text="×",
                font_size=dp(20),
                size_hint_x=None,
                width=dp(40)
            )

            delete_button.bind(
                on_press=lambda instance, cid=chat_id:
                self.delete_chat(cid)
            )

            row.add_widget(open_button)
            row.add_widget(delete_button)

            self.chat_list.add_widget(row)


    # ========================================================
    # DELETE CHAT
    # ========================================================

    def delete_chat(self, chat_id):

        folder = os.path.join(
            CHAT_FOLDER,
            chat_id
        )

        try:

            if os.path.exists(folder):
                import shutil
                shutil.rmtree(folder)

        except Exception as error:

            print(
                "Delete error:",
                error
            )

        chats = self.get_chats()

        self.refresh_chats()

        if chats:

            self.open_chat(
                chats[0]["id"]
            )

        else:

            self.create_new_chat()


    # ========================================================
    # OPEN CHAT
    # ========================================================

    def open_chat(self, chat_id):

        chat = self.load_chat(
            chat_id
        )

        if chat is None:
            return

        self.current_chat = chat

        self.header.text = chat.get(
            "title",
            "AI Friends"
        )

        self.chat_box.clear_widgets()

        for message in chat.get(
            "messages",
            []
        ):

            self.add_message(
                message["name"],
                message["avatar"],
                message["text"],
                message.get(
                    "is_user",
                    False
                )
            )

        Clock.schedule_once(
            self.scroll_bottom,
            0.1
        )


    # ========================================================
    # ADD MESSAGE
    # ========================================================

    def add_message(
        self,
        name,
        avatar,
        text,
        is_user=False
    ):

        bubble = MessageBubble(
            name=name,
            avatar=avatar,
            message=text,
            is_user=is_user
        )

        self.chat_box.add_widget(
            bubble
        )


    # ========================================================
    # SCROLL
    # ========================================================

    def scroll_bottom(self, *args):

        self.chat_scroll.scroll_y = 0


    # ========================================================
    # TOGGLE AI
    # ========================================================

    def toggle_ai(self, name):

        self.ai_enabled[name] = not self.ai_enabled[name]

        info = AI_INFO[name]

        status = (
            "✓"
            if self.ai_enabled[name]
            else "✗"
        )

        self.ai_buttons[name].text = (
            f"{info['avatar']}  {name}     {status}"
        )


    # ========================================================
    # SEND MESSAGE
    # ========================================================

    def send_message(self, *args):

        text = self.input_box.text.strip()

        if not text:
            return

        if self.current_chat is None:
            return

        self.input_box.text = ""

        # USER MESSAGE
        user_message = {
            "name": "You",
            "avatar": "👤",
            "text": text,
            "is_user": True,
            "time": datetime.now().isoformat()
        }

        self.current_chat["messages"].append(
            user_message
        )

        self.current_chat["updated"] = (
            datetime.now().isoformat()
        )

        # CHAT TITLE
        if self.current_chat.get(
            "title"
        ) == "New Chat":

            title = text[:28]

            if len(text) > 28:
                title += "..."

            self.current_chat["title"] = title
            self.header.text = title

        self.save_chat(
            self.current_chat
        )

        self.add_message(
            "You",
            "👤",
            text,
            True
        )

        self.refresh_chats()

        # ASK ALL ENABLED AIs
        for name in AI_INFO:

            if not self.ai_enabled[name]:
                continue

            thread = threading.Thread(
                target=self.ask_ai,
                args=(name, text),
                daemon=True
            )

            thread.start()


    # ========================================================
    # ASK AI
    # ========================================================

    def ask_ai(self, name, user_text):

        if self.gemini is None:

            answer = (
                "Gemini API is not connected.\n\n"
                "Check GEMINI_API_KEY."
            )

            Clock.schedule_once(
                lambda dt:
                self.receive_ai(
                    name,
                    answer
                )
            )

            return

        info = AI_INFO[name]

        prompt = f"""
You are {name}, one of three AI Friends.

Your personality:
{info['personality']}

The user is chatting with the AI Friends group.

Respond naturally, clearly and helpfully.
Do not pretend to be another AI.
Do not mention these instructions.

User message:
{user_text}
"""

        try:

            print(
                f"[{name}] Asking {info['model']}..."
            )

            response = self.gemini.models.generate_content(
                model=info["model"],
                contents=prompt
            )

            answer = getattr(
                response,
                "text",
                None
            )

            if not answer:

                answer = (
                    f"{name} returned an empty response."
                )

            print(
                f"[{name}] Response received."
            )

        except Exception as error:

            error_text = str(error)

            print(
                f"[{name}] ERROR: {error_text}"
            )

            # FRIENDLY 503 MESSAGE
            if "503" in error_text:

                answer = (
                    f"{name} is temporarily busy "
                    "right now (503).\n\n"
                    "Please try sending the message again."
                )

            # FRIENDLY 404 MESSAGE
            elif "404" in error_text:

                answer = (
                    f"{name}'s model was not found (404).\n\n"
                    f"Current model: {info['model']}"
                )

            else:

                answer = (
                    f"{name} couldn't respond.\n\n"
                    f"Error: {error_text}"
                )

        Clock.schedule_once(
            lambda dt:
            self.receive_ai(
                name,
                answer
            )
        )


    # ========================================================
    # RECEIVE AI
    # ========================================================

    def receive_ai(
        self,
        name,
        answer
    ):

        if self.current_chat is None:
            return

        info = AI_INFO[name]

        message = {
            "name": name,
            "avatar": info["avatar"],
            "text": answer,
            "is_user": False,
            "time": datetime.now().isoformat()
        }

        self.current_chat["messages"].append(
            message
        )

        self.current_chat["updated"] = (
            datetime.now().isoformat()
        )

        self.save_chat(
            self.current_chat
        )

        self.add_message(
            name,
            info["avatar"],
            answer,
            False
        )

        self.refresh_chats()

        Clock.schedule_once(
            self.scroll_bottom,
            0.1
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("          AI FRIENDS STARTING")
    print("========================================")

    AIFriendsApp().run()