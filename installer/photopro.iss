; PhotoPro Inno Setup Script
; Generates standalone "PhotoPro Setup.exe" for 64-bit Windows systems.
; Completely offline installer: bundles all Python runtimes, binaries, and ONNX models.

#define MyAppName "PhotoPro"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "PhotoPro Software"
#define MyAppURL "https://github.com/maijamalhoon/PhotoPro"
#define MyAppExeName "PhotoPro.exe"

[Setup]
AppId={{D3F9B76A-4A82-4DFB-86DF-7B29B1238910}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\THIRD_PARTY_LICENSES.md
OutputDir=..\dist_installer
OutputBaseFilename=PhotoPro Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\PhotoPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Also ensure model is placed in application folder
Source: "..\u2netp.onnx"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
