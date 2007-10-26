Name "Orange"
Icon OrangeInstall.ico
UninstallIcon OrangeInstall.ico

!ifndef ORANGEDIR
	!define ORANGEDIR orange
!endif

!define PYFILENAME python-${NPYVER}.msi
!define PYWINFILENAME pywin32-210.win32-py${NPYVER}.exe

OutFile ${OUTFILENAME}

!include "LogicLib.nsh"



licensedata license.txt
licensetext "Acknowledgments and License Agreement"

AutoCloseWindow true
ShowInstDetails nevershow

Var PythonDir
Var WhatsDownFile
Var AdminInstall
Var MissingModules

Page license
Page instfiles

!define SHELLFOLDERS \
  "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
 


Section Uninstall
	MessageBox MB_YESNO "Are you sure you want to remove Orange?$\r$\n$\r$\nThis won't remove any 3rd party software possibly installed with Orange, such as Python or Qt,$\r$\n$\r$\nbut make sure you have not left any of your files in Orange's directories!" /SD IDYES IDNO abort
	RmDir /R "$INSTDIR"
	${If} $AdminInstall = 0
	    SetShellVarContext all
	${Else}
	    SetShellVarContext current	   
	${Endif}
	RmDir /R "$SMPROGRAMS\Orange"

	ReadRegStr $0 HKCU "${SHELLFOLDERS}" AppData
	StrCmp $0 "" 0 +2
	  ReadRegStr $0 HKLM "${SHELLFOLDERS}" "Common AppData"
	StrCmp $0 "" +2 0
	  RmDir /R "$0\Orange"
	
	ReadRegStr $PythonDir HKLM Software\Python\PythonCore\${NPYVER}\InstallPath ""
	${If} $PythonDir != ""
		DeleteRegKey HKLM "SOFTWARE\Python\PythonCore\${NPYVER}\PythonPath\Orange"
		DeleteRegKey HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Orange"
	${Else}
		DeleteRegKey HKCU "SOFTWARE\Python\PythonCore\${NPYVER}\PythonPath\Orange"
		DeleteRegKey HKCU "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Orange"
	${Endif}
	
	Delete "$DESKTOP\Orange Canvas.lnk"

	DeleteRegKey HKEY_CLASSES_ROOT ".ows"
	DeleteRegKey HKEY_CLASSES_ROOT "OrangeCanvas"

	MessageBox MB_OK "Orange has been succesfully removed from your system.$\r$\nPython and other applications need to be removed separately.$\r$\n$\r$\nYou may now continue without rebooting your machine." /SD IDOK
  abort:
SectionEnd


!macro WarnMissingModule FILE MODULE
	${Unless} ${FileExists} ${FILE}
		${If} $MissingModules == ""
			StrCpy $MissingModules ${MODULE}
		${Else}
			StrCpy $MissingModules "$MissingModules, ${MODULE}"
		${EndIf}
	${EndUnless}
!macroend

!macro GetPythonDir
    ${If} $AdminInstall == 0
	    ReadRegStr $PythonDir HKCU Software\Python\PythonCore\${NPYVER}\InstallPath ""
		StrCmp $PythonDir "" 0 trim_backslash
		ReadRegStr $PythonDir HKLM Software\Python\PythonCore\${NPYVER}\InstallPath ""
		StrCmp $PythonDir "" return
		MessageBox MB_OK "Please ask the administrator to install Orange$\r$\n(this is because Python was installed by him, too)."
		Quit
	${Else}
	    ReadRegStr $PythonDir HKLM Software\Python\PythonCore\${NPYVER}\InstallPath ""
		StrCmp $PythonDir "" 0 trim_backslash
		ReadRegStr $PythonDir HKCU Software\Python\PythonCore\${NPYVER}\InstallPath ""
		StrCmp $PythonDir "" return
		StrCpy $AdminInstall 0
	${EndIf}

	trim_backslash:
	StrCpy $0 $PythonDir "" -1
    ${If} $0 == "\"
        StrLen $0 $PythonDir
        IntOp $0 $0 - 1
        StrCpy $PythonDir $PythonDir $0 0
    ${EndIf}

	return:
!macroend
		


!ifdef COMPLETE

!if ${PYVER} == 23
	!define MFC mfc42.dll
!else
	!define MFC mfc71.dll
!endif

