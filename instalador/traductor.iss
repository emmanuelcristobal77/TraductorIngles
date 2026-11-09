; Inno Setup 6 para TraductorIngles. Uso, desde la raíz del repositorio y después de PyInstaller:
;   iscc instalador\traductor.iss
; Genera dist\TraductorIngles-Setup.exe.
; - Acceso directo en el escritorio y en el menú Inicio (RF-001).
; - Ningún arranque automático: ni la clave Run del registro ni la carpeta Inicio (RF-004).
; - Al desinstalar borra los ajustes, la cuenta guardada y la bitácora (RF-015a).
; - No lleva ningún dato de la persona ni claves del servicio.

#define Nombre "TraductorIngles"
#define Version "0.1.0"

[Setup]
AppId={{6B3F6E2A-6D1C-4C1E-9B7A-5A1F0E2D7C31}
AppName={#Nombre}
AppVersion={#Version}
AppPublisher={#Nombre}
DefaultDirName={autopf}\{#Nombre}
DefaultGroupName={#Nombre}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename={#Nombre}-Setup
SetupIconFile=..\src\traductor\recursos\icono.ico
UninstallDisplayIcon={app}\{#Nombre}.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\dist\{#Nombre}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifexist "vc_redist.x64.exe"
; Solo si PyInstaller no copió msvcp140.dll, vcruntime140.dll y vcruntime140_1.dll en la app.
Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: FaltaVCRedist
#endif

[Icons]
Name: "{autodesktop}\{#Nombre}"; Filename: "{app}\{#Nombre}.exe"
Name: "{autoprograms}\{#Nombre}"; Filename: "{app}\{#Nombre}.exe"

[Run]
#ifexist "vc_redist.x64.exe"
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Instalando componentes de Microsoft Visual C++…"; Flags: waituntilterminated; Check: FaltaVCRedist
#endif
Filename: "{app}\{#Nombre}.exe"; Description: "Abrir {#Nombre}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\TraductorIngles"
Type: filesandordirs; Name: "{localappdata}\TraductorIngles"

[Code]
function FaltaVCRedist: Boolean;
var
  Instalado: Cardinal;
begin
  Result := not (RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',
    'Installed', Instalado) and (Instalado = 1));
end;
