import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime


with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["token"]
PREFIX = config["prefix"]
DEFAULT_MESSAGE = config["default_message"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

required_keys = ["token", "prefix"]
for key in required_keys:
    if key not in config or not config[key].strip():
        raise ValueError(f"Missing or empty config key: {key}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print(f"👑 xrszav: Type {PREFIX}help for commands.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: `{error.param.name}`")
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("⚠️ I’m missing permissions to do that.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You failed a check to run this command.")
    else:
        await ctx.send("❗ An unexpected error occurred. Check console for more info.")
        raise error 
    
@bot.command(name='dm')
@commands.has_permissions(administrator=True)
async def dm(ctx, member: discord.Member, *, custom_message=None):
    message = custom_message or DEFAULT_MESSAGE
    if not message.strip():
        await ctx.send("❌ No default message set | ❌ No message was sent. Please provide a message.")
        return
    
    if member.bot:
        await ctx.send("❌ You cannot DM bots.")
        return
    
    try:
        await member.send(message)
        await ctx.send(f"✅ DM sent to {member.name}")
    except Exception as e:
        await ctx.send(f"❌ Failed to DM {member.name}: {e}")

@bot.command(name='dmall', aliases=['massdm', 'dmallusers'])
@commands.has_permissions(administrator=True)
async def dmall(ctx, *, custom_message=None):
    members = [m for m in ctx.guild.members if not m.bot]
    total = len(members)
    if total == 0:
        await ctx.send("❌ No valid users to DM.")
        return

    message = custom_message or DEFAULT_MESSAGE
    if not message.strip():
        await ctx.send("❌ No default message set | ❌ No message was sent. Please provide a message.")
        return

    sent = 0
    failed = 0
    report_every = max(1, total // 100)
    pause_every = 20
    cooldown_duration = 300

    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")

    log_file_success = f"dm_success_{timestamp}.txt"
    log_file_failed = f"dm_failed_{timestamp}.txt"

    with open(log_file_success, "w", encoding="utf-8") as f:
        f.write("✅ DMed Users:\n")
    with open(log_file_failed, "w", encoding="utf-8") as f:
        f.write("❌ Failed DMs:\n")

    await ctx.send(
        f"📤 Starting to DM {total} users...\n"
        f"⏱ Progress every {report_every} users, cooldown every {pause_every} users.\n"
        f"📝 Success log: `{log_file_success}`\n"
        f"🛑 Failed log: `{log_file_failed}`"
    )

    for idx, member in enumerate(members, start=1):
        try:
            await member.send(message)
            sent += 1
            with open(log_file_success, "a", encoding="utf-8") as f:
                f.write(f"{member.name}#{member.discriminator} | {member.id}\n")
        except Exception as e:
            failed += 1
            print(f"❌ Failed to DM {member.name}: {e}")
            with open(log_file_failed, "a", encoding="utf-8") as f:
                f.write(f"{member.name}#{member.discriminator} | {member.id} | Error: {e}\n")

        if idx % report_every == 0:
            embed = discord.Embed(
                title="📬 DM Progress Update",
                description=f"Progress: **{idx}/{total}** users",
                color=discord.Color.blurple()
            )
            embed.add_field(name="✅ Sent", value=str(sent))
            embed.add_field(name="❌ Failed", value=str(failed))
            await ctx.send(embed=embed)

        if idx % pause_every == 0:
            await ctx.send(f"🕒 Cooling down for 5 minutes after {idx} users...")
            await asyncio.sleep(cooldown_duration)

        await asyncio.sleep(1)

    final_embed = discord.Embed(
        title="✅ DM Campaign Completed",
        description=f"All **{total}** users processed.",
        color=discord.Color.green()
    )
    final_embed.add_field(name="✅ Total Sent", value=str(sent), inline=True)
    final_embed.add_field(name="❌ Total Failed", value=str(failed), inline=True)
    final_embed.add_field(name="📄 Logs", value=f"Success: `{log_file_success}`\nFailed: `{log_file_failed}`", inline=False)
    await ctx.send(embed=final_embed)

@dmall.error
async def dmall_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need administrator permissions to use this command.")
    else:
        await ctx.send(f"❌ Error: {error}")

@bot.command(name='dmstatus')
@commands.has_permissions(administrator=True)
async def dmstatus(ctx):
    success_files = [f for f in os.listdir() if f.startswith("dm_success_")]
    failed_files = [f for f in os.listdir() if f.startswith("dm_failed_")]

    if not success_files and not failed_files:
        await ctx.send("❌ No DM log files found. Please run a DM campaign first.")
        return

    success_files.sort(reverse=True)
    failed_files.sort(reverse=True)

    latest_success_file = success_files[0] if success_files else None
    latest_failed_file = failed_files[0] if failed_files else None

    total_sent = 0
    total_failed = 0

    if latest_success_file:
        try:
            with open(latest_success_file, "r", encoding="utf-8") as f:
                success_lines = f.readlines()
            total_sent = len(success_lines) - 1
        except Exception as e:
            await ctx.send(f"❌ Error reading the success log: {e}")

    if latest_failed_file:
        try:
            with open(latest_failed_file, "r", encoding="utf-8") as f:
                failed_lines = f.readlines()
            total_failed = len(failed_lines) - 1
        except Exception as e:
            await ctx.send(f"❌ Error reading the failed log: {e}")

    total_users = total_sent + total_failed

    status_embed = discord.Embed(
        title="📊 DM Status",
        description="Current status of the DM campaign.",
        color=discord.Color.blue()
    )
    status_embed.add_field(name="Total Users", value=str(total_users), inline=True)
    status_embed.add_field(name="✅ Successful DMs", value=str(total_sent), inline=True)
    status_embed.add_field(name="❌ Failed DMs", value=str(total_failed), inline=True)
    status_embed.add_field(name="📝 Success Log", value=f"`{latest_success_file}`" if latest_success_file else "N/A", inline=False)
    status_embed.add_field(name="🛑 Failed Log", value=f"`{latest_failed_file}`" if latest_failed_file else "N/A", inline=False)

    await ctx.send(embed=status_embed)

@bot.command(name='dmretry', aliases=['dmallcontinue', 'retrydm', 'dmfailures'])
@commands.has_permissions(administrator=True)
async def dmallcontinue(ctx, *, filepath=None):
    if not filepath:
        await ctx.send("❌ Please provide the path to the success log file. Example: `!dmallcontinue dm_success_01042025_153000.txt`")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        await ctx.send(f"❌ File `{filepath}` not found.")
        return

    successful_ids = set()
    for line in lines:
        if "|" in line:
            parts = line.strip().split("|")
            if len(parts) >= 2:
                try:
                    user_id = int(parts[1].strip())
                    successful_ids.add(user_id)
                except ValueError:
                    continue

    members = [m for m in ctx.guild.members if not m.bot and m.id not in successful_ids]
    total = len(members)

    if total == 0:
        await ctx.send("❌ All users in the server have already been DM'd.")
        return

    message = DEFAULT_MESSAGE
    sent = 0
    failed = 0
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    retry_log_success = f"dm_retry_success_{timestamp}.txt"
    retry_log_failed = f"dm_retry_failed_{timestamp}.txt"

    with open(retry_log_success, "w", encoding="utf-8") as f:
        f.write("✅ Retried & DMed Users:\n")
    with open(retry_log_failed, "w", encoding="utf-8") as f:
        f.write("❌ Retried & Failed DMs:\n")

    await ctx.send(
        f"🔁 Retrying DM for {total} users from `{filepath}`...\n"
        f"📝 Retry success log: `{retry_log_success}`\n"
        f"🛑 Retry failed log: `{retry_log_failed}`"
    )

    for idx, member in enumerate(members, start=1):
        try:
            await member.send(message)
            sent += 1
            with open(retry_log_success, "a", encoding="utf-8") as f:
                f.write(f"{member.name}#{member.discriminator} | {member.id}\n")
        except Exception as e:
            failed += 1
            print(f"❌ Retry failed to DM {member.name}: {e}")
            with open(retry_log_failed, "a", encoding="utf-8") as f:
                f.write(f"{member.name}#{member.discriminator} | {member.id} | Error: {e}\n")

        await asyncio.sleep(1)

    final_embed = discord.Embed(
        title="🔁 DM Retry Completed",
        description=f"Retried DM for **{total}** users.",
        color=discord.Color.orange()
    )
    final_embed.add_field(name="✅ Retried & Sent", value=str(sent), inline=True)
    final_embed.add_field(name="❌ Retried & Failed", value=str(failed), inline=True)
    final_embed.add_field(name="📄 Logs", value=f"Success: `{retry_log_success}`\nFailed: `{retry_log_failed}`", inline=False)
    await ctx.send(embed=final_embed)

bot.run(TOKEN)
