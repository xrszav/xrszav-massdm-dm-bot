# 📬 Discord XrsZav MassDm / DM Bot
This is a Discord bot built with `discord.py` for server administrators who need to send direct messages (DMs) safely. It supports single-user DMs, bulk DMs, retrying failed campaigns, previewing messages, logging, status reports, and safer slow-mode delivery. So N1 Mass DM bot in the world.

## ⚙️ Features
- `!dm @user [message]`
  - Send a DM to a specific user.

- `!dmpreview [message]`
  - Preview the DM by sending it to yourself before sending a campaign.

- `!dmall [message]`
  - Mass DM all server members (excluding bots) using the default or provided message.
  - Built-in cooldowns and progress updates help reduce rate-limit risk.

- `!dmallsafe [message]`
  - Slower, more cautious version of mass DM.
  - Adds longer delays and extra cooldowns to help avoid rate-limits.

- `!dmroleall @Role [message]`
  - DM all members with a specific role.

- `!dmroleallsafe @Role [message]`
  - Slower, safer version of role-based DMs with extra cooldowns.

- `!dmretry <success_log_file>`
  - Retry failed DMs from a previous campaign by reading the success log file.

- `!dmstatus`
  - Report the last campaign status from the latest success/failed log files.

- `!dmstats [days]`
  - Show DM statistics for the last X days (default: 7).

- `!getlog [filename]`
  - List available log files or download a specific one.

- `!clearlogs [days]`
  - Delete log files older than the specified number of days (default: 30).

## 🧠 Command Aliases
| Command | Aliases |
|---|---|
| `!dmall` | `!massdm`, `!dmallusers` |
| `!dmallsafe` | `!massdmsafe`, `!slowdmall` |
| `!dmroleall` | `!roledm`, `!dmrole` |
| `!dmroleallsafe` | `!roledmsecure`, `!slowdmrole` |
| `!dmretry` | `!dmallcontinue`, `!retrydm`, `!dmfailures` |
| `!getlog` | `!downloadlog`, `!log` |
| `!clearlogs` | `!purgelogs` |

## 📁 Logs
The bot writes log files to the bot folder for tracking campaigns.

- ✅ `dm_success_<timestamp>.txt` — users who were successfully DM’d.
- ❌ `dm_failed_<timestamp>.txt` — users who failed to receive a DM.
- ✅ `dm_retry_success_<timestamp>.txt` — retry campaign success log.
- ❌ `dm_retry_failed_<timestamp>.txt` — retry campaign failed log.
- `dm_success_slow_<timestamp>.txt` / `dm_failed_slow_<timestamp>.txt` — safe slow campaign logs.
- `dm_success_<role>_slow_<timestamp>.txt` / `dm_failed_<role>_slow_<timestamp>.txt` — role-based safe slow campaign logs.

## 🔐 Permissions
Only users with the `Administrator` permission can run DM commands.

## 🛠 Configuration
Edit `config.json` before running the bot:

```json
{
  "token": "YOUR_BOT_TOKEN_HERE",
  "prefix": "!",
  "default_message": "This is a default DM message."
}
```

## 🚀 Running the Bot
Make sure you have Python 3.8+ and `discord.py` installed.

```bash
pip install -U discord.py
python3 bot.py
```

## ⚠️ Warnings
Mass DMing can trigger Discord rate limits or spam detection.
Use the safe commands (`!dmallsafe`, `!dmroleallsafe`) if you want extra delay and lower risk.

**Use this bot responsibly.**

## 🆘 Support & Contributions
Need help or have suggestions?

- **Discord**: `xrszav0`
- **Telegram**: `@xrszav` [https://t.me/xrszav](https://t.me/xrszav)
- **GitHub**: Open an issue or pull request for improvements.

## 🌐 Websites
- https://oblivity.xyz
- https://xrszav.xyz 


## 📄 License
This project is licensed under the **[MIT License](https://choosealicense.com/licenses/mit/)**.

## 🔑 Keywords
Discord Bot, Mass DM, Direct Messages, Bulk Messaging, Bot Development, Python, Discord.py, Admin Tools

## ONLY FOR EDUCATIONAL PURPOSES

