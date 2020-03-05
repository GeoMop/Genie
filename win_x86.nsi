# Genie nsi build script for Windows x86_64 platform
# 
#--------------------------------


# Maximum compression.
SetCompressor /SOLID lzma


# installation only for current user
!define MULTIUSER_EXECUTIONLEVEL Standard
!define MULTIUSER_INSTALLMODE_INSTDIR "Genie"
!include MultiUser.nsh

# Define directories.
!define GIT_DIR "."
!define SRC_DIR "${GIT_DIR}\src"
!define BUILD_DIR "${GIT_DIR}\build\win_x86"
#!define DATA_DIR "${GIT_DIR}\data"

!define PYTHON_MAJOR   "3"
!define PYTHON_MINOR   "7"

# The following are derived from the above.
!define PYTHON_VERS    "${PYTHON_MAJOR}.${PYTHON_MINOR}"
!define PYTHON_HK      "Software\Python\PythonCore\${PYTHON_VERS}\InstallPath"
!define PYTHON_HK_64   "Software\Wow6432Node\Python\PythonCore\${PYTHON_VERS}\InstallPath"


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

Var PYTHON_EXE
Var PYTHON_SCRIPTS

Function .onInit

  !insertmacro MULTIUSER_INIT

  !define APP_HOME_DIR "$APPDATA\Genie"

  CheckPython:
    # Check if Python is installed.
    ReadRegStr $PYTHON_EXE HKCU "${PYTHON_HK}" ""

    ${If} $PYTHON_EXE == ""
        ReadRegStr $PYTHON_EXE HKLM "${PYTHON_HK}" ""
    ${Endif}

    # Install Python.
    ${If} $PYTHON_EXE == ""
      MessageBox MB_YESNO|MB_ICONQUESTION "Python ${PYTHON_VERS} 64b is not installed. Do you wish to install it?" IDYES InstallPython
                  Abort
      InstallPython:
        SetOutPath $INSTDIR\prerequisites
        File "${BUILD_DIR}\python-3.7.6-amd64.exe"
        ExecWait 'python-3.7.6-amd64.exe'

        # Check installation.
        Goto CheckPython
    ${Endif}

    # Set the path to the python.exe instead of directory.
    StrCpy $PYTHON_EXE "$PYTHON_EXEpython.exe"

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

  # Install virtualenv.
  SetOutPath $INSTDIR\prerequisites
  File "${BUILD_DIR}\virtualenv-16.1.0-py2.py3-none-any.whl"
  ExecWait '"$PYTHON_EXE" -m pip install "$INSTDIR\prerequisites\virtualenv-16.1.0-py2.py3-none-any.whl"'
  ExecWait '"$PYTHON_EXE" -m virtualenv "$INSTDIR\env"'

  # Copy PyQt5 and other Python packages.
  SetOutPath $INSTDIR
  #File /r "${BUILD_DIR}\env"

  # Copy the gm_base folder.
  #File /r /x *~ /x __pycache__ /x pylintrc /x *.pyc "${SRC_DIR}\gm_base"

  # Copy LICENSE, CHANGELOG, VERSION.
  File "${GIT_DIR}\VERSION"
  #File "${GIT_DIR}\CHANGELOG.md"
  File "${GIT_DIR}\LICENSE"

  # Copy documentation
  #SetOutPath $INSTDIR\doc
  #File "${BUILD_DIR}\Genie 1.1.0 reference guide.pdf"

  # Set the varible with path to python virtual environment scripts.
  StrCpy $PYTHON_SCRIPTS "$INSTDIR\env\Scripts"

  # Install PyQt5.
  SetOutPath $INSTDIR\prerequisites
  File "${BUILD_DIR}\PyQt5_sip-12.7.1-cp37-cp37m-win_amd64.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\PyQt5_sip-12.7.1-cp37-cp37m-win_amd64.whl"'
  File "${BUILD_DIR}\PyQt5-5.14.1-5.14.1-cp35.cp36.cp37.cp38-none-win_amd64.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\PyQt5-5.14.1-5.14.1-cp35.cp36.cp37.cp38-none-win_amd64.whl"'

  # Install NumPy.
  SetOutPath $INSTDIR\prerequisites
  File "${BUILD_DIR}\numpy-1.18.1-cp37-cp37m-win_amd64.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\numpy-1.18.1-cp37-cp37m-win_amd64.whl"'

  # Install attrs.
  SetOutPath $INSTDIR\prerequisites
  File "${BUILD_DIR}\attrs-19.3.0-py2.py3-none-any.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\attrs-19.3.0-py2.py3-none-any.whl"'

  # Install pandas.
  SetOutPath $INSTDIR\prerequisites
  File "${BUILD_DIR}\six-1.14.0-py2.py3-none-any.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\six-1.14.0-py2.py3-none-any.whl"'
  File "${BUILD_DIR}\pytz-2019.3-py2.py3-none-any.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\pytz-2019.3-py2.py3-none-any.whl"'
  File "${BUILD_DIR}\python_dateutil-2.8.1-py2.py3-none-any.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\python_dateutil-2.8.1-py2.py3-none-any.whl"'
  File "${BUILD_DIR}\pandas-1.0.1-cp37-cp37m-win_amd64.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\pandas-1.0.1-cp37-cp37m-win_amd64.whl"'
  File "${BUILD_DIR}\xlrd-1.2.0-py2.py3-none-any.whl"
  ExecWait '"$PYTHON_SCRIPTS\python.exe" -m pip install "$INSTDIR\prerequisites\xlrd-1.2.0-py2.py3-none-any.whl"'

