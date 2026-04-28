# Steam Friend Annoyer - Implementation Summary

## Overview

This is a complete production-ready Windows desktop application built from the ground up to replace the original CLI tool. The application monitors multiple Steam friends and sends automated messages when they start playing games.

## Project Structure

```
steam-friend-annoyer/
├── src/                           # Main application source
│   ├── __init__.py
│   ├── app_controller.py          # Application orchestrator
│   ├── ui/                        # PySide6 GUI layer
│   │   ├── __init__.py
│   │   ├── main_window.py        # Main window & dialogs
│   │   └── widgets.py            # Reusable UI components
│   ├── steam_service/            # Steam client integration
│   │   ├── __init__.py
│   │   └── client.py             # SteamService wrapper
│   ├── persistence/              # Data storage & encryption
│   │   ├── __init__.py
│   │   └── storage.py            # StorageManager (thread-safe)
│   ├── system_integration/       # Windows integration
│   │   ├── __init__.py
│   │   ├── tray.py              # System tray icon & menu
│   │   ├── notifications.py      # Windows toast notifications
│   │   └── auto_update.py       # GitHub releases checker
│   └── utils/                   # Utility modules
│       ├── __init__.py
│       ├── config.py            # Paths & configuration
│       ├── encryption.py        # DPAPI encryption
│       └── validators.py        # Validators & parsers
├── build/
│   ├── pyinstaller.spec         # PyInstaller configuration
│   └── build.py                 # Build script
├── main.py                      # Entry point
├── dev.py                       # Development utilities
├── pyproject.toml              # Project metadata & dependencies
└── README.md                   # Full documentation
```

## Core Components

### 1. Persistence Layer (src/persistence/storage.py)

**StorageManager** - Thread-safe manager for all application data

Features:

- Atomic file I/O with locking
- JSON storage for lists and config
- DPAPI encryption for sensitive data (session)
- Default values on first run
- Full reset capability

Storage location: `%APPDATA%/SteamFriendAnnoyer/`

Files:

- `friends.json` - List of monitored friend SteamIDs
- `messages.json` - Messages to send
- `config.json` - Application settings (start with Windows, minimized, etc.)
- `session.enc` - Encrypted login session
- `app.log` - Application log

### 2. Steam Service (src/steam_service/client.py)

**SteamService** - Background Steam client wrapper

Features:

- Runs in separate daemon thread (non-blocking UI)
- Event-driven friend state monitoring
- Automatic message sending on game start
- Deduplication: One message per game session
- State reset when friend stops playing
- Thread-safe callbacks to UI
- Session persistence support

Architecture:

```
Main Thread (UI)  ←→  SteamService Thread
    ↓                       ↓
    QApplication        steam.client
    (Qt EventLoop)      (Steam Protocol)
```

### 3. UI Layer (src/ui/)

**MainWindow** - PySide6 main window with 4 tabs:

1. **Friends Tab**: ListWithInputWidget
   - Input field (accepts SteamID64 or URLs)
   - "Add" button + Enter key support
   - List with double-click remove

2. **Messages Tab**: ListWithInputWidget
   - Input field for message text
   - "Add" button + Enter key support
   - List with double-click remove

3. **Settings Tab**: SettingsWidget
   - Checkbox: Start with Windows (registry-based)
   - Checkbox: Start minimized
   - Button: Clear Session (removes login cache only)
   - Button: Clear All Data (full reset with confirmation)

4. **Control Section**: ControlWidget
   - Run/Stop button (toggles, changes color)
   - Status indicator (Disconnected/Running/Error)
   - Color-coded status display

**Dialogs**:

- LoginDialog - Username/password input
- 2FA prompt - For Steam Guard codes

### 4. System Integration (src/system_integration/)

**TrayIcon** - System tray icon and context menu

Features:

- Show/hide application from tray
- Tray menu: Start/Stop/Open/Exit
- Status tooltip
- Dynamic menu based on running state

**NotificationManager** - Windows toast notifications

Features:

- Uses win10toast library
- Shows when message is sent
- Includes friend ID and message preview
- Non-blocking (threaded)

**AutoUpdateManager** - GitHub releases checker

Features:

- Checks releases from munraitoo13/steam-friend-annoyer
- Downloads executable from release assets
- Supports version comparison
- Backup and rollback on failure
- Executable signing support (structure only)

