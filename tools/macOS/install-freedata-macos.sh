#!/bin/bash
#
# Simple script to install FreeDATA in Linux
# Dj Merrill - N1JOV
#
# modified Version for macOS
# All credits to the original creators
# Oliver - HB9HBO
# 
# Run this script by typing in the terminal (without the quotes):
# "bash install-freedata-macos.sh" to install from the main branch 
# "bash install-freedata-macos.sh develop" to install from the develop branch
#
# This script creates three subdirectories in the directory it is run
# FreeDATA: Contains the FreeDATA software
# FreeDATA-venv: Contains the Python virtual environment
# FreeDATA-hamlib: Contains the hamlib libraries
#
# FreeDATA config file is stored in $HOME/Library/Application Support/FreeDATA/config.ini
# See the run-freedata-macos.sh for more details
#
#
#
# Changelog:
# 2.4:	29 Jan 2025 (hb9hbo)
#	OS version handling and further macports refinement
#
# 2.3:  26 Jan 2025 (vk1kcm)
#	clean up macport install
#
# 2.2:	24 Jan 2025 (hb9hbo)
#	install with brew and macports
#
# 2.1:	23 Jan 2025 (hb9hbo)
#	Initial macOS version
#
# 2.0:	04 Oct 2024 (deej)
# 	Add support for Fedora 40
#
# 1.9:	14 Sep 2024 (deej)
# 	Tweak OS version checking section to handle minor OS revisions better
#
# 1.8:	23 July 2024 ( DJ2LS )
# 	Add support for browser based gui
#
# 1.7:	31 May 2024 ( DJ2LS )
# 	Add support for version specific setup
#
# 1.6:	22 May 2024
#	Reflect directory name changes in prep for merging develop to main
#
# 1.5:	12 May 2024
#	"dr-freedata-001" branch of codec2 merged to main so we don't
#	need to checkout that branch specifically
#
# 1.4:	05 May 2024
#	Change to "dr-freedata-001" branch of codec2 for develop mode
#	Added comments in scripts and README.txt for config file location
#	If hamlib 4.5.5 is already in FreeDATA-hamlib, don't reinstall
#
# 1.3:	02 May 2024
#	Remove dependency on distro supplied hamlib library which can be old
#	Download and install hamlib 4.5.5 into ./FreeDATA-hamlib
#	Add support for Debian 11 and Ubuntu 22.04
#
# 1.2:	30 Apr 2024
#	Remove dependency on distro supplied nodejs which can be too old
#	Install nodejs version 20 into ~/.nvm
#
# 1.1:	26 Apr 2024
#	Add support for installing from FreeDATA develop branch
#	Add support for Ubuntu 24.04
#	
# 1.0:	Initial release 25 Apr 2024 supporting Debian 12
#

case $1 in
   "" | "main")
	args="main"
   ;;
   "develop")
	args="develop"
   ;;
  v*)
  args=$1
  ;;
  *)
	echo "Argument" $1 "not valid.  Exiting."
	exit 1
   ;;
esac




#///////////////////////////////////////////////////////////////////////////////
# find macos and version	
# 
osname=`sw_vers -productName`
osversion=`sw_vers -productVersion | cut -d"." -f1`


#////////////////////////////////////////////////////////////////////////////////
# find installed additional Package Manager
#	
port=`which port`
brew=`which brew`

if [[ -x $port && -x $brew ]];
then
	echo "MacPorts and homebrew installed!"
	echo "selecting MacPorts for installation"
	pkgmgr='macports'
	brew=''
fi

if [[ -x $port  ]];
then
	pkgmgr='macports'
	pkgmgrversion=`port version | cut -d" " -f2 | awk -F. '{print $1 "." $2}'`
elif [[ -x $brew ]];
then
	pkgmgr='homebrew'
else
	echo "Neither MacPorts nor homebrew installed"
	echo "please install one!"
	exit 1
fi


echo "Running on $osname version $osversion with $pkgmgr"


echo "*************************************************************************"
echo "Installing software prerequisites"
echo "If prompted, enter your password to run the sudo command"
echo "*************************************************************************"



#////////////////////////////////////////////////////////////////////////////////
# Variables for MacPorts install
# we don't want break an already installed and working python3
#
mp_pkgs="wget cmake portaudio nvm nodejs22 npm10"
mp_path="/opt/local/bin"
mp_py_version="313"
mp_pkg_python="python$mp_py_version"
mp_pkg_pip="py$mp_py_version-pip"
mp_pkg_virtualenv="py$mp_py_version-virtualenv"
mp_path_python="$mp_path/python3"
mp_path_pip="$mp_path/pip3"
mp_path_virtualenv="$mp_path/virtualenv"
mp_select_python=0
mp_select_pip=0
mp_select_virtualenv=0

