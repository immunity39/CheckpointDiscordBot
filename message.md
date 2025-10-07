最高っす、その要件なら “ロール未付与ユーザーが指定チャンネルに書き込んだら自動でロール付与” を軸に、Koyeb 常時稼働 & GitHub 連携まで一気通しで作れます。以下、最短コースの設計 → 実装 → デプロイ手順です。参考リンクは要点に絞って付けました。

全体設計（最小構成）

監視チャンネル（例: #入室手続き）に最初の書き込みをしたユーザーへ、指定ロール（例: 新規メンバー）を自動付与

参加/退出ログを入退室表示チャンネルへ通知

ルール表記チャンネルは閲覧専用（Bot は書かない）

Bot 権限: Manage Roles とメッセージ読み取り（Message Content Intent）。ロール階層で Bot の最高位ロールを付与対象より上に配置が必須。
Discord

Intents（メンバー/メッセージコンテンツ）は Developer Portal で有効化（未認証の少人数 Bot なら自前で OK）。
Discord
+3
support-dev.discord.com
+3
discordpy.readthedocs.io
+3

リポジトリ構成（Python / discord.py）
discord-role-on-post/
├─ bot.py
├─ requirements.txt
├─ Dockerfile
└─ README.md

requirements.txt
discord.py==2.4.0

bot.py（コピペで動く最小例）
import os
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0")) # サーバ ID
WATCH_CHANNEL_ID = int(os.getenv("WATCH_CHANNEL_ID", "0")) # 監視チャンネル ID（書き込み可チャンネル）
ASSIGN_ROLE_ID = int(os.getenv("ASSIGN_ROLE_ID", "0")) # 付与するロール ID
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0")) # 入退室表示チャンネル ID

intents = discord.Intents.default()

# 権限: メンバー一覧・メッセージ内容・メンバーイベント

intents.members = True
intents.message_content = True
intents.guilds = True

class MyClient(discord.Client):
def **init**(self):
super().**init**(intents=intents)
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
async def on_member_join(member: discord.Member): # 参加通知
try:
ch = client.get_channel(LOG_CHANNEL_ID)
if ch:
await ch.send(f"✅ **{member.display_name}** さんが参加しました。ようこそ！")
except Exception as e:
print(f"on_member_join error: {e}")

@client.event
async def on_member_remove(member: discord.Member): # 退出通知
try:
ch = client.get_channel(LOG_CHANNEL_ID)
if ch:
await ch.send(f"👋 **{member.display_name}** さんが退出しました。")
except Exception as e:
print(f"on_member_remove error: {e}")

@client.event
async def on_message(message: discord.Message): # Bot 自身や DM は無視
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

参考: discord.py の Intents/権限まわりの公式ドキュメントと Developer Portal の権限仕様。
Discord
+3
discordpy.readthedocs.io
+3
discordpy.readthedocs.io
+3

Dockerfile（Koyeb 想定・Buildpack でも可）
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# 健康チェック（任意）

# HEALTHCHECK CMD python -c "import socket; print('ok')" || exit 1

CMD ["python", "bot.py"]

Discord 側の設定ポイント（重要）

Developer Portal → Bot

Privileged Gateway Intents:

✅ MESSAGE CONTENT INTENT（on_message で本文を見るため）

✅ SERVER MEMBERS INTENT（メンバー/ロール操作）

必要なら ✅ PRESENCE INTENT（今回は不要）

Bot Permissions: Manage Roles, Read Messages/View Channels, Send Messages など

サーバのロール階層

Bot の最高位ロール > 付与対象ロールでないと add_roles が失敗。
Discord

必要な ID を取得して .env or Koyeb 環境変数へ

GUILD_ID, WATCH_CHANNEL_ID, ASSIGN_ROLE_ID, LOG_CHANNEL_ID, DISCORD_TOKEN

GitHub 連携 & Koyeb 常時稼働

A. GitHub リポジトリ作成（チーム開発）

上記ファイルを push（必要なら README.md に運用ルールを記載）

main / develop ブランチ運用や PR テンプレを用意すると ◎

B. Koyeb でデプロイ

Koyeb ダッシュボード → Create App → GitHub リポジトリを選択（Koyeb は GitHub からのデプロイを標準サポート）
Koyeb

Builder は自動検出（Dockerfile があれば Docker ビルド、無ければ Buildpack）

Environment variables に以下を登録：

DISCORD_TOKEN, GUILD_ID, WATCH_CHANNEL_ID, ASSIGN_ROLE_ID, LOG_CHANNEL_ID
（.env を GitHub に置かない。Koyeb 側で安全に管理できます）
Koyeb Community

リージョン/インスタンスは最小で OK → Deploy

公式コミュニティに Discord Bot のチュートリアルやトラブルシュートもあり（ログで“no active deployment”等が出た時はビルドログを確認）
Koyeb Community
+1

GitHub を使わず CLI 直デプロイも可能ですが、チーム開発なら GitHub 連携が分かりやすいです。
Koyeb Community

動作確認チェックリスト

Bot をサーバに招待（スコープ: bot, applications.commands / 権限に Manage Roles）

監視チャンネルで、ロール未付与のテスト用アカウントが書き込む

Bot がメッセージを検知 → 付与完了メッセージ → ユーザーにロールが付く

参加/退出時にログチャンネルへ通知

Koyeb のログでエラーなし（on_ready の出力が出ていれば OK）

拡張アイデア（後から足せる）

一度付与済みならスルー/注意書き返信の切替

質問フォーム → 反応でロール分岐（リアクション/ボタン）

ルール同意コマンド /agree で付与（Message Content intent なしでも実装可能）

監視対象を複数チャンネルにする

付与ロールを環境変数で複数指定し、条件に応じて切替

必要なら、TypeScript（discord.js）版や、GitHub Actions での lint/test、Koyeb のリビルド戦略もすぐ用意します。上の Python 版をまず動かしてみて、ID と権限だけしっかり合わせれば、そのまま本番運用できます。
