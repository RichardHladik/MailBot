import os
import email
import discord
import asyncio
from aioimaplib import aioimaplib
from selectolax.parser import HTMLParser
from config import (
    imap_host,
    user,
    passwd,
    mail_channel_id,
    token,
)

client = discord.Client()
imap_host = imap_host.split(":")


def get_text_selectolax(html):
    """
    parsing HTML from email and returning crucial parts as TEXT
    """
    tree = HTMLParser(html)
    if tree.body is None:
        return None
    for tag in tree.css("script"):
        tag.decompose()
    for tag in tree.css("style"):
        tag.decompose()
    text = tree.body.text(separator="\n")
    return text


@asyncio.coroutine
async def idle_loop(host, port, user, password):
    """
    This will loop to get new emails and send them to "mail_channel_id"
    """
    imap_client = aioimaplib.IMAP4_SSL(host=host, port=port, timeout=30)
    await imap_client.wait_hello_from_server()
    await imap_client.login(user, password)
    await imap_client.select()

    while True:
        # only get emails which we haven't read
        status, data = await imap_client.search("(UNSEEN)")
        for i in data[0].split():
            typ, mail = await imap_client.fetch(i, "(RFC822)")
            mail_msg = email.message_from_bytes(mail[1], policy=email.policy.SMTP)
            mail_channel = client.get_channel(mail_channel_id)

            # sending the email as a discord message
            await mail_channel.send(
                "```\n------------START-OF-MAIL-----------```"
                f"```ini\n[From]: {mail_msg['from']}\n"
                f"[Subject]: {mail_msg['subject']}\n"
                f"[To]: {mail_msg['to']}\n"
                f"[Date]: {mail_msg['date']}\n```"
            )

            for part in mail_msg.walk():
                if part.get_content_type() == "text/plain":
                    message = ""
                    for line in part.get_content().splitlines():
                        message += line + "\n"

                    message = get_text_selectolax(message.rstrip("\n"))
                    # removing unicode character representations
                    # not best practice, but works.
                    message = "".join(i for i in message if ord(i) < 128)
                    d_msg_len = 1992
                    # cutting the email content so it-
                    # doesn't reach discords message char limit
                    for i in range(0, len(message), d_msg_len):
                        msg_ = message[i : i + d_msg_len] + "-"
                        await mail_channel.send(f"```\n{msg_}```")

                if part.get_content_maintype() == "multipart":
                    continue

                if part.get("Content-Disposition") is None:
                    continue

                file_name = part.get_filename()
                file_raw = part.get_payload(decode=True)

                if bool(file_name):
                    file_path = os.path.join(f"{os.getcwd()}/attachments/", file_name)

                    if not os.path.isfile(file_path):
                        with open(file_path, "wb") as fp:
                            fp.write(file_raw)

                    # won't send files that's bigger than 8mb
                    if len(file_raw) <= 8000000:
                        await mail_channel.send(
                            f"`{file_name}`", file=discord.File(file_path)
                        )
                    else:
                        await mail_channel.send(f"{file_name} file too big")
                    os.system("rm -r attachments/*")
            await mail_channel.send("```\n-------------END-OF-MAIL------------```")

        idle = await imap_client.idle_start(timeout=60)
        print((await imap_client.wait_server_push()))
        imap_client.idle_done()
        await asyncio.wait_for(idle, 30)


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


client.loop.create_task(idle_loop(imap_host[0], int(imap_host[1]), user, passwd))
client.run(token)
