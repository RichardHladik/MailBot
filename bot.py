import os
import email
import discord
import asyncio
import aiosmtplib
from aioimaplib import aioimaplib
from selectolax.parser import HTMLParser
from config import (
    imap_host, smtp_host, user, passwd, mail_channel_id,
    send_channel_id, from_mail, token, pre
)

client = discord.Client()
imap_host = imap_host.split(':')
smtp_host = smtp_host.split(':')


def get_text_selectolax(html):
    """
    parsing HTML from email and returning crucial parts as TEXT
    """
    tree = HTMLParser(html)
    if tree.body is None:
        return None
    for tag in tree.css('script'):
        tag.decompose()
    for tag in tree.css('style'):
        tag.decompose()
    text = tree.body.text(separator='\n')
    return text


async def send_mail(from_, to, subject, content, reply_to=None):
    message = email.message.EmailMessage()
    message["From"] = from_
    message["To"] = to
    message["Subject"] = subject
    message.set_content(content)

    if reply_to:
        message['reply-to'] = reply_to

    await aiosmtplib.send(
        message,
        hostname=smtp_host[0],
        port=smtp_host[1],
        username=user,
        password=passwd,
        use_tls=True
    )


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
        status, data = await imap_client.search('(UNSEEN)')
        for i in data[0].split():
            typ, mail = await imap_client.fetch(i, '(RFC822)')
            mail_msg = email.message_from_bytes(
                mail[1],
                policy=email.policy.SMTP
            )
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
                    message = ''
                    for line in part.get_content().splitlines():
                        message += line + '\n'

                    message = get_text_selectolax(message.rstrip('\n'))
                    # removing unicode character representations
                    # not best practice, but works.
                    message = ''.join(i for i in message if ord(i) < 128)
                    d_msg_len = 1992
                    # cutting the email content so it-
                    # doesn't reach discords message char limit
                    for i in range(0, len(message), d_msg_len):
                        msg_ = message[i:i+d_msg_len]+'-'
                        await mail_channel.send(f'```\n{msg_}```')

                if part.get_content_maintype() == 'multipart':
                    continue

                if part.get('Content-Disposition') is None:
                    continue

                file_name = part.get_filename()
                file_raw = part.get_payload(decode=True)

                if bool(file_name):
                    file_path = os.path.join(
                        f'{os.getcwd()}/attachments/',
                        file_name)

                    if not os.path.isfile(file_path):
                        with open(file_path, 'wb') as fp:
                            fp.write(file_raw)

                    # won't send files that's bigger than 8mb
                    if len(file_raw) <= 8000000:
                        await mail_channel.send(
                            f'`{file_name}`',
                            file=discord.File(file_path))
                    else:
                        await mail_channel.send(f'{file_name} file too big')
                    os.system('rm -r attachments/*')
            await mail_channel.send(
                "```\n-------------END-OF-MAIL------------```"
            )

        idle = await imap_client.idle_start(timeout=60)
        print((await imap_client.wait_server_push()))
        imap_client.idle_done()
        await asyncio.wait_for(idle, 30)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(f'{pre}ping'):
        await message.channel.send('pong')

    if message.channel.id == send_channel_id:
        # all the commands below will only be available-
        # in the "send_channel_id" discord channel
        if message.content.startswith(f'{pre}help'):
            await message.channel.send(
                "```ini\n[MailBot] - v1.0.0```"
                f"`{pre}help` - `show this help message`\n"
                f'`{pre}send` example@email.com "subject" \\`\\`\\`content'
                '\\`\\`\\` - `send an email`\n'
                f'`{pre}reply` 740042707807895642 \\`\\`\\`content\\`\\`\\` -'
                ' `reply to an email`\n'
                f'[note]: `{pre}reply message_id` of a message in the '
                '`mail_text_channel`\n'
                '```ini\n[commands only work in send_text_channel]```'
            )

        if message.content.startswith(f'{pre}send'):
            params = message.content.split(' ')
            try:
                to = message.content.split(' ')[1]
                subject = message.content.split('"')[1]
                content = message.content.split('```')[1]
                await send_mail(from_mail, to, subject, content)
                await message.channel.send(
                    f"```ini\n[From]: {from_mail}\n"
                    f"[Subject]: {subject}\n"
                    f"[To]: {to}\n```"
                    f'```\nsent email```'
                )

            except Exception as e:
                print(e)
                await message.channel.send('```\nError```')

        if message.content.startswith(f'{pre}reply'):
            mail_channel = client.get_channel(mail_channel_id)
            params = message.content.split(' ')
            try:
                # parsing info from the discord message id-
                # and replying to the email
                msg = await mail_channel.fetch_message(int(params[1]))
                msg = msg.content.split('\n')

                content = ' '.join(params[2:])[3:-3]
                to = msg[2][8:]
                subject = msg[3][11:]
                if 'Sent-To' in msg[4]:
                    to = msg[4][11:]
                if 'Re: ' not in msg[3][11:]:
                    subject = 'Re: ' + subject

                await send_mail(from_mail, to, subject, content, to)
                await message.channel.send(
                    f"```ini\n[From]: {from_mail}\n"
                    f"[Subject]: {subject}\n"
                    f"[To]: {to}\n```"
                    f'```\nreplied to email```'
                )

            except Exception as e:
                print(e)
                await message.channel.send('```\nError```')


client.loop.create_task(idle_loop(
    imap_host[0],
    int(imap_host[1]),
    user,
    passwd)
)
client.run(token)
