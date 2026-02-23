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

[Code]
var
  ConfigPage: TWizardPage;
  DbHostEdit: TNewEdit;
  DbPortEdit: TNewEdit;
  DbNameEdit: TNewEdit;
  ApiBaseUrlEdit: TNewEdit;
  ApiUserEdit: TNewEdit;
  ApiPasswordEdit: TNewEdit;
  ApiVerifyTlsCheck: TNewCheckBox;

function JsonEscape(const S: string): string;
begin
  Result := S;
  StringChangeEx(Result, '\', '\\', True);
  StringChangeEx(Result, '"', '\"', True);
end;

procedure AddField(const ParentPage: TWizardPage; const CaptionText: string; var EditBox: TNewEdit; var TopPos: Integer; const DefaultValue: string);
var
  LabelCtrl: TNewStaticText;
begin
  LabelCtrl := TNewStaticText.Create(ParentPage);
  LabelCtrl.Parent := ParentPage.Surface;
  LabelCtrl.Caption := CaptionText;
  LabelCtrl.Left := ScaleX(0);
  LabelCtrl.Top := TopPos;

  EditBox := TNewEdit.Create(ParentPage);
  EditBox.Parent := ParentPage.Surface;
  EditBox.Left := ScaleX(0);
  EditBox.Top := TopPos + ScaleY(16);
  EditBox.Width := ScaleX(420);
  EditBox.Text := DefaultValue;

  TopPos := EditBox.Top + EditBox.Height + ScaleY(10);
end;

procedure InitializeWizard;
var
  TopPos: Integer;
  InfoLabel: TNewStaticText;
begin
  ConfigPage := CreateCustomPage(
    wpSelectTasks,
    'Application Configuration',
    'Configure API/DB defaults for first run'
  );

  TopPos := ScaleY(0);

  InfoLabel := TNewStaticText.Create(ConfigPage);
  InfoLabel.Parent := ConfigPage.Surface;
  InfoLabel.Caption := 'These values are written only if app_settings.json does not already exist in the install folder.';
  InfoLabel.Left := ScaleX(0);
  InfoLabel.Top := TopPos;
  TopPos := TopPos + ScaleY(28);

  AddField(ConfigPage, 'Database host', DbHostEdit, TopPos, 'localhost');
  AddField(ConfigPage, 'Database port', DbPortEdit, TopPos, '5432');
  AddField(ConfigPage, 'Database name', DbNameEdit, TopPos, 'cloudvienna');
  AddField(ConfigPage, 'API base URL', ApiBaseUrlEdit, TopPos, 'http://127.0.0.1:8000');
  AddField(ConfigPage, 'API username', ApiUserEdit, TopPos, 'admin');
  AddField(ConfigPage, 'API password', ApiPasswordEdit, TopPos, '');
  ApiPasswordEdit.Password := True;

  ApiVerifyTlsCheck := TNewCheckBox.Create(ConfigPage);
  ApiVerifyTlsCheck.Parent := ConfigPage.Surface;
  ApiVerifyTlsCheck.Left := ScaleX(0);
  ApiVerifyTlsCheck.Top := TopPos + ScaleY(4);
  ApiVerifyTlsCheck.Caption := 'Verify TLS certificates (enable for HTTPS with trusted certs)';
  ApiVerifyTlsCheck.Checked := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  PortValue: Integer;
begin
  Result := True;
  if CurPageID = ConfigPage.ID then
  begin
    if Trim(DbHostEdit.Text) = '' then
    begin
      MsgBox('Database host is required.', mbError, MB_OK);
      Result := False;
      exit;
    end;
    if Trim(DbPortEdit.Text) = '' then
    begin
      MsgBox('Database port is required.', mbError, MB_OK);
      Result := False;
      exit;
    end;
    PortValue := StrToIntDef(Trim(DbPortEdit.Text), -1);
    if PortValue <= 0 then
    begin
      MsgBox('Database port must be a positive integer.', mbError, MB_OK);
      Result := False;
      exit;
    end;
    if Trim(DbNameEdit.Text) = '' then
    begin
      MsgBox('Database name is required.', mbError, MB_OK);
      Result := False;
      exit;
    end;
    if Trim(ApiBaseUrlEdit.Text) = '' then
    begin
      MsgBox('API base URL is required.', mbError, MB_OK);
      Result := False;
      exit;
    end;
    if Trim(ApiUserEdit.Text) = '' then
    begin
      MsgBox('API username is required.', mbError, MB_OK);
      Result := False;
      exit;
    end;
    if Trim(ApiPasswordEdit.Text) = '' then
    begin
      MsgBox('API password is required.', mbError, MB_OK);
      Result := False;
      exit;
    end;
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if (ConfigPage <> nil) and (PageID = ConfigPage.ID) then
    Result := FileExists(ExpandConstant('{app}\app_settings.json'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  SettingsPath: string;
  VerifyTlsText: string;
  JsonText: string;
begin
  if CurStep <> ssPostInstall then
    exit;

  SettingsPath := ExpandConstant('{app}\app_settings.json');
  if FileExists(SettingsPath) then
  begin
    Log('app_settings.json already exists. Preserving existing configuration.');
    exit;
  end;

  if ApiVerifyTlsCheck.Checked then
    VerifyTlsText := 'true'
  else
    VerifyTlsText := 'false';

  JsonText :=
    '{' + #13#10 +
    '  "api": {' + #13#10 +
    '    "base_url": "' + JsonEscape(Trim(ApiBaseUrlEdit.Text)) + '",' + #13#10 +
    '    "username": "' + JsonEscape(Trim(ApiUserEdit.Text)) + '",' + #13#10 +
    '    "password": "' + JsonEscape(ApiPasswordEdit.Text) + '",' + #13#10 +
    '    "verify_tls": ' + VerifyTlsText + #13#10 +
    '  },' + #13#10 +
    '  "db": {' + #13#10 +
    '    "host": "' + JsonEscape(Trim(DbHostEdit.Text)) + '",' + #13#10 +
    '    "name": "' + JsonEscape(Trim(DbNameEdit.Text)) + '",' + #13#10 +
    '    "port": ' + Trim(DbPortEdit.Text) + ',' + #13#10 +
    '    "sslmode": "prefer"' + #13#10 +
    '  },' + #13#10 +
    '  "language": "en"' + #13#10 +
    '}' + #13#10;

  if not SaveStringToFile(SettingsPath, JsonText, False) then
    MsgBox('Could not write app_settings.json to install folder.', mbError, MB_OK);
end;
