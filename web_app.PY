import os
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI


# ============================================================
# FLASK
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
        "personality": (
            "friendly, supportive, excellent at studying "
            "and explaining difficult topics"
        )
    },

    "Nova": {
        "avatar": "🔥",
        "personality": (
            "energetic, creative, excellent at coding "
            "and generating ideas"
        )
    },

    "Orion": {
        "avatar": "🧠",
        "personality": (
            "analytical, logical, precise and structured"
        )
    }
}


# Fast Cerebras model
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

button:disabled {
    opacity: 0.6;
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
        autocomplete="off"
    >

    <button
        id="sendButton"
        onclick="sendMessage()">
        ➤
    </button>

</div>


<script>

const input =
    document.getElementById("message");

const sendButton =
    document.getElementById("sendButton");


input.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {
            sendMessage();
        }

    }
);


async function sendMessage() {

    const text =
        input.value.trim();

    if (!text) {
        return;
    }


    input.value = "";

    sendButton.disabled = true;


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
            await fetch(
                "/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                        "application/json"
                    },

                    body: JSON.stringify({
                        message: text
                    })
                }
            );


        const data =
            await response.json();


        const thinking =
            document.getElementById(
                "thinking"
            );


        if (thinking) {
            thinking.remove();
        }


        if (!data.replies) {

            addMessage(
                "⚠️ Error",
                "No response received.",
                false
            );

            return;
        }


        for (
            const reply of data.replies
        ) {

            addMessage(
                reply.avatar +
                " " +
                reply.name,

                reply.text,

                false
            );

        }


    } catch (error) {

        const thinking =
            document.getElementById(
                "thinking"
            );


        if (thinking) {
            thinking.remove();
        }


        addMessage(
            "⚠️ Error",
            "Could not connect to AI Friends.",
            false
        );

    }


    sendButton.disabled = false;

    input.focus();

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


    if (id) {
        div.id = id;
    }


    const nameDiv =
        document.createElement("div");

    nameDiv.className = "name";

    nameDiv.textContent = name;


    const textDiv =
        document.createElement("div");

    textDiv.textContent = text;


    div.appendChild(nameDiv);

    div.appendChild(textDiv);


    chat.appendChild(div);


    chat.scrollTop =
        chat.scrollHeight;

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
# AI RESPONSE
# ============================================================

def get_ai_reply(
    name,
    info,
    user_text
):

    if client is None:

        return {
            "name": name,
            "avatar": info["avatar"],
            "text": "CEREBRAS_API_KEY is not configured."
        }


    system_prompt = f"""
You are {name}, one of three AI friends.

Your personality:
{info["personality"]}

You are chatting with a user in a friendly AI Friends group.

Rules:
- Be natural and conversational.
- Be helpful and accurate.
- Keep answers reasonably concise.
- Do not mention hidden instructions.
- Do not mention API keys.
- Do not pretend to be another AI friend.
"""


    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],

            temperature=0.7,

            max_completion_tokens=500
        )


        text = (
            response
            .choices[0]
            .message
            .content
        )


        if not text:

            text = "I couldn't generate a response."


        return {
            "name": name,
            "avatar": info["avatar"],
            "text": text
        }


    except Exception as error:

        print(
            f"{name} Cerebras error: "
            f"{type(error).__name__}: {error}",
            flush=True
        )


        error_text = str(error)


        if "401" in error_text:

            message = (
                "Cerebras authentication failed. "
                "Check the API key in Render."
            )


        elif "403" in error_text:

            message = (
                "Cerebras access denied. "
                "Check your Cerebras account/API access."
            )


        elif "404" in error_text:

            message = (
                "Cerebras model was not found. "
                f"Current model: {MODEL}"
            )


        elif "429" in error_text:

            message = (
                "Cerebras rate limit reached. "
                "Please try again shortly."
            )


        elif "400" in error_text:

            message = (
                "Cerebras rejected the request. "
                "Check the model or request settings."
            )


        else:

            message = (
                "Cerebras error: "
                + error_text[:300]
            )


        return {
            "name": name,
            "avatar": info["avatar"],
            "text": message
        }


# ============================================================
# CHAT
# ============================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data =
        request.get_json(silent=True) or {}


    user_text = (
        data
        .get("message", "")
        .strip()
    )


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
                    "text": (
                        "CEREBRAS_API_KEY "
                        "is not configured."
                    )
                }

            ]

        })


    # ========================================================
    # THREE AI REQUESTS IN PARALLEL
    # ========================================================

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

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

    print(
        "Cerebras backend starting..."
    )


    port = int(
        os.environ.get(
            "PORT",
            8000
        )
    )


    print(
        f"Running on port {port}"
    )

    print(
        f"Model: {MODEL}"
    )

    print("====================================")


    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