case $osname in
	"macOS")
	case $osversion in
		"14" | "15")
			case $pkgmgr in
				"macports")

					#////////////////////////////////////////////////////////////////////////////////
					# update the MacPorts package cache
					#
					echo "Installing FreeDATA on top of MacPorts"
					sudo port selfupdate


					#////////////////////////////////////////////////////////////////////////////////
					# Check for working python3 in macports
					#
					if [ ! -f "$mp_path_python" ] && [ ! -x "$mp_path_python" ];
					then
						echo "Python3 not installed, add $mp_pkg_python"
						mp_pkgs="$mp_pkg_python $mp_pkgs"
						mp_select_python=1
					fi
	
	
					#////////////////////////////////////////////////////////////////////////////////
					# Check for working pip in macports
					#
					if [ ! -f "$mp_path_pip" ] && [ ! -x "$mp_path_pip" ];
					then
						echo "Python pip not installed, add $mp_pkg_pip"
						mp_pkgs="$mp_pkg_pip $mp_pkgs"
						mp_select_pip=1
					fi
	

					#////////////////////////////////////////////////////////////////////////////////
					# Check for installed virtualenv  in macports
					#
					if [ ! -f "$mp_path_virtualenv" ] && [ ! -x "$mp_path_virtualenv" ];
					then
						echo "Python pip not installed, add $mp_pkg_virtualenv"
						mp_pkgs="$mp_pkg_virtualenv $mp_pkgs"
						mp_select_virtualenv=1
					fi
	
	
					#////////////////////////////////////////////////////////////////////////////////
					# install required packages
					#
					echo "Installing required Packages."			
					sudo port -N install $mp_pkgs
	
	
					#////////////////////////////////////////////////////////////////////////////////
					# select python3.10 and/or pip313 as the default version, if not installed
					#
					if [ "$mp_select_python" -eq 1 ];
					then
						echo "Selecting $mp_pkg_python"
						sudo port select --set python3 "python$mp_py_version"
					fi
					if [ "$mp_select_pip" -eq 1 ];
					then
						echo "Selecting $mp_pkg_pip"
						sudo port select --set pip3 "pip$mp_py_version"
					fi
					if [ "$mp_select_virtualenv" -eq 1 ];
					then
						echo "Selecting $mp_pkg_virtualenv"
						sudo port select --set virtualenv "virtualenv$mp_py_version"
					fi

					#////////////////////////////////////////////////////////////////////////////////
					# adding macports Path to $PATH
					#
					if [[ ! $PATH =~ "$mp_path" ]];
					then
						echo "Adding $mp_path to \$PATH"
						export PATH="$mp_path":$PATH
					fi
					;;
	
				"homebrew")
					#/////////////////////////////////////////////////////////////////////////
					# more testing needed
					echo "Installing FreeDATA on top of homebrew"
					brew update
					brew install wget cmake portaudio python pyenv-virtualenv nvm node@22 npm
					export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:$PATH"
					;;
	
				*)
					echo "*************************************************************************"
					echo "$osname $osversion $pkgmgr"
					echo "This installation is not compatible, please install macports or homebrew"
					echo "*************************************************************************"
					exit 1
			   		;;
			esac
			;;

		*)
			echo "*************************************************************************"
			echo "This version of MacOS is not yet supported by this script."
			echo $osname $osversion
			echo "*************************************************************************"
			exit 1
			;;
	esac
	;;

	*)
		echo "*************************************************************************"
		echo "This Operating System is not supported"
		echo $osname $osversion
		echo "*************************************************************************"
		exit 1
		;;

esac



#///////////////////////////////////////////////////////////////////////////////
# find No CPU's and use half of them for compiling (make -j $ncpu)
#
ncpu=`sysctl hw.ncpu | awk '{print $2}'`
ncpu=$(($ncpu / 2))
if [ $ncpu -lt 1 ];
then
	ncpu=1
fi



echo "*************************************************************************"
echo "Checking for hamlib 4.5.5 in FreeDATA-hamlib"
echo "*************************************************************************"

if [ -d "FreeDATA-hamlib.old" ];
then
	rm -rf FreeDATA-hamlib.old
fi

if [ -d "FreeDATA-hamlib" ];
then
	if [ -f "./FreeDATA-hamlib/bin/rigctl" ];
	then
		checkhamlibver=`./FreeDATA-hamlib/bin/rigctl --version | cut -f3 -d" "`
		if [ "$checkhamlibver" != "4.5.5" ];
		then
			mv FreeDATA-hamlib FreeDATA-hamlib.old
		else
			echo "Hamlib 4.5.5 found, no installation needed."
		fi
	else
		mv FreeDATA-hamlib FreeDATA-hamlib.old
	fi
fi

