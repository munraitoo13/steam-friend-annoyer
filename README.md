# Steam Friend Annoyer - Desktop Edition

Monitor your Steam friends and automatically send messages when they start playing games.

## Features

- **Multi-friend monitoring**: Watch multiple friends simultaneously
- **Automated messages**: Send random messages from your configured list when friends start playing
- **Session persistence**: Login once, session is cached and reused
- **System tray integration**: Minimize to tray, quick actions from system tray
- **Windows toast notifications**: Get notified when messages are sent
- **Data persistence**: All settings stored in `%APPDATA%/SteamFriendAnnoyer/`
- **Auto-update**: Check for new versions from GitHub releases
- **Portable executable**: Single standalone .exe file, no installation required

## Architecture

```
src/
├── ui/              # PySide6 GUI components
│   ├── main_window.py
│   └── widgets.py
├── steam_service/   # Steam client wrapper
│   └── client.py
├── persistence/     # Data storage and encryption
│   └── storage.py
├── system_integration/  # Tray, notifications, updates
│   ├── tray.py
│   ├── notifications.py
│   └── auto_update.py
└── utils/           # Helpers and validators
    ├── config.py
    ├── encryption.py
    └── validators.py
```

## Installation & Setup

### Requirements

- Python 3.12 or later
- Windows (for executable)

### Development Installation

```bash
# Clone and navigate to project
cd steam-friend-annoyer

# Install dependencies
python dev.py install

# For development with PyInstaller
python dev.py install-dev
```

### Running in Development

```bash
python dev.py run
```

Or directly:

```bash
python main.py
```

## Building the Executable

### Build Requirements

```bash
python dev.py install-dev
```

### Build Command

```bash
python build/build.py
```

The executable will be created at:

```
dist/SteamFriendAnnoyer/SteamFriendAnnoyer.exe
```

### Manual PyInstaller Build

```bash
pyinstaller build/pyinstaller.spec
```

## Usage

### First Run

1. Launch the application
2. Go to the **Friends** tab and add friends by:
   - Entering a SteamID64 (17-digit number, e.g., 76561198123456789)
   - Or pasting a Steam profile URL (extracts the ID automatically)
3. Go to the **Messages** tab and add messages to send
4. Click **Run** to start monitoring
5. Enter your Steam credentials when prompted
6. If Steam Guard is enabled, enter the 2FA code

### Features

**Friends Tab**

- Add multiple friends to monitor
- Double-click or use the X button to remove friends
- Supports SteamID64 and Steam profile URLs

**Messages Tab**

- Add multiple messages
- One random message is sent when a friend starts playing
- Double-click or use the X button to remove messages

**Settings Tab**

- **Start with Windows**: Auto-launch on system startup (registry-based)
- **Start minimized**: Launch directly to system tray
- **Clear Session**: Remove login cache (requires re-login on next run)
- **Clear All Data**: Full reset of all settings, friends, messages, and login data

**Control Section**

- **Run/Stop button**: Toggle monitoring on/off
- **Status indicator**: Shows current state (Disconnected/Running/Error)

### System Tray

- Minimize the window to system tray (click minimize or X)
- Right-click tray icon for quick actions:
  - **Start/Stop**: Control monitoring
  - **Open**: Show main window
  - **Exit**: Close application

## Data Storage

All application data is stored in:

```
%APPDATA%/SteamFriendAnnoyer/
```

Files:

- `friends.json` - List of monitored friends
- `messages.json` - Messages to send
- `config.json` - Application settings
- `session.enc` - Encrypted login session
- `app.log` - Application log file

### Security

- Session data is encrypted using Windows DPAPI
- Credentials are stored encrypted
- Clearing session only removes login cache; data persists

## Logging

Application logs are saved to:

```
%APPDATA%/SteamFriendAnnoyer/app.log
```

## Auto-Update

The application automatically checks for updates from:

```
https://github.com/munraitoo13/steam-friend-annoyer/releases
```

When an update is available, you'll be prompted to download and install it.

## GitHub Build and Release Automation

The repository includes a GitHub Actions workflow that:

- Builds the Windows `.exe` on every push to `main`
- Uploads the `.exe` as a downloadable workflow artifact
- Publishes the `.exe` to GitHub Releases when you push a tag like `v1.0.1`

To publish a release build:

```bash
git tag v1.0.1
git push origin v1.0.1
```

That is the step that turns your build into a stable download link for users and for the app's auto-update feature.

## Development

### Code Structure

**Persistence Layer** (`src/persistence/`)

- Thread-safe JSON storage
- DPAPI encryption for sensitive data
- Config, friends, messages, and session management

**Steam Service** (`src/steam_service/`)

- Background thread for Steam client
- Event-driven state changes
- Friend presence monitoring
- Message sending with deduplication

**UI Layer** (`src/ui/`)

- PySide6 main window
- Reusable widgets (lists, controls, settings)
- Login and confirmation dialogs

**System Integration** (`src/system_integration/`)

- System tray icon and menu
- Windows toast notifications
- GitHub releases auto-update checker

