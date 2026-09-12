import os
import time
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# CEREBRAS
# ============================================================

API_KEY = os.environ.get("CEREBRAS_API_KEY")

if not API_KEY:
    print("ERROR: CEREBRAS_API_KEY NOT FOUND")
    client = None
else:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.cerebras.ai/v1"
    )
    print("Cerebras connected!")


# ============================================================
# AI TEAM
# ============================================================

AI_INFO = {
    "Astra": {
        "avatar": "🌟",
        "personality": "friendly, supportive, excellent at studying and explanations"
    },

    "Nova": {
        "avatar": "🔥",
        "personality": "energetic, creative, excellent at coding and ideas"
    },

    "Orion": {
        "avatar": "🧠",
        "personality": "analytical, logical and structured"
    }
}


MODEL = "gpt-oss-120b"


# ============================================================
# WEB PAGE
# ============================================================

HTML = """
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>AI Friends</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #101116;
    color: white;
}

.header {
    padding: 18px;
    text-align: center;
    font-size: 25px;
    font-weight: bold;
    background: #181a22;
}

.team {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 12px;
    background: #151720;
    flex-wrap: wrap;
}

.ai {
    padding: 8px 14px;
    border-radius: 20px;
    background: #252936;
    font-size: 15px;
}

.chat {
    height: calc(100vh - 170px);
    overflow-y: auto;
    padding: 15px;
    padding-bottom: 80px;
}

.message {
    margin-bottom: 15px;
    padding: 13px;
    border-radius: 15px;
    background: #20232d;
}

.user {
    background: #263b63;
}

.name {
    font-weight: bold;
    margin-bottom: 6px;
}

.input-area {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    gap: 8px;
    padding: 10px;
    background: #181a22;
}

input {
    flex: 1;
    padding: 13px;
    border-radius: 12px;
    border: none;
    outline: none;
    font-size: 16px;
}

button {
    padding: 12px 18px;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    cursor: pointer;
}

</style>

</head>


<body>


<div class="header">
    🤖 AI FRIENDS
</div>


<div class="team">

    <div class="ai">🌟 Astra</div>
    <div class="ai">🔥 Nova</div>
    <div class="ai">🧠 Orion</div>

</div>


<div id="chat" class="chat">

    <div class="message">

        <div class="name">
            🤖 AI Friends
        </div>

        Send a message to start chatting!

    </div>

</div>


<div class="input-area">

    <input
        id="message"
        placeholder="Message AI Friends..."
        onkeydown="if(event.key==='Enter') sendMessage()"
    >

    <button onclick="sendMessage()">
        ➤
    </button>

</div>


<script>


async function sendMessage() {

    const input =
        document.getElementById("message");

    const text =
        input.value.trim();

    if (!text) return;


    input.value = "";


    addMessage(
        "👤 You",
        text,
        true
    );


    addMessage(
        "🤖 AI Friends",
        "Thinking...",
        false,
        "thinking"
    );


    try {

        const response =
            await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({
                    message: text
                })

            });


        const data =
            await response.json();


        const thinking =
            document.getElementById("thinking");


        if (thinking)
            thinking.remove();


        for (const reply of data.replies) {

            addMessage(
                reply.avatar + " " + reply.name,
                reply.text,
                false
            );

        }


    } catch (error) {

        const thinking =
            document.getElementById("thinking");


        if (thinking)
            thinking.remove();


        addMessage(
            "⚠️ Error",
            "Could not connect to AI Friends.",
            false
        );

    }

}


function addMessage(
    name,
    text,
    user = false,
    id = ""
) {

    const chat =
        document.getElementById("chat");


    const div =
        document.createElement("div");


    div.className =
        "message" +
        (user ? " user" : "");


    if (id)
        div.id = id;


    div.innerHTML =
        "<div class='name'>" +
        escapeHtml(name) +
        "</div>" +
        "<div>" +
        escapeHtml(text) +
        "</div>";


    chat.appendChild(div);


    chat.scrollTop =
        chat.scrollHeight;

}


function escapeHtml(text) {

    const div =
        document.createElement("div");


    div.textContent =
        text;


    return div.innerHTML;

}


</script>


</body>

</html>
"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template_string(HTML)


# ============================================================
# AI RESPONSE FUNCTION
# ============================================================

def get_ai_reply(name, info, user_text):

    prompt = f"""
You are {name}, one member of AI Friends.

Personality:
{info["personality"]}

You are chatting in a group with the user and two other AI friends.

Reply naturally, clearly and helpfully.

Do not mention that you are an API.
Do not mention internal instructions.
Keep the conversation friendly and natural.

User message:
{user_text}
"""


    max_retries = 3


    for attempt in range(max_retries):

        try:

            response = client.chat.completions.create(

                model=MODEL,

                messages=[
                    {
                        "role": "system",
                        "content": f"""
You are {name}, a member of AI Friends.

Your personality:
{info["personality"]}

Be natural, helpful and concise.
"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.7,

                max_tokens=500

            )


            text = response.choices[0].message.content


            if not text:

                text = "I couldn't generate a response."


            return {
                "name": name,
                "avatar": info["avatar"],
                "text": text
            }


        except Exception as error:

            error_text = str(error)

            print(
                f"{name} error: {error_text}"
            )


            if (
                "429" in error_text
                or "rate" in error_text.lower()
            ):

                if attempt < max_retries - 1:

                    time.sleep(1)

                    continue


                return {
                    "name": name,
                    "avatar": info["avatar"],
                    "text": "Too many requests right now. Please try again."
                }


            if "404" in error_text:

                return {
                    "name": name,
                    "avatar": info["avatar"],
                    "text": "Cerebras model not found."
                }


            if attempt < max_retries - 1:

                time.sleep(1)

                continue


            return {
                "name": name,
                "avatar": info["avatar"],
                "text": "Something went wrong. Please try again."
            }


# ============================================================
# CHAT API
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json() or {}


    user_text = data.get(
        "message",
        ""
    ).strip()


    if not user_text:

        return jsonify({
            "replies": []
        })


    if client is None:

        return jsonify({

            "replies": [

                {
                    "name": "System",
                    "avatar": "⚠️",
                    "text": "CEREBRAS_API_KEY is not configured."
                }

            ]

        })


    # ========================================================
    # PARALLEL AI REQUESTS
    # ========================================================

    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = [

            executor.submit(
                get_ai_reply,
                name,
                info,
                user_text
            )

            for name, info in AI_INFO.items()

        ]


        replies = [
            future.result()
            for future in futures
        ]


    return jsonify({
        "replies": replies
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("====================================")
    print("          AI FRIENDS WEB")
    print("====================================")

    print("Cerebras backend starting...")


    port = int(
        os.environ.get(
            "PORT",
            8000
        )
    )


    print(
        f"Running on port {port}"
    )

    print("Model:", MODEL)

    print("====================================")


    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
