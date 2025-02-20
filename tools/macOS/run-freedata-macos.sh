#!/bin/bash
#
# Simple script to run FreeDATA in Linux
# Dj Merrill - N1JOV
#
# slightly modified Version for macOS
# All credits to the original creators
# Oliver - HB9HBO
#
# Run this script in the directory that contains the "FreeDATA", 
# "FreeDATA-venv", and "FreeDATA-hamlib" directories 
# created by the install-freedata-linux.sh script
#
# Two log files are created in this directory:
# FreeDATA-server.log: debug output from the server process
# FreeDATA-client.log: debug output from the GUI front end
# To view live, "tail -f FreeDATA-server.log" or "tail -f FreeDATA-client.log"
#
# We expect the config.ini file to be at $HOME/.config/FreeDATA/config.ini
# If it isn't found, we copy config.ini.example there
#
# 2.0:	30 Jan 2025 (HB9HBO)
#	checks if MacPorts or brew is installed
# 1.9:	29.Jan 2025 (HB9HBO)
#	MacOS version 
# 1.8:  22 May 2024 (DJ2LS)
#	add support for browser based gui
# 1.7:  22 May 2024
#	Slightly change the way we shutdown the server
# 1.6:  05 May 2024
#	Don't stop rigctld if it was started separate from FreeDATA
#	We only want to clean up FreeDATA initiated processes
# 1.5:  05 May 2024
#	Check for rigctld at exit and stop it if needed
# 1.4:  05 May 2024
#	Added comments on how to view log outputs in realtime
# 1.3:  02 May 2024
#	Add support for hamlib installed by FreeDATA install script
# 1.2:  30 Apr 2024
# 1.1:  26 Apr 2024
# 1.0:	25 Apr 2024 Initial release
#


#///////////////////////////////////////////////////////////////
# verify installation of a pakage manager

port=`which port`
brew=`which brew`

if [ ! -x "$port" ] && [ ! -x "$brew" ];
then
	echo "Macports or Homebrew not found in PATH!"
	echo "Maybe you forgot adding the search path to your .bashrc or .zprofile?"
	echo "Or try a logout/login, so the ENV Variables would setup correctly "
	exit 1
fi



# Set path to find our hamlib install
export PATH=./FreeDATA-hamlib/bin:$PATH
export LD_LIBRARY_PATH=./FreeDATA-hamlib/lib:$LD_LIBRARY_PATH

if [ ! -f "FreeDATA-hamlib/bin/rigctl" ];
then
	echo "Something went wrong.  FreeDATA-hamlib/bin/rigctl not found."
	exit 1
fi

# Activate the Python Virtual Environment
source ./FreeDATA-venv/bin/activate

# Check to see if there is an old server running, and stop it if there is
checkoldserver=`ps auxw | grep FreeDATA | grep server.py`

if [ ! -z "$checkoldserver" ];
then
	oldserverpid=`echo $checkoldserver | cut -d" " -f2`
	echo "*************************************************************************"
	echo "Found old FreeDATA server at PID" $oldserverpid "- stopping it"
	echo "*************************************************************************"
	kill $oldserverpid
	sleep 7
fi

# Check for an already running rigctld process
# This was probably started by other means so we should leave this 
# alone when we exit
checkrigexist=`ps auxw | grep -i rigctld | grep -v grep`

echo "*************************************************************************"
echo "Running the FreeDATA server component"
echo "*************************************************************************"

# New versions use freedata_server, old version use modem
if [ -d "FreeDATA/freedata_server" ];
then
	serverdir="FreeDATA/freedata_server"
else
	serverdir="FreeDATA/modem"
fi


#////////////////////////////////////////////////////////////////
#	Changes for macOS
#	Put the config and DB-file on a macOS like location
#
if [ ! -d $HOME/Library/Application\ Support/FreeDATA ];
then
	mkdir -p $HOME/Library/Application\ Support/FreeDATA
fi
if [ ! -f $HOME/Library/Application\ Support/FreeDATA/config.ini ];
then
	echo "*************************************************************************"
	echo "No config file found.  Copying example config file to"
	echo $HOME/Library/Application\ Support/FreeDATA/config.ini
	echo "*************************************************************************"

	cp $serverdir/config.ini.example $HOME/Library/Application\ Support/FreeDATA/config.ini


	#////////////////////////////////////////////////////////////////
	# Change the Server Port, macOS uses TCP 5000 for AirPlay
	#
	sed -i'' -e 's/modemport = 5000/modemport = 5050/' $HOME/Library/Application\ Support/FreeDATA/config.ini

fi


#////////////////////////////////////////////////////////////////
#	Config and DB-File macOS like
#
FREEDATA_CONFIG=$HOME/Library/Application\ Support/FreeDATA/config.ini FREEDATA_DATABASE=$HOME/Library/Application\ Support/FreeDATA/freedata-messages.db python3 $serverdir/server.py > FreeDATA-server.log 2>&1 &
serverpid=$!
echo "Process ID of FreeDATA server is" $serverpid



# Function to handle Ctrl-C
function ctrl_c() {
    echo "*************************************************************************"
    echo "Stopping the server component"
    echo "*************************************************************************"
    kill -INT $serverpid

	#################################################################
	# 	macOS Change 5s to 5, doesn't like s
    # Give time for the server to clean up rigctld if needed
    sleep 5

    # If rigctld was already running before starting FreeDATA, leave it alone
    # otherwise we should clean it up
    if [ -z "$checkrigexist" ]; then
        # rigctld was started by FreeDATA and should have stopped when the
        # server exited.  If it didn't, stop it now.
        checkrigctld=$(ps auxw | grep -i rigctld | grep -v grep)
        if [ ! -z "$checkrigctld" ]; then
            echo "*************************************************************************"
            echo "Stopping rigctld"
            echo "*************************************************************************"
            rigpid=$(echo $checkrigctld | awk '{print $2}')
            kill $rigpid
        fi
    fi

    # Return to the directory we started in
    cd ..

    # Exit the script
    exit 0
}


# Trap Ctrl-C (SIGINT) and call the ctrl_c function
trap ctrl_c SIGINT

# Wait indefinitely for Ctrl-C
echo "Server started with PID $serverpid. Press Ctrl-C to stop."
while true; do
    sleep 1
done

