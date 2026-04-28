# Quick Start Guide

## Installation & Setup (5 minutes)

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd steam-friend-annoyer

# Install all required packages
python dev.py install
```

### Step 2: Run in Development Mode

```bash
python dev.py run
```

Or directly:

```bash
python main.py
```

## Building the Executable (10 minutes)

### Step 1: Install Build Dependencies

```bash
python dev.py install-dev
```

### Step 2: Build

```bash
python build/build.py
```

### Step 3: Find Your Executable

```
dist/SteamFriendAnnoyer/SteamFriendAnnoyer.exe
```

You can run this directly or move it anywhere on your system.

## First Time Setup (3 minutes)

1. **Launch** the application
2. **Add Friends**:
   - Go to "Friends" tab
   - Enter a SteamID64 or Steam profile URL
   - Click "Add" or press Enter
   - Repeat for each friend

3. **Add Messages**:
   - Go to "Messages" tab
   - Enter a message
   - Click "Add" or press Enter
   - Add multiple messages for variety

4. **Configure (Optional)**:
   - Go to "Settings" tab
   - Enable "Start with Windows" to auto-launch
   - Enable "Start minimized" to launch to tray

5. **Start Monitoring**:
   - Click "Run"
   - Enter your Steam username and password
   - If prompted, enter your Steam Guard code
   - Status will show "Running"

## How to Use

### Monitoring Friends

Once running:

- The app monitors all friends you added
- When a friend starts a game, a random message is sent
- You get a Windows notification
- Each game session sends the message once (no duplicates)
- When they stop playing, the system resets

### System Tray

- Click the minimize button or window close button (X)
- App minimizes to system tray (bottom-right corner)
- Right-click tray icon for quick options:
  - **Start/Stop**: Control monitoring
  - **Open**: Show the window
  - **Exit**: Close application

### Stopping

- Click "Stop" button, or
- Use "Stop" from tray menu

## Common Tasks

### Change Friends/Messages

- While stopped: Edit freely
- While running: Changes take effect immediately
- No restart required

### Login Again (New Account)

Settings → "Clear Session" → Click "Run" → Enter new credentials

### Complete Reset

Settings → "Clear All Data" → Confirm

This deletes:

- All friends
- All messages
- Login cache
- Settings

The app resets to defaults with example messages.

### Check Logs

Open file explorer and navigate to:

```
%APPDATA%\SteamFriendAnnoyer\
```

You'll see:

- `friends.json` - Your friends list
- `messages.json` - Your messages
- `config.json` - Settings
- `session.enc` - Encrypted login (safe to delete)
- `app.log` - Debug log (check if issues)

## Troubleshooting

### "Login Failed"

- Verify username and password
- Try "Clear Session" in Settings
- Check if Steam account needs verification

### "No Message Sent"

- Ensure friends are added correctly
- Ensure at least one message exists
- Check app.log for errors

### "Friend Not Detected"

- Verify Steam ID is correct
- Check friend's privacy settings (add you)
- Restart monitoring

### App Won't Start

- Check Windows Defender/antivirus (may flag new .exe)
- Run as Administrator
- Check `%APPDATA%\SteamFriendAnnoyer\app.log` for errors

## Tips & Tricks

### Finding Your Friend's SteamID

1. Go to their Steam profile
2. Copy the URL (e.g., `steamcommunity.com/profiles/123456789`)
3. Paste in the app - it extracts the ID automatically

### Mass Add Friends

Add one friend, then manually edit `%APPDATA%\SteamFriendAnnoyer\friends.json`:

```json
{
  "friends": [76561198123456789, 76561198987654321]
}
```

Save and restart.

### Backup Your Setup

Copy folder: `%APPDATA%\SteamFriendAnnoyer\`

To restore, copy back the files (or the entire folder).

### Update Checking

The app checks for updates automatically on startup. If a new version is available, you'll see a prompt. Click "Yes" to download and install.

## Keyboard Shortcuts

- **Enter** in Friend/Message fields: Add item
- **Double-click** item: Remove item
- **Alt+F4**: Close window (minimizes to tray)

## Support

For issues or feature requests:

- Check README.md for detailed docs
- Look at IMPLEMENTATION.md for technical details
- Check app.log for error messages

---

Need help? See the full README.md or IMPLEMENTATION.md for detailed documentation.
