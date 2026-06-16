# Enable SSH on the Raspberry Pi
## Run these commands on the Pi directly (HDMI + keyboard, or existing terminal)

---

### Check if SSH is already running

```bash
sudo systemctl status ssh
```

Look for `active (running)` in the output.

---

### If SSH is not running — enable it

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

---

### Confirm SSH is listening on port 22

```bash
ss -tlnp | grep :22
```

You should see a line containing `0.0.0.0:22`.

---

### Find the Pi's IP address (confirm it is 192.168.2.11)

```bash
hostname -I
```

---

### Test from the engineering PC

Open a terminal on your PC and run:

```bash
ssh pi@192.168.2.11
```

You should get a login prompt. Type your Pi password (default: `raspberry`).

---

### If SSH is blocked by firewall

```bash
sudo ufw allow 22
sudo ufw status
```

---

### Raspi-config alternative (GUI method)

```bash
sudo raspi-config
```

Navigate: **Interface Options → SSH → Enable → Finish**

---

That's it. Once SSH is confirmed running, go back to the engineering PC and run the setup script.
