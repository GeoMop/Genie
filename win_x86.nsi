# Genie nsi build script for Windows x86_64 platform
# 
#--------------------------------


# Unicode target
Unicode True

# Maximum compression.
#SetCompressor /SOLID lzma # not working for very large installers
SetCompressor lzma

#faster compression
#SetCompressor /SOLID zlib

# installation only for current user
!define MULTIUSER_EXECUTIONLEVEL Standard
!define MULTIUSER_INSTALLMODE_INSTDIR "Genie"
!include MultiUser.nsh

# Define directories.
!define GIT_DIR "."
!define SRC_DIR "${GIT_DIR}\src"
!define BUILD_DIR "${GIT_DIR}\build\win_x86"
#!define DATA_DIR "${GIT_DIR}\data"


# Include the tools we use.
!include MUI2.nsh
!include LogicLib.nsh


# Read version information from file.
!searchparse /file "${GIT_DIR}\VERSION" '' VERSION ''


Name "Genie ${VERSION}"
Caption "Genie ${VERSION} Setup"
#InstallDir "$PROGRAMFILES\GeoMop"
OutFile "${GIT_DIR}\dist\genie_${VERSION}_x86_64.exe"

# Registry key to check for directory (so if you install again, it will 
# overwrite the old one automatically)
InstallDirRegKey HKCU "Software\Genie" "Install_Dir"

# Request application privileges for Windows Vista and newer
#RequestExecutionLevel admin

#--------------------------------

# Define the different pages.
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${GIT_DIR}\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

# Other settings.
!insertmacro MUI_LANGUAGE "English"

#--------------------------------
# Init

Var CONDA_ENV

Function .onInit

  !insertmacro MULTIUSER_INIT

  !define APP_HOME_DIR "$APPDATA\Genie"

FunctionEnd

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
FunctionEnd

#--------------------------------
# The stuff to install

# These are the programs that are needed by Genie.
Section "Runtime Environment" SecRuntime
  
  # Section is mandatory.
  SectionIn RO

  # Clean GeoMop source, env directories.
  RMDir /r "$INSTDIR\env"
  #RMDir /r "$INSTDIR\gm_base"

  # Install conda environment.
  SetOutPath $INSTDIR
  File /r "${BUILD_DIR}\env"

  # Copy the gm_base folder.
  #File /r /x *~ /x __pycache__ /x pylintrc /x *.pyc "${SRC_DIR}\gm_base"

  # Copy LICENSE, CHANGELOG, VERSION.
  File "${GIT_DIR}\VERSION"
  #File "${GIT_DIR}\CHANGELOG.md"
  File "${GIT_DIR}\LICENSE"

  # Copy documentation
  RMDir /r "$INSTDIR\doc"
  SetOutPath $INSTDIR\doc
  File /r "${GIT_DIR}\doc\*"

  # Set the varible with path to conda environment.
  StrCpy $CONDA_ENV "$INSTDIR\env"

  # Install gmsh.
  SetOutPath $INSTDIR
  File /r "${BUILD_DIR}\gmsh"

SectionEnd


Section "Genie" SecGenie

  # Section is mandatory.
  SectionIn RO

  RMDir /r "$INSTDIR\genie"
  SetOutPath $INSTDIR
  File /r /x *~ /x __pycache__ /x pylintrc /x *.pyc "${SRC_DIR}\genie"

  #RMDir /r "$INSTDIR\data"
  #SetOutPath $INSTDIR\data
  #File /r /x *~ /x __pycache__ /x pylintrc /x *.pyc "${GIT_DIR}\data\*"

  #RMDir /r "$INSTDIR\projects"
  #SetOutPath $INSTDIR\projects
  #File /r /x *~ /x __pycache__ /x pylintrc /x *.pyc "${GIT_DIR}\projects\*"

SectionEnd


Section "-Batch files" SecBatchFiles

  CreateDirectory "$INSTDIR\bin"
  SetOutPath $INSTDIR\bin

  IfFileExists "$INSTDIR\genie\genie_ert.py" 0 +7
    FileOpen $0 "genie_ert.bat" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 'call "$CONDA_ENV\Scripts\activate.bat"$\r$\n'
    FileWrite $0 'set "PYTHONPATH=$INSTDIR"$\r$\n'
    FileWrite $0 '"$CONDA_ENV\python.exe" "$INSTDIR\genie\genie_ert.py" %*$\r$\n'
    FileClose $0

  IfFileExists "$INSTDIR\genie\genie_st.py" 0 +7
    FileOpen $0 "genie_st.bat" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 'call "$CONDA_ENV\Scripts\activate.bat"$\r$\n'
    FileWrite $0 'set "PYTHONPATH=$INSTDIR"$\r$\n'
    FileWrite $0 '"$CONDA_ENV\python.exe" "$INSTDIR\genie\genie_st.py" %*$\r$\n'
    FileClose $0

  FileOpen $0 "pythonw.bat" w
  FileWrite $0 "@echo off$\r$\n"
  FileWrite $0 'call "$CONDA_ENV\Scripts\activate.bat"$\r$\n'
  FileWrite $0 'set "PYTHONPATH=$INSTDIR"$\r$\n'
  FileWrite $0 'start "" "$CONDA_ENV\pythonw.exe" %*$\r$\n'
  FileClose $0

