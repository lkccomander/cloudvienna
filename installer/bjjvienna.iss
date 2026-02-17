[Setup]
AppId={{0D1CDE2B-2335-4D20-BE24-B8BDE2D2D4F8}
AppName=BJJ Vienna
AppVersion=1.0.4
AppPublisher=BJJ Vienna
DefaultDirName={userappdata}\BJJVienna
DefaultGroupName=BJJ Vienna
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=BJJVienna-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\logo1.ico
UninstallDisplayIcon={app}\gui.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\gui.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\BJJ Vienna"; Filename: "{app}\gui.exe"
Name: "{autodesktop}\BJJ Vienna"; Filename: "{app}\gui.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\gui.exe"; Description: "Launch BJJ Vienna"; Flags: nowait postinstall skipifsilent