Section ""
		StrCmp $PythonDir "" 0 have_python
		MessageBox MB_OKCANCEL "Orange installer will first launch installation of Python ${NPYVER}$\r$\nOrange installation will continue after you finish installing Python." /SD IDOK IDOK installpython
			MessageBox MB_YESNO "Orange cannot run without Python.$\r$\nAbort the installation?" IDNO installpython
				Quit
		installpython:

		SetOutPath $DESKTOP
		!if ${PYVER} == 23
			File 3rdparty-23\Python-2.3.5.exe
			ExecWait "$DESKTOP\Python-2.3.5.exe"
			Delete "$DESKTOP\Python-2.3.5.exe"
		!else
			File 3rdparty-${PYVER}\${PYFILENAME}
			${If} $AdminInstall == 1
				ExecWait 'msiexec.exe /i "$DESKTOP\${PYFILENAME}" ADDLOCAL=Extensions,Documentation ALLUSERS=1 /Qb-' $0
			${Else}
				ExecWait 'msiexec.exe /i "$DESKTOP\${PYFILENAME}" ADDLOCAL=Extensions,Documentation /Qb-' $0
			${EndIf}
			Delete "$DESKTOP\${PYFILENAME}"
		!endif

		!insertMacro GetPythonDir
		StrCmp $PythonDir "" 0 have_python
			MessageBox MB_OK "Python installation failed.$\r$\nOrange installation cannot continue."
			Quit
		have_python:


		IfFileExists $PythonDir\lib\site-packages\PythonWin have_pythonwin
			MessageBox MB_YESNO "Do you want to install PythonWin (recommended)?$\r$\n(Orange installation will continue afterwards.)" /SD IDYES IDNO have_pythonwin
			IfFileExists "$SysDir\${MFC}" have_mfc
				SetOutPath $SysDir
				File various\${MFC}
			have_mfc:
			SetOutPath $DESKTOP
			File 3rdparty-${PYVER}\${PYWINFILENAME}
			ExecWait "$DESKTOP\${PYWINFILENAME}"
			Delete "$DESKTOP\${PYWINFILENAME}"
		have_pythonwin:


		SetOutPath $PythonDir\lib\site-packages
		IfFileExists $PythonDir\lib\site-packages\qt.py have_pyqt
			File /r 3rdparty-${PYVER}\pyqt\*.*
		have_pyqt:


		IfFileExists $PythonDir\lib\site-packages\qwt\*.* have_pyqwt
			File /r 3rdparty-${PYVER}\qwt
		have_pyqwt:


		IfFileExists $PythonDir\lib\site-packages\Numeric\*.* have_numeric
			File /r 3rdparty-${PYVER}\numeric
			File various\Numeric.pth
        have_numeric:


		IfFileExists "$PythonDir\lib\site-packages\qt-mt230nc.dll" have_qt
		IfFileExists "$SysDir\qt-mt230nc.dll" have_qt
			File various\qt-mt230nc.dll
			SetOutPath $INSTDIR
			File various\QT-LICENSE.txt
		have_qt:

SectionEnd
!endif