### 5. Utilities (src/utils/)

**config.py** - Application paths and constants

- `get_app_data_dir()` - Returns %APPDATA%/SteamFriendAnnoyer/
- `get_friends_file()`, `get_messages_file()`, etc.
- APP_VERSION, GITHUB_REPO constants

**encryption.py** - Windows DPAPI encryption

- `encrypt_data(str) -> bytes`
- `decrypt_data(bytes) -> str`
- JSON variants for objects
- Fallback for non-Windows (plaintext)

**validators.py** - Input validation

- `parse_steam_id(input)` - Accepts SteamID64 and URLs
- `is_valid_steam_id(int)` - Validates range
- `normalize_message(str)` - Trim/clean
- `is_valid_message(str)` - Non-empty check

### 6. Application Controller (src/app_controller.py)

**ApplicationController** - Orchestrates all components

Responsibilities:

- Initialize all services (UI, Steam, Storage, Tray, Updates)
- Connect all callbacks between components
- Handle user interactions from UI
- Manage Steam service lifecycle
- Handle update notifications
- Route messages between layers

## Technology Stack

| Component     | Technology    | Version |
| ------------- | ------------- | ------- |
| GUI           | PySide6       | 6.6.0+  |
| Steam         | steam[client] | 1.4.4+  |
| HTTP          | requests      | 2.31.0+ |
| Crypto        | cryptography  | 41.0.0+ |
| Windows       | pywin32       | 305+    |
| Notifications | win10toast    | 1.0+    |
| Build         | PyInstaller   | 6.0.0+  |

## Build & Distribution

### Development Mode

```bash
python dev.py install          # Install dependencies
python dev.py install-dev      # Include PyInstaller
python dev.py run              # Run from source
```

### Build Executable

```bash
python build/build.py
```

Output: `dist/SteamFriendAnnoyer/SteamFriendAnnoyer.exe`

PyInstaller Configuration:

- Single executable (no console window)
- All dependencies bundled
- Supports code signing (codesign_identity in spec)
- Windows-only (could be adapted for other platforms)

## Data Flow

### Friend Monitoring Flow

```
1. User adds friend (SteamID64 or URL)
   ↓
2. Validator parses and validates
   ↓
3. StorageManager saves to friends.json
   ↓
4. UI updated with friend list
   ↓
5. SteamService monitors friend (if running)
   ↓
6. Friend starts game (PersonaState event)
   ↓
7. SteamService detects state change
   ↓
8. Select random message from message list
   ↓
9. Send message via Steam API
   ↓
10. Deduplication marker set (prevents re-send)
   ↓
11. Notification sent to user
   ↓
12. Friend stops playing (PersonaState event)
   ↓
13. Deduplication marker cleared
```

### Login Flow

```
1. User clicks "Run"
   ↓
2. Check if session cached
   ↓
3. If no session:
   ├─ Show LoginDialog
   ├─ User enters username/password
   └─ Prompt for 2FA if enabled
   ↓
4. SteamService.start(username, password, session)
   ├─ Runs in background thread
   ├─ Authenticates with Steam
   └─ Saves session encrypted (DPAPI)
   ↓
5. On success:
   ├─ Call on_connected callback
   ├─ Update UI status
   └─ Start monitoring
   ↓
6. On next run:
   ├─ Load cached session
   ├─ Attempt silent re-auth
   └─ Skip login prompt if valid
```

### Session Management

- **First run**: Prompt for login → Save encrypted session
- **Subsequent runs**: Load cached session → Silent auth
- **Clear Session**: Delete session.enc, prompt for login next run
- **Clear All Data**: Delete everything, reset to defaults

## Security Considerations

1. **Credential Storage**
   - Session encrypted with Windows DPAPI
   - Per-user encryption (tied to Windows account)
   - Stored in user's %APPDATA% directory
   - Separate "Clear Session" to remove just login cache

2. **Message Deduplication**
   - Prevents duplicate sends per game session
   - Resets when game_id changes or becomes null
   - Per-friend tracking

3. **Input Validation**
   - SteamID64 range checking
   - URL parsing with regex
   - Message validation (non-empty)
   - Invalid entries silently rejected from UI

4. **Thread Safety**
   - StorageManager uses RLock for all operations
   - SteamService runs in isolated thread
   - Qt signals for safe cross-thread communication

## Concurrency Model

### Threading

