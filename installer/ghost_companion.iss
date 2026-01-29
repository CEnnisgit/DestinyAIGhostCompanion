; Inno Setup script for Ghost Companion desktop app
; Build with Inno Setup Compiler (https://jrsoftware.org/isinfo.php)

#define AppName "Ghost Companion"
#define AppVersion "0.1.0"
#define Publisher "Your Company"
#define URL "https://your-site.example"

[Setup]
AppId={{6A0F8C10-0F4E-4C9D-AB7C-1E9A8A7CFA11}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#URL}
DefaultDirName={pf}\{#AppName}
DefaultGroupName={#AppName}
DisableDirPage=no
DisableProgramGroupPage=yes
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=dist\installer
OutputBaseFilename=GhostCompanion-Setup-{#AppVersion}
; Optional: provide an icon file
; SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\GhostCompanion.exe
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Point this to the PyInstaller output folder (onefolder mode is recommended)
Source: "dist\GhostCompanion\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\GhostCompanion.exe"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\GhostCompanion.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GhostCompanion.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
// You can add VC++ Redistributable detection here if needed and offer to install
