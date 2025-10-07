import os
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))              # サーバID
WATCH_CHANNEL_ID = int(os.getenv("WATCH_CHANNEL_ID", "0"))  # 監視チャンネルID（書き込み可チャンネル）
ASSIGN_ROLE_ID = int(os.getenv("ASSIGN_ROLE_ID", "0"))      # 付与するロールID
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))      # 入退室表示チャンネルID

intents = discord.Intents.default()
# 権限: メンバー一覧・メッセージ内容・メンバーイベント
intents.members = True
intents.message_content = True
intents.guilds = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

client = MyClient()

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

@client.event
async def on_member_join(member: discord.Member):
    # 参加通知
    try:
        ch = client.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(f"✅ **{member.display_name}** さんが参加しました。ようこそ！")
    except Exception as e:
        print(f"on_member_join error: {e}")

@client.event
async def on_member_remove(member: discord.Member):
    # 退出通知
    try:
        ch = client.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(f"👋 **{member.display_name}** さんが退出しました。")
    except Exception as e:
        print(f"on_member_remove error: {e}")

@client.event
async def on_message(message: discord.Message):
    # Bot自身やDMは無視
    if message.author.bot or not message.guild:
        return
    if message.channel.id != WATCH_CHANNEL_ID:
        return

    # すでに対象ロールを持っていたら何もしない
    role = message.guild.get_role(ASSIGN_ROLE_ID)
    if role is None:
        return  # ロール未発見（IDミスなど）

    member: discord.Member = message.author

    # 「@everyone のみ」or 「対象ロール未所持」を基準に付与（片方で十分なら条件を簡略化OK）
    has_target = role in member.roles
    if not has_target:
        try:
            # 付与はBotの最高位ロール>対象ロール でないと失敗します（サーバ設定必須）
            await member.add_roles(role, reason="初回書き込み検知による自動ロール付与")
            await message.channel.send(f"{member.mention} さんにロール **{role.name}** を付与しました！")
        except discord.Forbidden:
            await message.channel.send("⚠️ 権限不足でロールを付与できません。Botのロール位置や権限（Manage Roles）を確認してください。")
        except Exception as e:
            await message.channel.send(f"⚠️ ロール付与時にエラーが発生しました: {e}")