- **Main Thread (UI)**
  - Qt event loop
  - Handles user input
  - Runs on startup

- **Steam Service Thread** (daemon)
  - SteamClient loop
  - Friend monitoring
  - Asynchronous message sends
  - Communicates via callbacks

- **Background Threads** (for long operations)
  - Auto-update checker
  - Network requests (non-blocking)

### Thread-Safe Components

- **StorageManager**: RLock on all operations
- **SteamService**: Thread-safe callbacks
- **Qt Signals**: Built-in thread-safe signaling

## Configuration & Persistence

### Default Configuration (First Run)

```json
{
  "start_with_windows": false,
  "start_minimized": false
}
```

### Default Messages

```json
{
  "messages": [
    "pode fechar",
    "sai do jogo",
    "vc tá viciado demais",
    "larga esse jogo"
  ]
}
```

### Registry/Startup Integration

For "Start with Windows":

- (To be implemented) Adds shortcut to Windows Startup folder
- Or registry entry for autorun
- Currently only stores setting in config.json

## Error Handling

### Graceful Degradation

1. **Login Failures**
   - Shows error dialog
   - Allows retry
   - Doesn't crash app

2. **Steam Disconnects**
   - Automatic reconnect attempts
   - Status updated to "Error"
   - User can manually stop

3. **Message Send Failures**
   - Logged but non-fatal
   - Allows continued monitoring
   - Notification still shown for attempt

4. **Update Check Failures**
   - Silently logged
   - Doesn't block app startup
   - User can retry from menu (future feature)

## Testing Checklist

Before release, verify:

- [ ] Launch application
- [ ] Add friend (test SteamID64 and URL)
- [ ] Add multiple messages
- [ ] Login with Steam credentials
- [ ] Monitor friend (watch for state changes)
- [ ] Message sent when friend starts game
- [ ] No duplicate messages for same game
- [ ] Friend stops game, state resets
- [ ] Logout and login again (session persistence)
- [ ] Clear Session, login again (clears cache)
- [ ] Clear All Data, recreate setup
- [ ] Build to .exe with PyInstaller
- [ ] Run .exe standalone
- [ ] Check %APPDATA% for data files
- [ ] Verify encryption of session.enc
- [ ] Test system tray (minimize, close, open)
- [ ] Test 2FA flow (if enabled)
- [ ] Check app.log for errors

## Future Enhancements

(Design ready, not implemented):

- [ ] NSIS installer with uninstaller
- [ ] Custom icon/branding
- [ ] Message templates with variables
- [ ] Scheduled messaging
- [ ] Activity log viewer in UI
- [ ] Friend profile preview/link
- [ ] Multi-account support
- [ ] Message statistics/history
- [ ] Custom notification sounds
- [ ] Proxy support for Steam
- [ ] Auto-backup of configuration
- [ ] Performance metrics

## Deployment

### For End Users

1. Download SteamFriendAnnoyer.exe from releases
2. Run directly (no installation needed)
3. Data stored in %APPDATA%/SteamFriendAnnoyer/
4. Portable - can run from USB

### For Developers

```bash
git clone https://github.com/munraitoo13/steam-friend-annoyer.git
cd steam-friend-annoyer
python dev.py install-dev
python build/build.py
```

## Support & Troubleshooting

See README.md for comprehensive troubleshooting guide, including:

- Login issues
- Steam disconnects
- Notification problems
- Build failures
- Performance considerations

## Key Design Decisions

1. **Separate Steam Thread**: Prevents UI blocking, uses callbacks
2. **DPAPI Encryption**: Windows-native, secure, per-user
3. **PySide6 over Tkinter**: Modern UI, better aesthetics, animations support
4. **Event-Driven**: Uses Steam's persona state events (efficient)
5. **Modular Architecture**: Clean separation of concerns
6. **Git Releases for Updates**: No custom server required
7. **%APPDATA% Storage**: Standard Windows location, user-owned
8. **Standalone .exe**: No installation, fully portable

## Known Limitations

- Windows only (could be adapted to Linux/Mac)
- Single account per installation
- No message placeholders/templates
- No rate limiting (Steam API handles this)
- No UI logging (only file logging)
- Auto-start registry entry not yet implemented

---

**Version**: 1.0.0
**Repository**: https://github.com/munraitoo13/steam-friend-annoyer
**Last Updated**: 2026-04-27