Section ""
	ReadRegStr $0 HKCU "${SHELLFOLDERS}" AppData
	StrCmp $0 "" 0 +2
	  ReadRegStr $0 HKLM "${SHELLFOLDERS}" "Common AppData"
	StrCmp $0 "" not_installed_before 0

	IfFileExists "$0\Orange" 0 not_installed_before
		ask_remove_old:
		MessageBox MB_YESNOCANCEL "Another version of Orange has been found on the computer.$\r$\nDo you want to keep the existing settings for canvas and widgets?$\r$\n$\r$\nYou can usually safely answer 'Yes'; in case of problems, re-run this installation." /SD IDYES IDYES not_installed_before IDNO remove_old_settings
			MessageBox MB_YESNO "Abort the installation?" IDNO ask_remove_old
				Quit

		remove_old_settings:
		RmDir /R "$0\Orange"

	not_installed_before:

	StrCpy $INSTDIR  "$PythonDir\lib\site-packages\orange"
	SetOutPath $INSTDIR
	File "license.txt"

	FileOpen $WhatsDownFile $INSTDIR\whatsdown.txt w
    
	!include ${INCLUDEPREFIX}_base.inc
	!include ${INCLUDEPREFIX}_binaries.inc
	!include ${INCLUDEPREFIX}_widgets.inc
	!include ${INCLUDEPREFIX}_canvas.inc

	SetOutPath $INSTDIR\icons
	File Orange.ico
	SetOutPath $INSTDIR\OrangeCanvas\icons
	File OrangeOWS.ico

   	!include ${INCLUDEPREFIX}_doc.inc

	SetOutPath $INSTDIR\doc
	File "various\Orange White Paper.pdf"
	File "various\Orange Widgets White Paper.pdf"

	SetOutPath $INSTDIR\doc\datasets
	File ${ORANGEDIR}\doc\datasets\*

	!ifdef INCLUDEGENOMICS
		!include ${INCLUDEPREFIX}_genomics.inc
	    
		SetOutPath $INSTDIR\doc
		File "various\Orange Genomics.pdf"
	
		SetOutPath $INSTDIR
		CreateDirectory "$SMPROGRAMS\Orange"
		CreateShortCut "$SMPROGRAMS\Orange\Orange Widgets For Functional Genomics.lnk" "$INSTDIR\doc\Orange Genomics.pdf"
	
		SetOutPath "$INSTDIR\OrangeCanvas"
		File various\bi-visprog\*.tab
		File various\bi-visprog\*.ows
	!endif

	!ifdef INCLUDETEXTMINING
		SetOutPath $PythonDir\lib\site-packages
		File E:\orange\download\snapshot\${PYVER}\lib\site-packages\orngText.pth
		File /r E:\orange\download\snapshot\${PYVER}\lib\site-packages\orngText

	!endif

	CreateDirectory "$SMPROGRAMS\Orange"
	CreateShortCut "$SMPROGRAMS\Orange\Orange White Paper.lnk" "$INSTDIR\doc\Orange White Paper.pdf"
	CreateShortCut "$SMPROGRAMS\Orange\Orange Widgets White Paper.lnk" "$INSTDIR\doc\Orange Widgets White Paper.pdf"
	CreateShortCut "$SMPROGRAMS\Orange\Orange for Beginners.lnk" "$INSTDIR\doc\ofb\default.htm"
	CreateShortCut "$SMPROGRAMS\Orange\Orange Modules Reference.lnk" "$INSTDIR\doc\modules\default.htm"
	CreateShortCut "$SMPROGRAMS\Orange\Orange Reference Guide.lnk" "$INSTDIR\doc\reference\default.htm"

	CreateShortCut "$SMPROGRAMS\Orange\Orange.lnk" "$INSTDIR\"
	CreateShortCut "$SMPROGRAMS\Orange\Uninstall Orange.lnk" "$INSTDIR\uninst.exe"

	SetOutPath $INSTDIR\OrangeCanvas
	CreateShortCut "$DESKTOP\Orange Canvas.lnk" "$INSTDIR\OrangeCanvas\orngCanvas.pyw" "" $INSTDIR\icons\Orange.ico 0
	CreateShortCut "$SMPROGRAMS\Orange\Orange Canvas.lnk" "$INSTDIR\OrangeCanvas\orngCanvas.pyw" "" $INSTDIR\icons\Orange.ico 0

	WriteRegStr SHELL_CONTEXT "SOFTWARE\Python\PythonCore\${NPYVER}\PythonPath\Orange" "" "$INSTDIR;$INSTDIR\OrangeWidgets;$INSTDIR\OrangeCanvas"
	WriteRegStr SHELL_CONTEXT "Software\Microsoft\Windows\CurrentVersion\Uninstall\Orange" "DisplayName" "Orange (remove only)"
	WriteRegStr SHELL_CONTEXT "Software\Microsoft\Windows\CurrentVersion\Uninstall\Orange" "UninstallString" '"$INSTDIR\uninst.exe"'

	WriteRegStr HKEY_CLASSES_ROOT ".ows" "" "OrangeCanvas"
	WriteRegStr HKEY_CLASSES_ROOT "OrangeCanvas\DefaultIcon" "" "$INSTDIR\OrangeCanvas\icons\OrangeOWS.ico"
	WriteRegStr HKEY_CLASSES_ROOT "OrangeCanvas\Shell\Open\Command\" "" '$PythonDir\python.exe $INSTDIR\orangeCanvas\orngCanvas.pyw "%1"'

	WriteUninstaller "$INSTDIR\uninst.exe"

	FileClose $WhatsDownFile

	!ifdef INCLUDETEXTMINING
             ExecWait '"$PythonDir\python" -c $\"import orngRegistry; orngRegistry.addWidgetCategory(\$\"Text Mining\$\", \$\"$PythonDir\lib\site-packages\orngText\widgets\$\")$\"'
	!endif

SectionEnd	

Function .onInit
	StrCpy $AdminInstall 1

	UserInfo::GetAccountType
	Pop $1
	SetShellVarContext all
	${If} $1 != "Admin"
		SetShellVarContext current
		StrCpy $AdminInstall 0
	${Else}
		SetShellVarContext all
		StrCpy $AdminInstall 1
	${EndIf}

	!insertMacro GetPythonDir


	!ifndef COMPLETE
		StrCmp $PythonDir "" 0 have_python
			MessageBox MB_OK "Please install Python first (www.python.org)$\r$\nor download Orange which includes Python."
			Quit
		have_python:

		!insertMacro WarnMissingModule "$PythonDir\lib\site-packages\PythonWin" "PythonWin"
		!insertMacro WarnMissingModule "$PythonDir\lib\site-packages\qt.py" "PyQt"
		!insertMacro WarnMissingModule "$PythonDir\lib\site-packages\qwt\*.*" "PyQwt"
		!insertMacro WarnMissingModule "$PythonDir\lib\site-packages\Numeric\*.*" "Numeric"

		IfFileExists "$SYSDIR\qt-mt230nc.dll" have_qt
			!insertMacro WarnMissingModule "$PythonDir\lib\site-packages\qt-mt230nc.dll" "Qt"
        have_qt:

		StrCmp $MissingModules "" continueinst
		MessageBox MB_YESNO "Missing module(s): $MissingModules$\r$\n$\r$\nThese module(s) are not needed for running scripts in Orange, but Orange Canvas will not work without them.$\r$\nYou can download and install them later or obtain an Orange installation that includes them.$\r$\n$\r$\nContinue with installation?" /SD IDYES IDYES continueinst
		Quit
		continueinst:
	!endif
FunctionEnd


Function .onInstSuccess
	MessageBox MB_OK "Orange has been successfully installed." /SD IDOK
FunctionEnd
