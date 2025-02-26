# Isolation of legacy equipment

This software demonstrates the use of a CyberHive Connect VPN and an ARM Morello machine to
allow a piece of legacy equipment to be safely connected to a network.

## Overview
Many organisations must grapple with the problem of *legacy equipment*. The term *legacy equipment*
refers to any piece of computer equipment which remains in use despite being very out-of-date, and
in particular to devices which remain in use after support and security updates have been discontinued.
In an ideal world, such devices would not remain in use, but legacy equipment is an unavoidable reality
of the modern IT world. For example, the UK's NHS makes use of medical equipment which relies on outdated
software, including Microsoft Windows XP. This equipment includes, for example, medical imaging devices
which remain in use after their intended lifespan.

The primary issue around the use of legacy equipment is the risk created when it is connected to a computer
network which might be accessible to malicious actors. These malicious actors can exploit vulnerabilities in
the legacy systems. This is of particular concern when (as is frequently the case) the legacy equipment is
performing some critical or sensitive function.

It is possible to mitigate the dangers of networked legacy equipment via traditional network security
measures such as firewalls. However, a more reliable solution is to isolate the legacy equipment inside
a dedicated LAN segment, and allow access to this LAN segment only via a trusted VPN. This allows secure
remote access for devices on the VPN, while totally hiding the legacy equipment from anyone
outside the VPN. It may, however, not be possible or desirable to allow all devices which might need to
have some network interaction with the legacy equipment to be part of the VPN. Instead, we use a carefully-secured
device to act as a gateway between the VPN and a public network, which can enforce control of access to the
legacy hardware. It is vital that this gateway device be hardened against attack, and we show that the use
of an ARM Morello machine in this role prevents the exploitation of memory access bugs in software running on
the gateway.

This repository contains code for a simple demonstrator to show the above ideas in action.

## Warning and License

This software was created for use in a technology demonstrator. It is neither
designed nor intended to be used for any other purpose. In particular, the
authors strongly advise against the use of this software for commercial
purposes, or in any situation where its reliability or security against attack
is important. The software was not designed to operate for more than
a short period of time sufficient for the purposes of demonstration, nor to
operate unsupervised by a person, and is not designed to be secure against
attack by hackers.

The above notice does not form part of the license under which this software
is released, and is for informational purposes only. See LICENSE for details
of how you may use this software, and for the disclaimer of warranties.

## Demonstrator structure

The demonstrator consists of three devices.

- The **legacy equipment device**. In our version of the demonstrator, this role
  is played by a desktop PC running Microsoft Windows XP, with a simple Python
  script to generate simulated medical scan images. This machine represents a legacy
  medical scanning device, e.g. an MRI scanner or X-ray machine.

- A small portable router, which we call the **isolation router**. This router
  provides a LAN segment for the legacy equipment device to connect to. The router
  is also one end of the VPN link with the *public proxy* (below)

- An ARM Morello machine, which we call the **public proxy**. This machine is connected
  to the isolation router via the VPN. The images from the scanner are mirrored to the
  public proxy via the VPN, and made accessible to authorised users via a web interface.

The following diagram shows the structure of the demonstrator.

![demonstrator structure](legacy_system_isolation.svg)

In detail, the demonstrator works as follows.

The legacy equipment device is connected to the LAN of the isolation router, and exposes
services via open network ports. In our set-up, it exposes a Windows network share (SMB) via ports 445 and 139,
and listens for commands to take a scan image on port 5533.

