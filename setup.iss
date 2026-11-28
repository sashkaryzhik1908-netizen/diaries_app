[Setup]
AppId={{C4D9DFA6-53C3-4549-A7F6-B6078BBEE98E}
AppName=Diaries
AppVersion=1.3
DefaultDirName={localappdata}\Programs\Diaries
DefaultGroupName=Diaries
OutputDir=installer
OutputBaseFilename=Diaries_Setup_1.3
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
CloseApplications=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Diaries.exe

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "dist\Diaries\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "instance\database.db"; DestDir: "{userappdata}\Diaries"; Flags: onlyifdoesntexist uninsneveruninstall
Source: ".env.example"; DestDir: "{userappdata}\Diaries"; DestName: ".env"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\Diaries"; Filename: "{app}\Diaries.exe"
Name: "{userdesktop}\Diaries"; Filename: "{app}\Diaries.exe"

[Run]
Filename: "{app}\Diaries.exe"; Description: "Запустить Diaries"; Flags: nowait postinstall skipifsilent