# Steam Friend Annoyer

Automatiza o envio de uma mensagem privada para um amigo específico da sua lista da Steam assim que ele entrar em um jogo. Se o script iniciar e o amigo já estiver jogando, a mensagem também é enviada imediatamente.

O projeto usa a biblioteca [steam](https://steam.readthedocs.io/) para conectar na conta, ler o estado de presença do amigo e enviar a mensagem pelo chat da Steam.

## Funcionalidades

- Envia mensagem para um amigo específico pelo Steam ID64.
- Detecta quando o amigo já está em jogo logo na inicialização.
- Detecta mudanças de presença e dispara a mensagem quando um novo jogo começa.
- Funciona com login normal da Steam e autenticação em dois fatores.
- Configuração simples via variáveis de ambiente.

## Requisitos

- Python 3.12 ou superior.
- Conta Steam válida.
- A biblioteca `uv` instalada, se você quiser usar o fluxo recomendado do projeto.

## Instalação

1. Clone o repositório.
2. Entre na pasta do projeto.
3. Instale as dependências.

```bash
uv sync
```

Se preferir usar `pip`, instale as dependências listadas em `pyproject.toml`.

## Configuração

Crie um arquivo `.env` na raiz do projeto com estas variáveis:

```env
USERNAME=seu_usuario_steam
PASSWORD=sua_senha_steam
TARGET_FRIEND_ID64=7656119xxxxxxxxxx
MESSAGE=pode fechar
```

### Variáveis de ambiente

- `USERNAME`: nome de usuário da sua conta Steam.
- `PASSWORD`: senha da sua conta Steam.
- `TARGET_FRIEND_ID64`: Steam ID64 do amigo que deve receber a mensagem.
- `MESSAGE`: texto enviado no chat. Se não definir, o padrão é `pode fechar`.

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
