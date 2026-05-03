import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime, timedelta


with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["token"]
PREFIX = config["prefix"]
DEFAULT_MESSAGE = config["default_message"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

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
    
@bot.command(name='help', aliases=['commands'], description="Show all available commands or details about a specific command")
async def custom_help(ctx, *, command_name: str = None):
    """Show all available commands or details about a specific command"""
    if command_name:
        # Show help for a specific command
        command = bot.get_command(command_name.lower())
        if not command:
            return await ctx.send(f"❌ Command `{command_name}` not found. Use `{PREFIX}help` to see all commands.")
        
        embed = discord.Embed(
            title=f"ℹ️ {command.name.capitalize()} Command Help",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Description",
            value=command.help or "No description available",
            inline=False
        )
        
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False
            )
        
        embed.add_field(
            name="Usage",
            value=f"`{PREFIX}{command.name} {command.signature}`" if command.signature else f"`{PREFIX}{command.name}`",
            inline=False
        )
        
        return await ctx.send(embed=embed)
    
    # Show general help menu
    embed = discord.Embed(
        title="📚 DM Bot Help Menu",
        description=f"Use `{PREFIX}help <command>` for more info on a specific command",
        color=discord.Color.blue()
    )
    
    # DM Commands
    dm_commands = [
        ("dm", "Send a DM to a specific user"),
        ("dmpreview", ":new: Preview a DM by sending it to yourself"),
        ("dmall", "Mass DM all server members"),
        ("dmallsafe", ":new: Slow, safer mass DM all server members"),
        ("dmroleall", "DM all members with a specific role"),
        ("dmroleallsafe", ":new: Slow, safer DM all members with a role"),
        ("dmretry", "Retry failed DMs from a previous campaign")
    ]
    embed.add_field(
        name="📨 DM Commands",
        value="\n".join(f"• `{cmd[0]}` - {cmd[1]}" for cmd in dm_commands),
        inline=False
    )
    
    # Log Management
    log_commands = [
        ("getlog", "Download DM log files"),
        ("dmstatus", "Show status of last DM campaign"),
        ("dmstats", "Show DM statistics"),
        ("clearlogs", "Delete old log files")
    ]
    embed.add_field(
        name="📂 Log Management",
        value="\n".join(f"• `{cmd[0]}` - {cmd[1]}" for cmd in log_commands),
        inline=False
    )
    
    # Additional Info
    embed.add_field(
        name="ℹ️ Additional Information",
        value=(
            f"• Prefix: `{PREFIX}`\n"
            "• All commands require administrator permissions\n"
            "• The bot automatically creates logs for all DM campaigns"
        ),
        inline=False
    )

    embed.set_footer(text="xrszav's DM Bot | https://oblivity.xyz | https://xrszav.xyz")
    await ctx.send(embed=embed)

@bot.command(name='dm', description="Send a DM to a specific user")
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

@bot.command(name='dmpreview', aliases=['previewdm'], description="Preview a DM by sending it to yourself")
@commands.has_permissions(administrator=True)
async def dmpreview(ctx, *, custom_message=None):
    message = custom_message or DEFAULT_MESSAGE
    if not message.strip():
        await ctx.send("❌ No default message set | ❌ No message was sent. Please provide a message.")
        return

    try:
        await ctx.author.send(message)
        await ctx.send(f"✅ Preview DM sent to {ctx.author.name}.")
    except Exception as e:
        await ctx.send(f"❌ Failed to send preview DM: {e}")

@bot.command(name='dmall', aliases=['massdm', 'dmallusers'], description="Mass DM all server members")
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

