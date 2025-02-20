Suggested instructions for using the install and run scripts.

Before running the install script, ensure that your account is in the
"dialout" group, and that your account has "sudo" privileges.  Refer to 
your particular OS variant for instructions on how to do this.

To install the FreeDATA software:

Open a terminal shell and run the following commands:

mkdir ~/freedata

cd ~/freedata

wget https://raw.githubusercontent.com/DJ2LS/FreeDATA/main/tools/Linux/install-freedata-linux.sh

wget https://raw.githubusercontent.com/DJ2LS/FreeDATA/main/tools/Linux/run-freedata-linux.sh

To install from the main FreeDATA branch, run:
bash install-freedata-linux.sh

or to install from the develop FreeDATA branch, run:
bash install-freedata-linux.sh develop


To run the FreeDATA software:

Open a terminal shell and run the following commands:

cd ~/freedata

bash run-freedata-linux.sh


To view debugging output while running FreeDATA:

Open a terminal shell.

cd ~/freedata

To view the GUI debug output:
tail -f FreeDATA-client.log

To view the server debug output:
tail -f FreeDATA-server.log


The run script looks for the config.ini file at: 
$HOME/.config/FreeDATA/config.ini

If it isn't found, we place a copy of config.ini.example into that location
to give FreeDATA something to start with.  Changes to the defaults can be
made within the FreeDATA GUI.
