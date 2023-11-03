remove-item package/ -Force
pyinstaller --onefile --windowed --icon=media/icon.ico main.py
copy-item media/ dist/ -Recurse -Force
copy-item positions.json dist -Force
copy-item views.json dist -Force
move-item dist/main.exe dist/FMDS.exe -Force
new-item -Path "./package/FMDS" -ItemType "directory" -Force
Get-Item -Path dist\* | Move-Item -Destination package\FMDS\ -Force
remove-item dist/ -Force
new-item -Path "./package/FMDS/fm_files/filters/" -ItemType "directory" -Force
new-item -Path "./package/FMDS/fm_files/views/" -ItemType "directory" -Force
Get-Item -Path fm_files\filters\* | Copy-Item -Destination package\FMDS\fm_files\filters\ -Force
Get-Item -Path fm_files\views\* | Copy-Item -Destination package\FMDS\fm_files\views\ -Force

Compress-Archive -Path package/FMDS -DestinationPath package/FMDS.zip