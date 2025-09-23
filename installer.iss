; =======================
; GridX - Inno Setup Script
; =======================

; --------- METADADOS ---------
#define MyAppName "GridX"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "Arthur Dev Labs"
#define MyAppExeName "GridX.exe"
#define MyAppId "{{5CF6B0B2-8A73-4A5A-94A4-9B4A2E9C9E10}}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://bit.ly/prdctec

; Diretório padrão de instalação
DefaultDirName={autopf}\{#MyAppName}
; Grupo no Menu Iniciar
DefaultGroupName={#MyAppName}
; Pasta de saída do instalador compilado
OutputDir=dist_installer
OutputBaseFilename={#MyAppName}_Setup_{#MyAppVersion}

; Ícone do instalador (use .ico com múltiplos tamanhos, ex: 16,32,48,64,128,256)
SetupIconFile="gridx.ico"

; Aparência
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

; Mostra o ícone do app no Painel de Controle
UninstallDisplayIcon={app}\{#MyAppExeName}
Uninstallable=yes

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english";    MessagesFile: "compiler:Default.isl"

[Files]
; Se você usou --onefile no PyInstaller
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Se você usou --onedir (pasta cheia de DLLs), use isso em vez do de cima:
; Source: "dist\GridX\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Atalho no Menu Iniciar
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; Atalho no Desktop (opcional, via Tasks)
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
; Usuário pode escolher criar atalho no desktop
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Opções adicionais:"; Flags: unchecked

[Run]
; Pergunta se quer executar o app após instalar
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName} agora"; Flags: nowait postinstall skipifsilent
