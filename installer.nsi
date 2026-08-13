; Windows installer for the CIB Mango Tree API Extractor.
;
; The application is a PyInstaller onedir build: a launcher exe plus an _internal directory of
; dependencies. The whole tree is installed recursively -- installing only the exe would produce
; something that cannot start.

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Directory holding the PyInstaller onedir output (the folder containing the .exe).
!ifndef INPUT_DIR
  !define INPUT_DIR "api\dist\mango-tree-api-extractor"
!endif

; NSIS resolves a relative OutFile against the directory holding this .nsi file, not the working
; directory makensis was invoked from. The workflow passes an absolute path.
!ifndef OUTPUT_FILE
  !define OUTPUT_FILE "api\dist\mango-tree-api-extractor-windows-installer.exe"
!endif

!ifndef APP_VERSION
  !define APP_VERSION "0.0.0"
!endif

!define APP_NAME "CIB Mango Tree API Extractor"
!define APP_EXE "mango-tree-api-extractor.exe"
!define PUBLISHER "CIB Mango Tree"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\MangoTreeExtractor"

Name "${APP_NAME}"
OutFile "${OUTPUT_FILE}"
; PROGRAMFILES64: the application is 64-bit, and plain $PROGRAMFILES resolves to the 32-bit
; directory on 64-bit Windows.
InstallDir "$PROGRAMFILES64\${APP_NAME}"
; Remember where a previous install went so upgrades land in the same place.
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"
; Writing to Program Files and HKLM needs elevation; with "user" the install silently fails or
; gets redirected into VirtualStore.
RequestExecutionLevel admin
Unicode true

!define MUI_ICON "api\icon.ico"
!define MUI_UNICON "api\icon.ico"
!define MUI_ABORTWARNING

; Deliberately no MUI_FINISHPAGE_RUN. The installer runs elevated, and anything it launches
; inherits that token -- the app would then resolve %APPDATA% to the administrator's profile and
; write the database and extracted datasets to the wrong user. Launching from the shortcuts runs
; it as the actual user. Doing this safely from the finish page needs the UAC plugin.
!define MUI_FINISHPAGE_LINK "CIB Mango Tree"
!define MUI_FINISHPAGE_LINK_LOCATION "https://cibmangotree.org"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    ; Shortcuts and registry entries go machine-wide, matching the Program Files install.
    SetShellVarContext all
    SetOutPath "$INSTDIR"

    ; /r: the onedir build is a tree (the exe plus _internal), not a pair of files.
    File /r "${INPUT_DIR}\*"

    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe"
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Populates Add/Remove Programs. EstimatedSize is in KB and is what Windows shows as the
    ; install footprint.
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0

    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE},0"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "${UNINSTALL_KEY}" "QuietUninstallString" '"$INSTDIR\uninstall.exe" /S'
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "EstimatedSize" "$0"
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
    SetShellVarContext all

    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"

    ; /r because the install is a directory tree. The user's extracted data lives in %APPDATA%
    ; and is deliberately left alone.
    RMDir /r "$INSTDIR"

    DeleteRegKey HKLM "${UNINSTALL_KEY}"
SectionEnd
