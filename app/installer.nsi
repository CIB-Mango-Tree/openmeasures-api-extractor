!include "MUI2.nsh"

; Parameters passed from command line
!ifndef INPUT_DIR
  !define INPUT_DIR "dist"
!endif

!ifndef OUTPUT_FILE
  !define OUTPUT_FILE "dist\mango-tree-api-extractor-windows-installer.exe"
!endif

Name "Mango Tree API Extractor"
OutFile "app\dist\mango-tree-api-extractor-windows-installer.exe"
InstallDir "$PROGRAMFILES\mango-tree-api-extractor"
RequestExecutionLevel user

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Include both executables from the temp directory
    File "${INPUT_DIR}\mango-tree-api-extractor.exe"
    File "${INPUT_DIR}\mango-tree-api-extractor-backend.exe"
    
    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\Mango Tree API Extractor"
    CreateShortcut "$SMPROGRAMS\Mango Tree API Extractor\Mango Tree API Extractor.lnk" "$INSTDIR\mango-tree-api-extractor.exe"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Add to Add/Remove Programs
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MangoTreeExtractor" "DisplayName" "Mango Tree API Extractor"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MangoTreeExtractor" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MangoTreeExtractor" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MangoTreeExtractor" "Publisher" "CIB Mango Tree"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\mango-tree-api-extractor.exe"
  Delete "$INSTDIR\mango-tree-api-extractor-backend.exe"
  Delete "$INSTDIR\uninstall.exe"
  RMDir "$INSTDIR"
  
  Delete "$SMPROGRAMS\Mango Tree API Extractor\Mango Tree API Extractor.lnk"
  RMDir "$SMPROGRAMS\Mango Tree API Extractor"
  
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MangoTreeExtractor"
SectionEnd