**Utilities** (`src/utils/`)

- Configuration paths
- Windows DPAPI encryption
- Steam ID and message validation

### Threading Model

- **Main thread**: UI event loop (Qt)
- **Steam thread**: Background Steam client, runs independently
- **Communication**: Thread-safe callbacks from Steam service to UI

### Building with Code Signing

To build a signed executable:

1. Update `build/pyinstaller.spec`:

```python
exe = EXE(
    ...
    codesign_identity="Your Certificate Name",
    ...
)
```

2. Build:

```bash
pyinstaller build/pyinstaller.spec
```

## Troubleshooting

### Login Fails

- Verify username and password
- Try clearing session via Settings → Clear Session
- Check app.log for detailed error messages

### Steam Disconnects

- Check internet connection
- Verify Steam account is accessible
- Logs will show reconnection attempts

### Notifications Not Showing

- Verify Windows notifications are enabled
- Notifications are sent with app name "SteamFriendAnnoyer"
- Check Windows notification settings for the app

### Application Won't Start

- Check `%APPDATA%/SteamFriendAnnoyer/app.log`
- Verify all dependencies are installed
- Try running in development mode to see errors

## API & Integration

### Steam Service Callbacks

The application uses event-driven callbacks:

```python
steam_service.set_on_connected(callback)           # Connected to Steam
steam_service.set_on_disconnected(callback)        # Disconnected
steam_service.set_on_friend_state_changed(callback)  # Friend started/stopped playing
steam_service.set_on_message_sent(callback)        # Message sent successfully
steam_service.set_on_error(callback)               # Error occurred
```

### Storage Thread Safety

`StorageManager` is thread-safe with internal locking:

```python
storage = StorageManager()
storage.add_friend(steam_id)        # Thread-safe
storage.get_friends()               # Thread-safe
storage.set_session(session_data)   # Thread-safe
```

## Performance Considerations

- Steam client runs in separate thread (non-blocking UI)
- Friend state updates via event stream (not polling)
- Deduplication prevents duplicate messages per game session
- Lazy file I/O with batched writes for performance

## Future Enhancements

- [ ] Executable installer (NSIS)
- [ ] Custom icon/branding
- [ ] Message templates and variables
- [ ] Schedule-based messaging
- [ ] Activity logging UI
- [ ] Friend profile preview
- [ ] Multi-account support
- [ ] Message history

## License

See LICENSE file (if applicable)

## Support

For issues, feature requests, or contributions:

- GitHub: https://github.com/munraitoo13/steam-friend-annoyer
- Issues: https://github.com/munraitoo13/steam-friend-annoyer/issues

## Como descobrir o Steam ID64

Você pode pegar o Steam ID64 do perfil do amigo pela URL do perfil, por ferramentas de conversão de Steam ID, ou por páginas públicas de perfil que mostrem o identificador numérico.

Se o perfil for público, uma forma prática é usar a URL completa do perfil e converter o identificador para o formato de 64 bits com uma ferramenta confiável.

## Uso

Depois de configurar o `.env`, execute:

```bash
uv run main.py
```

Ao iniciar, o script pode pedir o código de autenticação em dois fatores da Steam. Depois disso ele:

- sincroniza o estado do amigo alvo;
- envia a mensagem se ele já estiver em um jogo;
- continua monitorando atualizações de presença para detectar novos jogos.

## Como funciona

Em alto nível, o fluxo é este:

1. Faz login na Steam.
2. Espera a lista de amigos ficar pronta.
3. Busca o amigo alvo pelo Steam ID64.
4. Lê o jogo atual do amigo a partir do estado de presença.
5. Envia a mensagem apenas quando detecta uma nova sessão de jogo.

Isso evita disparos desnecessários repetidos para o mesmo jogo.

## Exemplo de mensagem

Você pode deixar a mensagem mais curta, mais engraçada ou mais direta. Por exemplo:

```env
MESSAGE=já pode fechar?
```

## Solução de problemas

### O script pede 2FA toda vez

Isso pode acontecer quando a conta ainda não tem um login key reutilizável salvo ou quando a sessão foi invalidada. Faça o login novamente e confirme o código normalmente.

### O amigo não recebe a mensagem

Confira os pontos abaixo:

- o Steam ID64 está correto;
- o amigo está adicionado na sua lista;
- sua conta está online e logada com sucesso;
- a mensagem privada não está bloqueada nas preferências da Steam.

### O script diz que não encontrou o amigo

Isso normalmente significa que o `TARGET_FRIEND_ID64` está incorreto ou que a conta ainda não carregou o estado do amigo durante a sessão atual.

## Estrutura do projeto

- `main.py`: lógica principal de login, monitoramento de presença e envio da mensagem.
- `pyproject.toml`: metadados do projeto e dependências.
- `README.md`: documentação do projeto.

## Observações

- O projeto foi pensado para uso pessoal com amigos que consentem com esse tipo de automação.
- Se quiser adaptar o comportamento, o ponto principal está em `main.py`.
