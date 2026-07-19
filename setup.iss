[Setup]
AppName=Jarvis AI Assistant
AppVersion=1.0
DefaultDirName={autopf}\JarvisAgent
DefaultGroupName=Jarvis
OutputDir=.\Installer
OutputBaseFilename=Jarvis_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\Jarvis.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; DestName: ".env"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\Jarvis"; Filename: "{app}\Jarvis.exe"
Name: "{group}\Jarvis"; Filename: "{app}\Jarvis.exe"
Name: "{userstartup}\Jarvis"; Filename: "{app}\Jarvis.exe"

[Run]
Filename: "{app}\Jarvis.exe"; Description: "Launch Jarvis"; Flags: nowait postinstall skipifsilent