SectionEnd


Section "XLSReader" SecXLSReader

  # Section is mandatory.
  SectionIn RO

  #RMDir /r "$INSTDIR\xlsreader"
  #SetOutPath $INSTDIR\xlsreader
  #File /r /x *~ /x __pycache__ /x pylintrc /x *.pyc "${SRC_DIR}\xlsreader\*"
  RMDir /r "$INSTDIR\xlsreader"
  SetOutPath $INSTDIR
  File /r /x *~ /x __pycache__ /x pylintrc /x *.pyc "${SRC_DIR}\xlsreader"

SectionEnd


Section "-Batch files" SecBatchFiles

  CreateDirectory "$INSTDIR\bin"
  SetOutPath $INSTDIR\bin

  IfFileExists "$INSTDIR\xlsreader\xls_reader.py" 0 +6
    FileOpen $0 "xls_reader.bat" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 'set "PYTHONPATH=$INSTDIR"$\r$\n'
    FileWrite $0 '"$PYTHON_SCRIPTS\python.exe" "$INSTDIR\xlsreader\xls_reader.py" %*$\r$\n'
    FileClose $0

  FileOpen $0 "pythonw.bat" w
  FileWrite $0 "@echo off$\r$\n"
  FileWrite $0 'set "PYTHONPATH=$INSTDIR"$\r$\n'
  FileWrite $0 'start "" "$PYTHON_SCRIPTS\pythonw.exe" %*$\r$\n'
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

  IfFileExists "$INSTDIR\xlsreader\xls_reader.py" 0 +3
    SetOutPath $INSTDIR\xlsreader
    CreateShortcut "$SMPROGRAMS\Genie\XLSReader.lnk" "$INSTDIR\bin\pythonw.bat" '"$INSTDIR\xlsreader\xls_reader.py"' "$INSTDIR\gm_base\resources\icons\ico\geomap.ico" 0

SectionEnd


Section "Desktop icons" SecDesktopIcons

  IfFileExists "$INSTDIR\xlsreader\xls_reader.py" 0 +3
    SetOutPath $INSTDIR\xlsreader
    CreateShortCut "$DESKTOP\XLSReader.lnk" "$INSTDIR\bin\pythonw.bat" '"$INSTDIR\xlsreader\xls_reader.py"'

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
"The runtime environment for Genie - Python 3.7 with PyQt5."
!insertmacro MUI_DESCRIPTION_TEXT ${SecXLSReader} \
"The reader for Excel files."
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
  Delete "$DESKTOP\XLSReader.lnk"

  # Remove start menu shortcuts.
  RMDir /r "$SMPROGRAMS\Genie"

  # Remove Genie installation directory and all files within.
  RMDir /r "$INSTDIR"

SectionEnd
