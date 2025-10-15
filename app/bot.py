import os
import sys
import logging
import traceback
import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rolebot")

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
WATCH_CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
ASSIGN_ROLE_ID = int(os.getenv("ROLE_ID", "0"))
LOGIN_CHANNEL_ID = int(os.getenv("LOGIN_CHANNEL_ID", "0"))
RULE_CHANNEL_ID = int(os.getenv("RULE_CHANNEL_ID", "0"))

# 設定の簡易チェック
if not TOKEN:
    logger.error("DISCORD_TOKEN is not set. Exiting.")
    sys.exit(1)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)

@bot.event
async def on_member_join(member):
    try:
        ch = bot.get_channel(LOGIN_CHANNEL_ID)
        if ch:
            await ch.send(f"✅ {member.display_name} joined. Send a message in <#{WATCH_CHANNEL_ID}> to get role.")
            await ch.send(
                f"""こんにちは、{member.mention} さん！\n
                サーバーへようこそ！\n
                <#{RULE_CHANNEL_ID}> を読んで <#{WATCH_CHANNEL_ID}> チャンネルでメッセージを送信してください。"""
            )
    except Exception:
        logger.exception("on_member_join error")

@bot.event
async def on_message(message):
    # debug print of every message (keep this to confirm channel ids)
    logger.info("Message from %s (id=%s) in channel %s (id=%s): %s",
                getattr(message.author, "display_name", message.author),
                message.author.id,
                getattr(message.channel, "name", str(message.channel)),
                message.channel.id,
                message.content)

    # ignore bots and DMs
    if message.author.bot or not message.guild:
        return

    # 重要: 確認用ログ
    if WATCH_CHANNEL_ID:
        if message.channel.id != WATCH_CHANNEL_ID:
            logger.debug("Message channel id %s != WATCH_CHANNEL_ID %s -> ignoring", message.channel.id, WATCH_CHANNEL_ID)
            return
    else:
        logger.warning("WATCH_CHANNEL_ID not set; ignoring messages")
        return

    # ロールを取得
    role = message.guild.get_role(ASSIGN_ROLE_ID)
    if role is None:
        logger.warning("Role with ID %s not found in guild %s. Available roles: %s",
                       ASSIGN_ROLE_ID, message.guild.id, [r.id for r in message.guild.roles])
        return

    member = message.author  # discord.Member

    # 既に持っているか？
    if role in member.roles:
        logger.info("Member %s already has role %s", member.display_name, role.name)
        return

    # 追加トライ
    try:
        logger.info("Attempting to add role %s to member %s", role.name, member.display_name)
        await member.add_roles(role, reason="Auto-assign on first message")
        await message.channel.send(f"{member.mention} さんにロール **{role.name}** を付与しました！")
        logger.info("Role added successfully")
    except discord.Forbidden:
        logger.exception("Forbidden: Bot lacks permissions or role position is too low. Bot role position must be above target role and it needs Manage Roles permission.")
        try:
            await message.channel.send("⚠️ Bot cannot assign roles (missing Manage Roles or role position). Please check bot permissions.")
        except Exception:
            pass
    except Exception:
        logger.exception("Failed to add role")

    # allow commands to be processed if you later add any commands
    await bot.process_commands(message)

# Run
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception:
        logger.exception("Fatal error in bot.run()")
        sys.exit(1)
