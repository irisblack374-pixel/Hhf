<div align="center">

# 🤖 Hhf

### A modular Discord utility & moderation bot built with Python

<p>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/discord.py-2.x-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  <img src="https://img.shields.io/github/license/irisblack374-pixel/Hhf?style=for-the-badge" />
</p>

<p>
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-commands">Commands</a> •
  <a href="#-security">Security</a>
</p>

</div>

---

## 📌 Overview

**Hhf** is a Discord bot focused on everyday server management, moderation, utilities, and interactive tools.

The project is built with **Python + discord.py** and is designed around a simple environment-based configuration so the bot token stays outside the source code.

---

## ✨ Features

### 🛡️ Moderation
- 🧹 Message cleanup
- 👢 Kick members
- 🔨 Ban & unban members
- 🔒 Lock & unlock channels
- 🐢 Slowmode controls

### 🧰 Utilities
- 🏓 Bot ping / latency
- ⏱️ Uptime
- 👤 User information
- 🖼️ Avatar display
- 🏠 Server information

### 📢 Community Tools
- 📣 Embed announcements
- 💬 Say messages
- 📊 Reaction-based polls
- ❓ Help system

---

## 🧱 Tech Stack

| Technology | Purpose |
|---|---|
| 🐍 Python 3.11+ | Core language |
| 💬 discord.py | Discord API library |
| 🔐 python-dotenv | Environment configuration |
| ☁️ Procfile | Hosting/startup configuration |

---

## 📂 Project Structure

```text
Hhf/
├── bot.py
├── requirements.txt
├── Procfile
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚡ Installation

### 1. Clone the repository

```bash
git clone https://github.com/irisblack374-pixel/Hhf.git
cd Hhf
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file based on `.env.example`:

```env
DISCORD_TOKEN=YOUR_BOT_TOKEN
PREFIX=!
```

### 4. Start the bot

```bash
python bot.py
```

---

## 🔑 Discord Configuration

Depending on the commands enabled in the bot, you may need to enable the required intents in the Discord Developer Portal.

For member-related functionality, enable the corresponding **Server Members Intent**.  
For message-content based commands, enable **Message Content Intent**.

---

## 📋 Commands

### 📌 General

```text
!help
!ping
!server
!userinfo [@member]
!avatar [@member]
!uptime
```

### 🛡️ Moderation

```text
!clear <amount>
!kick @member [reason]
!ban @member [reason]
!unban <ID>
!lock
!unlock
!slowmode <seconds>
```

### 📢 Tools

```text
!say <message>
!announce <message>
!poll <question>
```

> Moderation commands require the appropriate Discord permissions.

---

## 🔐 Security

**Never commit your real Discord bot token.**

Use environment variables instead:

```env
DISCORD_TOKEN=YOUR_BOT_TOKEN
```

If a token is ever exposed, rotate it immediately through the Discord Developer Portal.

GitHub also recommends using repository security features such as secret scanning, push protection, and Dependabot where appropriate.

---

## 🗺️ Roadmap

- [ ] Expand moderation tools
- [ ] Add more utility commands
- [ ] Improve error handling
- [ ] Add automated tests
- [ ] Improve command documentation
- [ ] Add richer configuration options

---

## 🤝 Contributing

Suggestions and improvements are welcome.

Before submitting changes:

1. Keep the existing command behavior in mind.
2. Test the bot locally.
3. Never include secrets or tokens.
4. Keep documentation updated when commands change.

---

## 📄 License

© 2026 Hhf.

See the repository's license information before redistributing or using the project commercially.

---

<div align="center">

### 🚀 Built with Python & discord.py

**Hhf — simple tools for better Discord servers.**

</div>
