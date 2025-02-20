# Running FreeDATA in Docker

This image was built to allow FreeDATA to be run on MacOS. These instructions are for MacOS, but should work on any platform that supports Docker.

## Prerequisites

* An install of Docker (eg. [Docker Desktop for MacOS](https://docs.docker.com/desktop/setup/install/mac-install/)).
* Some familiarity with the command line (eg: via `Terminal.app`).
* [Brew](https://brew.sh/) - I've tried to avoid this as a requirement but it is the easiest way to install `pulseaudio` on MacOS.

## Setting up

### PulseAudio

A lot of this is taken from [this gist](https://gist.github.com/seongyongkim/b7d630a03e74c7ab1c6b53473b592712) and [this Dockerfile](https://github.com/KEINOS/Dockerfile_of_Speaker-Test-for-MacHost/blob/master/Dockerfile)

Firstly, install.

```bash
brew install pulseaudio
```

Now run the daemon.
```bash
pulseaudio --load=module-native-protocol-tcp --exit-idle-time=-1 --daemon
```

Confirm it is running.
```bash
pulseaudio --check -v
```

Setup the audio output, this will list your audio output devices. The `*` will show the default output.
```bash
pacmd list-sinks | grep -e 'name:' -e 'index:' -e 'card:'
```

If you need to change your default output then this can be done by specifying the index:
```bash
pacmd set-default-sink 1
```

As will above, setup the the audio source.
```bash
pacmd list-sources | grep -e 'name:' -e 'index:' -e 'card:'
```

Any updates to sources can be triggered with:
```bash
pacmd set-default-source 1
```

### FreeDATA Image

This can be run in one of two ways. By running the docker image with a long command line or via `docker compose`. Lets start with the long command line.

On first run, this will copy the sample config file into the `./freedata-data` directory. This can be edited to suit your needs via the GUI. However, to get the GUI to run you will need to update the `NETWORK` section in `config.ini` file to be:

```bash
[NETWORK]
modemaddress = 0.0.0.0
modemport = 5050
```

Now we can start the server.

```bash
docker run --rm -it \
    -v ./freedata-data:/data
    -e PULSE_SERVER=host.docker.internal
    -v /$HOME/.config/pulse:/home/freedata/.config/pulse \
    -p 5050:5050 \
    --name freedata \
    ghcr.io/dj2ls/freedata:latest
```

If you'd like to start a `rigctld` instance in the container (see [the wiki](https://wiki.freedata.app/en/usage/radio-control#hamlib-rigctld-commands)), the arguments can be provided with the `RIGCTL_ARGS` environment variable. In the examples below I'm passing a model for a FlexRadio at IP `192.168.0.10` listening on port `6701`:

```bash
docker run --rm -it \
    -v ./freedata-data:/data
    -e PULSE_SERVER=host.docker.internal
    -e RIGCTLD_ARGS="--model=2036 --port=4532 --rig-file=192.168.0.10:6701"
    -v /$HOME/.config/pulse:/home/freedata/.config/pulse \
    -p 5050:5050 \
    --name freedata \
    ghcr.io/dj2ls/freedata:latest
```

A slightly more tidy method of provding the same config is via `docker compose`. Create a `docker-compose.yml` file with the following content:

```yaml
services:
  freedata:
    container_name: freedata
    image: ghcr.io/dj2ls/freedata:latest
    pull_policy: always
    volumes:
      - ./freedata-data:/data
      - /$HOME/.config/pulse:/home/freedata/.config/pulse
    environment:
      - PULSE_SERVER=host.docker.internal
      - RIGCTLD_ARGS=--model=2036 --port=4532 --rig-file=192.168.0.10:6701
    ports:
      - 5050:5050
```

This can then be run with:

```bash
docker-compose up -d
```

And its logs viewed with:

```bash
docker-compose logs -f
```

## Usage

Once the server is running, you can access the GUI by visiting `http://localhost:5050/gui` in your browser.

You will need to set up your audio device and radio config.
