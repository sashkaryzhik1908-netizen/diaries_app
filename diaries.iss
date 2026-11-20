
#define MyAppName "Diaries"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Diaries"
#define MyAppExeName "Diaries.exe"

[Setup]
AppId={{A71C8B42-5E31-4F91-9C62-8D72A2B103F4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={localappdata}\Programs\Diaries
DefaultGroupName={#MyAppName}

PrivilegesRequired=lowest

OutputDir=.
OutputBaseFilename=Diaries_Setup

Compression=lzma
SolidCompression=yes
WizardStyle=modern

Uninstallable=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные значки:"

[Files]
Source: "dist\Diaries\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Diaries"; Filename: "{app}\Diaries.exe"
Name: "{autodesktop}\Diaries"; Filename: "{app}\Diaries.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Diaries.exe"; Description: "Запустить Diaries"; Flags: nowait postinstall skipifsilent