@bot.command(name='dmallsafe', aliases=['massdmsafe', 'slowdmall'], description="Slow, safer mass DM all server members")
@commands.has_permissions(administrator=True)
async def dmall_safe(ctx, *, custom_message=None):
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
    short_delay = 4
    medium_pause_every = 15
    medium_pause = 90
    long_pause_every = 40
    long_pause = 240
    extra_pause_every = 100
    extra_pause = 480

    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    log_file_success = f"dm_success_slow_{timestamp}.txt"
    log_file_failed = f"dm_failed_slow_{timestamp}.txt"

    with open(log_file_success, "w", encoding="utf-8") as f:
        f.write("✅ Slowly DMed Users:\n")
    with open(log_file_failed, "w", encoding="utf-8") as f:
        f.write("❌ Slowly Failed DMs:\n")

    await ctx.send(
        f"🐢 Starting safe slow DM of {total} users...\n"
        f"⏱ Progress every {report_every} users, longer cooldowns to reduce rate limit risk.\n"
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
                title="📬 Slow DM Progress Update",
                description=f"Progress: **{idx}/{total}** users",
                color=discord.Color.blurple()
            )
            embed.add_field(name="✅ Sent", value=str(sent))
            embed.add_field(name="❌ Failed", value=str(failed))
            await ctx.send(embed=embed)

        if idx % extra_pause_every == 0:
            await ctx.send(f"🕒 Extra cooldown: waiting {extra_pause} seconds after {idx} users...")
            await asyncio.sleep(extra_pause)
        elif idx % long_pause_every == 0:
            await ctx.send(f"🕒 Long cooldown: waiting {long_pause} seconds after {idx} users...")
            await asyncio.sleep(long_pause)
        elif idx % medium_pause_every == 0:
            await ctx.send(f"🕒 Medium cooldown: waiting {medium_pause} seconds after {idx} users...")
            await asyncio.sleep(medium_pause)

        await asyncio.sleep(short_delay)

    final_embed = discord.Embed(
        title="✅ Safe Slow DM Campaign Completed",
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

@bot.command(name='dmstatus', description="Show status of last DM campaign")
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

@bot.command(name='dmretry', aliases=['dmallcontinue', 'retrydm', 'dmfailures'],description="Retry DMs for users who failed in the last campaign")
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

@bot.command(name='getlog', aliases=['downloadlog', 'log'],description="Download specific log file or list all available logs")
@commands.has_permissions(administrator=True)
async def get_log(ctx, filename: str = None):
    """
    Download specific log file or list all available logs
    Usage: !getlog [filename] or just !getlog to list all logs
    """
    # Get all log files
    all_logs = [f for f in os.listdir() if f.startswith(("dm_success_", "dm_failed_", "dm_retry_"))]
    all_logs.sort(reverse=True)  # Sort by newest first
    
    if not all_logs:
        await ctx.send("❌ No log files found.")
        return
    
    # If no filename specified, show list of all logs
    if filename is None:
        embed = discord.Embed(
            title="📜 Available Log Files",
            description="Use `!getlog filename` to download a specific file",
            color=discord.Color.blue()
        )
        
        # Split logs into success and failed categories
        success_logs = [f for f in all_logs if "success" in f]
        failed_logs = [f for f in all_logs if "failed" in f]
        
        if success_logs:
            embed.add_field(
                name="✅ Success Logs",
                value="\n".join(f"`{f}`" for f in success_logs),
                inline=False
            )
        
        if failed_logs:
            embed.add_field(
                name="❌ Failed Logs",
                value="\n".join(f"`{f}`" for f in failed_logs),
                inline=False
            )
        
        await ctx.send(embed=embed)
        return
    
    # Check if requested file exists
    if filename not in all_logs:
        await ctx.send(f"❌ File `{filename}` not found. Use `!getlog` to see available files.")
        return
    
    # Send the requested file
    try:
        await ctx.send(f"📄 Here's your log file: `{filename}`", file=discord.File(filename))
    except Exception as e:
        await ctx.send(f"❌ Error sending file: {e}")

@get_log.error
async def get_log_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need administrator permissions to use this command.")
    else:
        await ctx.send(f"❌ Error: {error}")

@bot.command(name='clearlogs', aliases=['purgelogs'], description="Delete log files older than X days (default: 30)")
@commands.has_permissions(administrator=True)
async def clear_logs(ctx, days: int = 30):
    """Delete log files older than X days (default: 30)"""
    cutoff = datetime.now().timestamp() - (days * 86400)
    deleted = 0
    
    for filename in os.listdir():
        if filename.startswith(("dm_success_", "dm_failed_", "dm_retry_")):
            file_time = os.path.getmtime(filename)
            if file_time < cutoff:
                try:
                    os.remove(filename)
                    deleted += 1
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")
    
    await ctx.send(f"♻️ Deleted {deleted} log files older than {days} days.")

@bot.command(name='dmstats')
@commands.has_permissions(administrator=True)
async def dm_stats(ctx, days: int = 7):
    """Show DM statistics for the last X days"""
    cutoff = datetime.now() - timedelta(days=days)
    stats = {
        'total_sent': 0,
        'total_failed': 0,
        'unique_users': set(),
        'last_campaign': None
    }
    
    for filename in os.listdir():
        if filename.startswith("dm_success_") and datetime.fromtimestamp(os.path.getmtime(filename)) > cutoff:
            try:
                with open(filename, 'r', encoding='utf-8') as f:  # Added encoding here
                    stats['total_sent'] += len(f.readlines()) - 1
                    f.seek(0)
                    for line in f.readlines()[1:]:
                        if '|' in line:
                            stats['unique_users'].add(line.split('|')[1].strip())
            except UnicodeDecodeError:
                await ctx.send(f"⚠️ Warning: Could not read {filename} as UTF-8. Skipping...")
                continue
        
        if filename.startswith("dm_failed_"):
            try:
                with open(filename, 'r', encoding='utf-8') as f:  # Added encoding here
                    stats['total_failed'] += len(f.readlines()) - 1
            except UnicodeDecodeError:
                await ctx.send(f"⚠️ Warning: Could not read {filename} as UTF-8. Skipping...")
                continue
    
    embed = discord.Embed(
        title=f"📊 DM Statistics (Last {days} Days)",
        color=discord.Color.gold()
    )
    embed.add_field(name="✅ Successful DMs", value=str(stats['total_sent']))
    embed.add_field(name="❌ Failed DMs", value=str(stats['total_failed']))
    embed.add_field(name="👥 Unique Users Reached", value=str(len(stats['unique_users'])))
    embed.add_field(name="📈 Success Rate", 
                   value=f"{stats['total_sent']/(stats['total_sent']+stats['total_failed'])*100:.1f}%" if (stats['total_sent']+stats['total_failed']) > 0 else "N/A")
    
    await ctx.send(embed=embed)

    
@bot.command(name='dmroleall', aliases=['roledm', 'dmrole'], description="DM all users with a specific role")
@commands.has_permissions(administrator=True)
async def dm_role_all(ctx, role: discord.Role, *, custom_message=None):
    """DM all users with a specific role"""
    members = [m for m in role.members if not m.bot]
    total = len(members)
    if total == 0:
        await ctx.send(f"❌ No users found with the {role.name} role.")
        return

    message = custom_message or DEFAULT_MESSAGE
    if not message.strip():
        await ctx.send("❌ No default message set | ❌ No message was sent. Please provide a message.")
        return

    sent = 0
    failed = 0
    report_every = max(1, total // 10)  # More frequent updates since groups are smaller
    pause_every = 20
    cooldown_duration = 300

    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    log_file_success = f"dm_success_{role.name}_{timestamp}.txt"
    log_file_failed = f"dm_failed_{role.name}_{timestamp}.txt"

    with open(log_file_success, "w", encoding="utf-8") as f:
        f.write(f"✅ DMed Users with {role.name} role:\n")
    with open(log_file_failed, "w", encoding="utf-8") as f:
        f.write(f"❌ Failed DMs for {role.name} role:\n")

    await ctx.send(
        f"📤 Starting to DM {total} users with {role.name} role...\n"
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
                title=f"📬 DM Progress Update ({role.name})",
                description=f"Progress: **{idx}/{total}** users",
                color=role.color if role.color != discord.Color.default() else discord.Color.blurple()
            )
            embed.add_field(name="✅ Sent", value=str(sent))
            embed.add_field(name="❌ Failed", value=str(failed))
            await ctx.send(embed=embed)

        if idx % pause_every == 0:
            await ctx.send(f"🕒 Cooling down for 5 minutes after {idx} users...")
            await asyncio.sleep(cooldown_duration)

        await asyncio.sleep(1)

    final_embed = discord.Embed(
        title=f"✅ DM Campaign Completed ({role.name})",
        description=f"All **{total}** users with {role.name} role processed.",
        color=role.color if role.color != discord.Color.default() else discord.Color.green()
    )
    final_embed.add_field(name="✅ Total Sent", value=str(sent), inline=True)
    final_embed.add_field(name="❌ Total Failed", value=str(failed), inline=True)
    final_embed.add_field(name="📄 Logs", 
                         value=f"✅ Success: `{log_file_success}`\n ❌ Failed: `{log_file_failed}`", 
                         inline=False)
    await ctx.send(embed=final_embed)

@bot.command(name='dmroleallsafe', aliases=['roledmsecure', 'slowdmrole'], description="Slow, safer DM all users with a specific role")
@commands.has_permissions(administrator=True)
async def dm_role_all_safe(ctx, role: discord.Role, *, custom_message=None):
    members = [m for m in role.members if not m.bot]
    total = len(members)
    if total == 0:
        await ctx.send(f"❌ No users found with the {role.name} role.")
        return

    message = custom_message or DEFAULT_MESSAGE
    if not message.strip():
        await ctx.send("❌ No default message set | ❌ No message was sent. Please provide a message.")
        return

    sent = 0
    failed = 0
    report_every = max(1, total // 10)
    short_delay = 4
    medium_pause_every = 10
    medium_pause = 90
    long_pause_every = 25
    long_pause = 240
    extra_pause_every = 60
    extra_pause = 480

    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    log_file_success = f"dm_success_{role.name}_slow_{timestamp}.txt"
    log_file_failed = f"dm_failed_{role.name}_slow_{timestamp}.txt"

    with open(log_file_success, "w", encoding="utf-8") as f:
        f.write(f"✅ Slowly DMed Users with {role.name} role:\n")
    with open(log_file_failed, "w", encoding="utf-8") as f:
        f.write(f"❌ Slowly Failed DMs for {role.name} role:\n")

    await ctx.send(
        f"🐢 Starting safe slow DM of {total} users with {role.name} role...\n"
        f"⏱ Progress every {report_every} users, longer cooldowns to reduce rate limit risk.\n"
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
                title=f"📬 Slow DM Progress Update ({role.name})",
                description=f"Progress: **{idx}/{total}** users",
                color=role.color if role.color != discord.Color.default() else discord.Color.blurple()
            )
            embed.add_field(name="✅ Sent", value=str(sent))
            embed.add_field(name="❌ Failed", value=str(failed))
            await ctx.send(embed=embed)

        if idx % extra_pause_every == 0:
            await ctx.send(f"🕒 Extra cooldown: waiting {extra_pause} seconds after {idx} users...")
            await asyncio.sleep(extra_pause)
        elif idx % long_pause_every == 0:
            await ctx.send(f"🕒 Long cooldown: waiting {long_pause} seconds after {idx} users...")
            await asyncio.sleep(long_pause)
        elif idx % medium_pause_every == 0:
            await ctx.send(f"🕒 Medium cooldown: waiting {medium_pause} seconds after {idx} users...")
            await asyncio.sleep(medium_pause)

        await asyncio.sleep(short_delay)

    final_embed = discord.Embed(
        title=f"✅ Safe Slow DM Campaign Completed ({role.name})",
        description=f"All **{total}** users with {role.name} role processed.",
        color=role.color if role.color != discord.Color.default() else discord.Color.green()
    )
    final_embed.add_field(name="✅ Total Sent", value=str(sent), inline=True)
    final_embed.add_field(name="❌ Total Failed", value=str(failed), inline=True)
    final_embed.add_field(name="📄 Logs",
                         value=f"✅ Success: `{log_file_success}`\n ❌ Failed: `{log_file_failed}`",
                         inline=False)
    await ctx.send(embed=final_embed)

@dm_role_all.error
async def dm_role_all_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need administrator permissions to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please mention a role. Example: `!dmroleall @RoleName Your message`")
    else:
        await ctx.send(f"❌ Error: {error}")  


bot.run(TOKEN)
