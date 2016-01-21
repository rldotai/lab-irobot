# Installation

We want to install OpenCV3, yet (at the time of this writing) such a package is not available in the repositories maintained by Continuum.
Thankfully, some heroic people at the Menpo project have made an OpenCV3 package available which works with Python 3.

Assuming you have `conda` installed already,

```bash
conda install conda-build
git clone https://github.com/menpo/conda-opencv3
cd conda-opencv3
conda config --add channels menpo
conda build conda/
# This will generate a .tar.gz file that conda can install
# (switch to the environment you wish to install OpenCV3 in)
conda install /PATH/TO/OPENCV3/PACKAGE.tar.gz
```

## Building with FFMPEG

I haven't tried this yet, but it may be as easy as adding a repository containing the requisite backports and installing, all via `apt-get`

```bash
sudo add-apt-repository ppa:kirillshkrogalev/ffmpeg-next
sudo apt-get update
sudo apt-get install ffmpeg
```

You would then have to alter the `conda-opencv3/conda/build.sh` file to ensure the proper flags are set for building OpenCV3 with FFMPEG. 

# Troubleshooting

## Building OpenCV3 with Conda using Menpo package

### cURL fails with a certificate error

If you see something like this

```
rl: (77) error setting certificate verify locations:
  CAfile: /etc/pki/tls/certs/ca-bundle.crt
  CApath: none
```

It means that for whatever reason cURL is looking for SSL certificates in `/etc/pki/tls/certs`, yet this directory doesn't exist on Ubuntu/Debian systems.

While this is probably due to a misconfiguration somewhere, you can fix it by copying the certificates that Ubuntu does use to the place where cURL expects them to be:

```
sudo mkdir -p /etc/pki/tls/certs
sudo cp  /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt
```