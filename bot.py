# -*- coding: utf8 -*-
import os
import email
import email.policy
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

intents = discord.Intents.default()
client = discord.Client(intents=intents)
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


def strip_ending(t, pattern):
    if t.endswith(pattern):
        t = t[: -len(pattern)]
    return t


def simple_format(msg):
    msg = msg.replace("\n>\n", "\n> \n")
    msg = strip_ending(msg, "\n>")
    return msg


async def chunkize(channel, msg):
    LIMIT = 2000
    for i in range(0, len(msg), LIMIT):
        await channel.send(msg[i : i + LIMIT])


async def idle_loop(host, port, user, password):
    """
    This will loop to get new emails and send them to "mail_channel_id"
    """
    imap_client = aioimaplib.IMAP4_SSL(host=host, port=port, timeout=30)
    await imap_client.wait_hello_from_server()
    await imap_client.login(user, password)
    await imap_client.select()
    await asyncio.sleep(5)

    while True:
        # only get emails which we haven't read
        mail_channel = client.get_channel(mail_channel_id)

        status, data = await imap_client.search("(ALL)")
        data = [d.decode() for d in data]
        for i in data[0].split():
            typ, mail = await imap_client.fetch(str(i), "(RFC822)")
            mail_msg = email.message_from_bytes(mail[1], policy=email.policy.SMTP)
            mail_channel = client.get_channel(mail_channel_id)

            msg_header = (
                f"**From:** {mail_msg['from']}\n"
                f"**Subject:** {mail_msg['subject']}\n"
                f"**To:** {mail_msg['to']}\n"
                f"**Date:** {mail_msg['date']}"
            )

            msg_body = []
            for part in mail_msg.walk():
                if part.get_content_type() == "text/plain":
                    message = "\n".join(
                        part.get_payload(decode=True).decode().splitlines()
                    )

                    message = get_text_selectolax(message).strip("\n")
                    message = simple_format(message)
                    msg_body.append(message)

                if part.get_content_maintype() == "multipart":
                    continue

                if part.get("Content-Disposition") is None:
                    continue

            msg = msg_header + "\n\n" + "\n".join(msg_body)
            await chunkize(mail_channel, msg)

        idle = await imap_client.idle_start(timeout=60)
        print((await imap_client.wait_server_push()))
        imap_client.idle_done()
        await asyncio.wait_for(idle, 30)


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


async def main():
    async with client:
        client.loop.create_task(
            idle_loop(imap_host[0], int(imap_host[1]), user, passwd)
        )
        await client.start(token)


asyncio.run(main())