The isolation router is connected to some public network which provides access to the Internet.
This network, which we call the WAN, is assumed to be hostile. The isolation router has the
CyberHive Connect client installed. [CyberHive Connect](https://www.cyberhive.com/product/cyberhive-connect/)
is a mesh VPN, which links devices together into a *Trusted Area Network* (TAN). The isolation
router is configured to forward ports 139, 445, and 5533 from the legacy equipment device to its
TAN interface, and to allow no network traffic to pass between the LAN and
the WAN. This protects the legacy hardware from attack from the WAN.

The public proxy is also connected to the WAN, and also has CyberHive Connect installed.
The public proxy is linked via the Connect TAN to the isolation router, and so can connect
to the port forwards which provide access to the legacy equipment device. The public proxy
is an ARM Morello machine running [Morello Linux](https://www.morello-project.org/).

There are two pieces of software running on the public proxy to implement the gateway
functionality:
- A custom Python script which automatically mirrors the SMB network share from the
  legacy equipment device to a local directory on the public proxy via the TAN..
- Two copies of Apache web server running in docker containers. Each server provides
  access to the directory of scan images (mirrored from the legacy equipment device),
  subject to a successful login. The login process works by taking the credentials
  supplied by the user and passing them to an external binary for checking. The difference
  between the two servers is that one uses a password-checking binary which was compiled
  without CHERI enabled, while the other one uses a CHERI-enabled binary. This allows us
  to demonstrate the use of CHERI (see below). The pages served by these servers also
  allow a user to issue a command to run a scan.

## Setting up the demonstrator

In order to run the demonstrator, you will need an ARM Morello machine running
[Morello Linux](https://www.morello-project.org/) to act as the public proxy,
some device capable of playing the role of the legacy equipment device, and some device capable
of acting as the isolation router, together with some network to connect the isolation router
and public proxy to each other and to the public Internet (to allow CyberHive Connect to function).
For our version of the demonstrator, we used a desktop PC running Microsoft Windows XP as the
legacy equipment device, and a GL.iNet Shadow Router (Model GL-AR300M16-Ext) running OpenWrt
as the isolation router.

The required set up on each devices is as follows.

### Set up on isolation router

We give instructions here for an isolation router running OpenWrt. The key points of the configuration
are that [CyberHive Connect](https://www.cyberhive.com/product/cyberhive-connect/) is installed and
configured, that a static IP address on the LAN is set for the legacy equipment device, and that routing
is configured to block all traffic between the WAN and the LAN, and to forward the relevant ports from
the legacy equipment device to the TAN interface of the router.

To install CyberHive Connect on OpenWrt, do the following.
1. Obtain a `cyberhive-connect` binary for the appropriate architecture (this can be extracted from
   a .deb file provided by CyberHive).
2. Create a user with an access token in your CyberHive Connect Organisation. Use this username and
   token to fill in the placeholder values in the file `etc_config_cyberhive-connect` provided here.
3. Copy the `cyberhive-connect` binary, and the files `etc_config_cyberhive-connect` (from previous step)
   and `etc_init.d_cyberhive-connect` to `/root` on the router, and from this directory execute the
   following commands (NB ensure the router is connected to the Internet).
   ```
   mkdir /root/cyberhive-connect-config
   mv etc_config_cyberhive-connect /etc/config/cyberhive-connect
   mv etc_init.d_cyberhive-connect /etc/init.d/cyberhive-connect
   chmod 755 /etc/init.d/cyberhive-connect 
   mv cyberhive-connect-shadow_3.0 /usr/sbin/cyberhive-connect
   chmod 755 /usr/sbin/cyberhive-connect 
   service cyberhive-connect enable
   service cyberhive-connect start
   ```
   Then approve the router in your CyberHive Connect Organisation. Make a
   note of the TAN IP allocated to the router, as you will need it below.

Next, set a static IP for the legacy equipment device. This makes firewall configuration easier, and
can be done very easily by adding an entry like the following to the end of `/etc/config/dhcp`.
```
config host
       option mac 'xx:xx:xx:xx:xx:xx'
       option ip '192.168.1.4'
```
Where the `xx` values should be replaces with the MAC address of your legacy equipment devices' network
interface. The instructions below assume that you use the IP address `192.168.1.4` as here, but of course
this can easily be altered.

Finally, configure the firewall. A working configuration is provided here in the file `etc_config_firewall`.
To use it, add the following to the bottom of `/etc/config/network`
```
config interface 'tan'
       option device 'connect'
```
and replace the default `/etc/config/firewall` with the file `etc_config_firewall` provided here.

Restart the router after doing all of the above, and connect the legacy equipment device to its LAN.

 
### Set up on public proxy

It is assumed that you have an ARM Morello machine running [Morello Linux](https://www.morello-project.org/)
to act as the public proxy. Do the following.
1. Install the package `smbclient` and install Docker.
2. Add the following lines to `/etc/samba/smb.conf`, under `[global]`
   ```
   client min protocol = CORE
   client max protocol = SMB3
   ```
   This step may not be needed, depending on the SMB setup on the legacy equipment device, but it can
   be needed if (as in our version of the demonstrator) the legacy equipment device is running Microsoft
   Windows XP.
3. Install [CyberHive Connect](https://www.cyberhive.com/product/cyberhive-connect/) and register it in
   your Connect Organisation.
4. Copy all of the files provided here in the directory `public proxy` to some directory on the public proxy
   (e.g. `/root/legacy-demo`). Fill in the placeholder value `xxx.xxx.xxx.xxx` with the TAN IP of the isolation
   router in the files `smb-sync.py` and `html/index.php`.
5. From the demonstrator directory, run `./setup.sh` to complete the set up.

### Set up on legacy equipment device

The legacy equipment device needs to be capable of running a Python script and
providing an SMB network file share. To set up the simple scanning simulation,
copy the files from the `scanner` directory here to some directory on the legacy
equipment device. We shall call this directory the *base directory*.

1. In the base directory, create directories `image-share` and `scanner`.
   Move the files `make_images.py` and `image_template` to `scanner`.
2. Ensure that ports 445, 139, and 5533 are not blocked by any firewall.
3. Set up an SMB network share on `image-share`, with the name `sambashare`.

## Running the demonstrator

After the above set up is done, the demonstrator can be started with the following steps.

1. Ensure all devices are running, that the legacy equipment device is connected to the
   LAN of the isolation router, and that the isolation router and public proxy are connected
   to the WAN.
2. On the legacy equipment device, start the script `make_images.py` and ensure that the
   SMB network share is running.
3. On the public proxy, go to the demonstrator directory and run `./run.sh`

The public interface of the demonstrator can then be accessed via a web browser from any
device connected to the WAN. The two image servers are available on ports 8090 (non-CHERI version)
and 8091 (CHERI version).

Upon navigating to one of the above ports, the user is presented with a login box. The "legitimate"
login credentials are the username `gooduser` and the password `abc123`, and logging in with these
credentials takes the user to a page where they can either issue a command for a new scan, or
view the archive of scanned images (this archive will be empty on first viewing). To demonstrate the
system, press the button to take a scan, and then view the archive of images, refreshing occasionally.
The new image should appear in the archive within 30 seconds.

The power of CHERI can be demonstrated as follows. When a user attempts to log in, the Apache web server
passes the supplied credentials to an external binary for checking. This binary is compiled from a small
piece of C code. However, this C code contains a (deliberate) buffer
overflow vulnerability. The code copies whatever password is entered into a small fixed-length
buffer without any checking of length. If the C code has been compiled with the clang compiler,
then the memory directly after this buffer contains a boolean variable which records whether
authentication was successful.

If CHERI protections are not enabled, then a malicious user can log in by entering the username `gooduser`,
any 10 character string in the password box. This will overflow the buffer (note that the buffer
has been made artificially short to allow ease of demonstration) and overwrite the boolean
variable, making the program think that authentication was successful. However, if CHERI is
enabled, then the processor will detect the illegal memory access and kill the password-checking
program before the illicit log in can succeed.

The difference between the two image servers is that one uses a binary without CHERI features enabled,
while the other uses a binary with CHERI features enabled (these two binaries are both compiled from
exactly the same C source code file). When a user attempts to exploit the buffer overflow in the non-CHERI
version, the log in will succeed, while in the CHERI version the log in will fail.








