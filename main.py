import base64
from openai import OpenAI, BadRequestError
import telebot
from Token import *
from telebot.types import Message
import requests


client = OpenAI(api_key=CHATGPT_TOKEN)
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start", "help"])
def start_command(message):
    bot.send_message(message.from_user.id, "Hi")
    print(message.from_user)


@bot.message_handler(content_types=["text"])
def start_chatting(message: Message):
    if "$" == message.text[0]:
        mess = message.text.split()
        text_from_gpt = chatting(text=" ".join(mess[1:]))
        bot.send_message(message.from_user.id, text_from_gpt)
    if "&" == message.text[0]:
        mess = message.text.split()
        link_to_gpt, text_to_gpt = mess[1], " ".join(mess[2:])
        if text_to_gpt != "":
            answer_from_gpt = get_link(link_to_gpt, text_to_gpt)
        else:
            answer_from_gpt = get_link(link_to_gpt)
        bot.send_message(message.from_user.id, answer_from_gpt)
    if "*" == message.text[0]:
        mess = message.text.split()
        status, photo_from_gpt = generate_photo(question=" ".join(mess[1:]))
        if status:
            bot.send_photo(message.from_user.id, photo_from_gpt)
        else:
            bot.send_message(message.from_user.id, "Мне нельзя")
            bot.send_message(ID, f"{message.from_user.id} отправил - {mess}")


def chatting(text: str):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "общайся только зумерским сленгом, не юзай плохих слов"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content


def get_link(link, question="Прокомментируй"):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": link,
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content


@bot.message_handler(content_types=["photo"])
def start_photting(message: Message):
    img = bot.get_file(message.photo[-1].file_id)
    downloaded_img = bot.download_file(img.file_path)

    with open("1.png", "wb") as new_img:
        new_img.write(downloaded_img)
    if message.caption != "":
        answer = vision(message.caption)
    else:
        answer = vision()
    bot.send_message(message.from_user.id, answer)


def vision(question="Прокомментируй"):
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Path to your image
    image_path = "1.png"

    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {client.api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response.json().choices[0].message.content


def generate_photo(question):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=question,
            size="1024x1024",
            quality="hd",
            n=1,
        )
    except BadRequestError as error:
        return False, error
    else:
        return True, response.data[0].url


bot.infinity_polling(timeout=20, skip_pending=True)
