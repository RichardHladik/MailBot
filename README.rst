.. image:: https://img.shields.io/badge/mailbot-1.0.0-pink
    :alt: mailbot

.. image:: https://img.shields.io/pypi/pyversions/discord-py.svg
    :target: https://pypi.python.org/pypi/discord.py
    :alt: python

.. image:: https://img.shields.io/badge/aioimaplib-0.7.18-green
    :target: https://pypi.org/project/aioimaplib/
    :alt: aioimaplib

.. image:: https://img.shields.io/badge/aiosmtplib-1.1.3-red
    :target: https://pypi.org/project/aiosmtplib/
    :alt: aiosmtplib

.. image:: https://img.shields.io/github/license/0xCN/MailBot?color=gr
    :target: https://github.com/0xCN/MailBot/blob/master/LICENSE
    :alt: licence



===================
MailBot
===================

    .. image:: /attachments/help.png


``MailBot`` is a discord bot which forwards new emails to your discord server. This is a fork of [0xCN/MailBot](https://github.com/0xCN/MailBot) that deliberately doesn't support sending email.


Installation
============

Requirements:
-------------

    1. **discord.py**
    2. **aioimaplib**
    3. **aiosmtplib**
    4. **selectolax**


Installation:
-------------

::

    $ pip install -r requirements.txt



Config:
--------------------------

In your ``config.py``:

.. code:: python

    # Bot Command Prefix
    pre = 'm!'
    # Discord Channel IDs
    mail_channel_id = 739137691681030197 
    # host:port
    imap_host = 'imap.gmail.com:993'
    # AUTH for imap
    user = 'test@gmail.com'
    passwd = 'password123@'
    # Discord Bot Token
    token = 'NzM3NzU5NjI1NTE2MTU1MDEw............'