SectionEnd


Section "Start Menu shortcuts" SecStartShortcuts

  CreateDirectory "$SMPROGRAMS\Genie"

  # Make sure this is clean and tidy.
  RMDir /r "$SMPROGRAMS\Genie"
  CreateDirectory "$SMPROGRAMS\Genie"
  
  # Uninstall shortcut.
  SetOutPath $INSTDIR
  CreateShortcut "$SMPROGRAMS\Genie\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

  IfFileExists "$INSTDIR\genie\genie_ert.py" 0 +3
    SetOutPath $INSTDIR\genie
    CreateShortcut "$SMPROGRAMS\Genie\GenieERT.lnk" "$INSTDIR\bin\pythonw.bat" '"$INSTDIR\genie\genie_ert.py"' "$INSTDIR\genie\icons\genie_ert_128.ico" 0

  IfFileExists "$INSTDIR\genie\genie_st.py" 0 +3
    SetOutPath $INSTDIR\genie
    CreateShortcut "$SMPROGRAMS\Genie\GenieST.lnk" "$INSTDIR\bin\pythonw.bat" '"$INSTDIR\genie\genie_st.py"' "$INSTDIR\genie\icons\genie_st_128.ico" 0

SectionEnd


Section "Desktop icons" SecDesktopIcons

  IfFileExists "$INSTDIR\genie\genie_ert.py" 0 +3
    SetOutPath $INSTDIR\genie
    CreateShortCut "$DESKTOP\GenieERT.lnk" "$INSTDIR\bin\pythonw.bat" '"$INSTDIR\genie\genie_ert.py"' "$INSTDIR\genie\icons\genie_ert_128.ico" 0

  IfFileExists "$INSTDIR\genie\genie_st.py" 0 +3
    SetOutPath $INSTDIR\genie
    CreateShortCut "$DESKTOP\GenieST.lnk" "$INSTDIR\bin\pythonw.bat" '"$INSTDIR\genie\genie_st.py"' "$INSTDIR\genie\icons\genie_st_128.ico" 0

SectionEnd


Section /o "Wipe settings" SecWipeSettings

  # Clear all configuration from APPDATA
  RMDir /r "${APP_HOME_DIR}"

SectionEnd


Section "-Default resources data" SecDefaultResourcesData

  # Section is mandatory.
  SectionIn RO

  IfFileExists "${APP_HOME_DIR}" +2 0
    CreateDirectory "${APP_HOME_DIR}"
    # fill data home to default resources data
    #SetOutPath "${APP_HOME_DIR}"
    #File /r "${DATA_DIR}/*"

SectionEnd


Section -post
 
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  WriteUninstaller "uninstall.exe"

  ; Write the installation path into the registry
  WriteRegStr HKCU SOFTWARE\Genie "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Genie" "DisplayName" "Genie"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Genie" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Genie" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Genie" "NoRepair" 1
  
SectionEnd


# Section description text.
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecRuntime} \
"The runtime environment for Genie."
!insertmacro MUI_DESCRIPTION_TEXT ${SecGenie} \
"Genie application."
!insertmacro MUI_DESCRIPTION_TEXT ${SecBatchFiles} \
"This adds batch files to bin directory."
!insertmacro MUI_DESCRIPTION_TEXT ${SecStartShortcuts} \
"This adds shortcuts to your Start Menu."
!insertmacro MUI_DESCRIPTION_TEXT ${SecDesktopIcons} \
"This creates icons on your Desktop."
!insertmacro MUI_DESCRIPTION_TEXT ${SecWipeSettings} \
"Deletes all user settings. Check this option if you're experiencing issues with launching the applications."
!insertmacro MUI_DESCRIPTION_TEXT ${SecDefaultResourcesData} \
"If user data don't exist, create default resources data."
!insertmacro MUI_FUNCTION_DESCRIPTION_END


# Uninstaller
Section "Uninstall"
  
  # Remove registry keys
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Genie"
  DeleteRegKey HKCU SOFTWARE\Genie

  # Delete desktop icons.
  Delete "$DESKTOP\GenieERT.lnk"
  Delete "$DESKTOP\GenieST.lnk"

  # Remove start menu shortcuts.
  RMDir /r "$SMPROGRAMS\Genie"

  # Remove Genie installation directory and all files within.
  RMDir /r "$INSTDIR"

SectionEnd