if [ ! -d "FreeDATA-hamlib" ];
then
	echo "Installing hamlib 4.5.5 into FreeDATA-hamlib"
	curdir=`pwd`
	wget https://github.com/Hamlib/Hamlib/releases/download/4.5.5/hamlib-4.5.5.tar.gz
	if [ -f "hamlib-4.5.5.tar.gz" ];
	then
		tar -xf hamlib-4.5.5.tar.gz
	else
		echo "Something went wrong.  hamlib-4.5.5.tar.gz not downloaded."
		exit 1
	fi
	if [ -d "hamlib-4.5.5" ];
	then
		cd hamlib-4.5.5


		#///////////////////////////////////////////////////////////////////////////////
		# make sure the Libraries and Includes where found, no need for libusb
		#
		./configure --prefix=$curdir/FreeDATA-hamlib CPPFLAGS="-I/opt/local/include" LDFLAGS="-L/opt/local/lib/" --without-libusb
		make -j $ncpu
		make install
		cd ..
	else
		echo "Something went wrong.  hamlib-4.5.5 directory not found."
		exit 1
	fi
	if [ ! -f "$curdir/FreeDATA-hamlib/bin/rigctl" ];
	then
		echo "Something went wrong." $curdir"/FreeDATA.hamlib/bin/rigctl not found."
                exit 1
	else
		echo "Cleaning up files from hamlib build."
		rm -f hamlib-4.5.5.tar.gz
		rm -rf hamlib-4.5.5
        fi
fi


echo "*************************************************************************"
echo "Checking for old FreeDATA directories"
echo "*************************************************************************"
if [ -d "FreeDATA.old" ];
then
	rm -rf FreeDATA.old
fi
if [ -d "FreeDATA-venv.old" ];
then
	rm -rf FreeDATA-venv.old
fi
if [ -d "FreeDATA" ];
then
	mv FreeDATA FreeDATA.old
fi
if [ -d "FreeDATA-venv" ];
then
	mv FreeDATA-venv FreeDATA-venv.old
fi

echo "*************************************************************************"
echo "Creating Python Virtual Environment FreeDATA-venv"
echo "*************************************************************************"
python3 -m venv FreeDATA-venv

echo "*************************************************************************"
echo "Activating the Python Virtual Environment"
echo "*************************************************************************"
if [ -f "./FreeDATA-venv/bin/activate" ];
then
	source ./FreeDATA-venv/bin/activate
else
	echo "Something went wrong.  FreeDATA-venv virtual environment not created properly."
	exit 1
fi

echo "*************************************************************************"
echo "Updating pip and wheel"
echo "*************************************************************************"
pip3 install --upgrade pip wheel

echo "*************************************************************************"
echo "Downloading the FreeDATA software from the git repo"
echo "*************************************************************************"
if [ "$args" == "develop" ];
then
  echo "Downloading development version"
  git clone https://github.com/DJ2LS/FreeDATA.git -b develop
	git checkout develop
elif [[ $args == v* ]];
then
    echo "Downloading specific version: $args"
    git clone https://github.com/DJ2LS/FreeDATA.git -b $args
else
    echo "Downloading regular version"
	git clone https://github.com/DJ2LS/FreeDATA.git
fi


echo "*************************************************************************"
echo "Changing Directory into FreeDATA"
echo "*************************************************************************"
if [ -d "FreeDATA" ];
then
	cd FreeDATA
else
	echo "Something went wrong.  FreeDATA software not downloaded from git."
	exit 1
fi


echo "*************************************************************************"
echo "Installing required Python programs into the virtual environment"
echo "*************************************************************************"

#///////////////////////////////////////////////////////////////////////////////
# Compiler can't find the Includes and Libraries
#	
if [ $pkgmgr == "macports" ];
then
	CFLAGS="-I/opt/local/include" LDFLAGS="-L/opt/local/lib" pip3 install --upgrade -r requirements.txt
fi
if [ $pkgmgr == "homebrew" ];
then
	CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip3 install --upgrade -r requirements.txt
fi


echo "*************************************************************************"
echo "Changing into the server directory"
echo "*************************************************************************"
cd freedata_server/lib


echo "*************************************************************************"
echo "Checking and removing any old codec2 libraries"
echo "*************************************************************************"
if [ -d "codec2" ];
then
	mv codec2 codec2.old
fi

echo "*************************************************************************"
echo "Downloading the latest codec library"
echo "*************************************************************************"
git clone https://github.com/drowe67/codec2.git


echo "*************************************************************************"
echo "Changing into the codec2 library directory"
echo "*************************************************************************"
if [ -d "codec2" ];
then
	cd codec2
else
	echo "Something went wrong.  Codec2 software not downloaded from git."
	exit 1
fi
	
echo "*************************************************************************"
echo "Setting up the codec2 build"
echo "*************************************************************************"
mkdir build_macos
cd build_macos

echo "*************************************************************************"
echo "Building the codec2 library"
echo "*************************************************************************"
cmake ..
make -j $ncpu

if [ ! -f "src/libcodec2.1.2.dylib" ];
then
	echo "Something went wrong.  Codec2 software not built."
	exit 1
fi

echo "*************************************************************************"
echo "Building the FreeDATA GUI frontend"
echo "*************************************************************************"
cd ../../../..
cd freedata_gui
npm i
npm run build

# Return to the directory we started in
cd ../..

echo ""
echo "*************************************************************************"
echo "FreeDATA is installed, run with 'bash run-freedata-macos.sh'"
echo "*************************************************************************"
echo ""
