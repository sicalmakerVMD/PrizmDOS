
# PrizmDOS

MS-DOS simulator for the CASIO Prizm calculator line, written in MicroPython.

## Screenshots
<img width="385" height="226" alt="{ECA6FBAA-3593-41B0-9549-734E1B58BD87}" src="https://github.com/user-attachments/assets/95c16653-b3ed-42a9-a7f1-c4310aa3e7d4" /> <img width="380" height="214" alt="{8D56A8B3-9A9A-45C0-9A8D-3326D872A679}" src="https://github.com/user-attachments/assets/8d834b23-a74a-4913-bc21-ef9c23fa06cc" /> <img width="378" height="217" alt="{AAD2C844-589A-42DD-820A-65349141AF1C}" src="https://github.com/user-attachments/assets/9dc18e76-b7c0-431b-b003-47ba21d51ccd" />




## Features

- File and directory management with DIR, CD, MD, RD, COPY, DEL, REN, MOVE TYPE, TREE, and DELTREE.
- Wildcard support with ? and *.
- Environment variables with SET, PATH, and %VAR% expansion.
- Customizable command prompt using $P, $G, and $N prompt codes.
- Output redirection with > and >>, including support for NUL.
. Built-in text editor via EDIT, with line insertion, editing, deletion, and saving.
- DOS utilities and system commands: HELP, VER, VOL, LABEL, DATE, TIME, MEM, CHKDSK, MODE, CLS, FIND.
- Virtual disk simulation with a 32 MB simulated C: drive and volume label support.
- Batch file support with CALL, GOTO, IF, PAUSE, REM %0, SHIFT and ECHO ON/OFF.
- Disk persistance using SAVEFS and LOADFS.
- Formatting simulation through FORMAT C:
## Authors

- [@sicalmakervmd](https://www.github.com/sicalmakervmd)


## Contributing

You're welcome to edit PrizmDOS' source code and improve its overall functionality. If you wish to see what you made in future updates (if I ever make any), feel free to drop a pull request!


## FAQ

#### Is this a real version of MS-DOS?

No. PrizmDOS is a simulation. It recreates the behavior and appearance of selected DOS commands.

#### What commands are supported?

Use HELP inside PrizmDOS to see the available commands. DIR, CD, MD, RD, COPY, DEL, REN, MOVE, TYPE, TREE, EDIT, FIND, SET, PATH, PROMPT, FORMAT, SAVEFS, LOADFS, and an easter egg or two.

#### Does it work on other calculators?

Yes. On any Python-based interpreter. The script is just tailored to fit the PRIZM's screen height and width, but, yes, you can test. Feedback is appreciated!

#### Does it support batch files?

Yes. PrizmDOS supports .BAT files and includes CALL, GOTO, IF, PAUSE, REM, ECHO, argument expansion, and SHIFT.

#### Does it have a real filesystem?

Don't expect much from someone who vibecoded a Python script. The C: drive is represented internally as a simulated directory/file structure. Files can optionally be saved to and loaded from a real file using SAVEFS and LOADFS.

#### Can I run real .EXE or .COM programs?

Executables are only simulated, so no.

### Note: even though you can build something similar in 10 minutes, I believe that having a dedicated repo for this script can inspire someone to build a better implementation of this idea. Maybe an add-in made using the fxSDK platform. Who knows?
