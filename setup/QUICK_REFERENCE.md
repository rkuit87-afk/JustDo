# JustDo Pi — Quick Reference Card

## Connect

```bash
ssh justdo-pi                          # SSH into the Pi
ssh pi@192.168.2.11                    # Same thing, by IP
```

## Open JustDo in VS Code (Remote)

```bash
code --remote ssh-remote+justdo-pi /home/pi/JustDo
```

Or: VS Code → Remote Explorer → justdo-pi → Connect → Open Folder → `/home/pi/JustDo`

## Tunnel Flask to your PC

```bash
ssh -L 5000:localhost:5000 justdo-pi
```

Then open: **http://localhost:5000**

## Run Flask on Pi

```bash
ssh justdo-pi "cd /home/pi/JustDo && python3 app.py"
```

## Check Flask is running

```bash
ssh justdo-pi "pgrep -a -f app.py"
```

## Stop Flask on Pi

```bash
ssh justdo-pi "pkill -f app.py"
```

## List JustDo files

```bash
ssh justdo-pi "ls -la /home/pi/JustDo"
```

## Copy a file TO the Pi

```bash
scp myfile.py justdo-pi:/home/pi/JustDo/
```

## Copy a file FROM the Pi

```bash
scp justdo-pi:/home/pi/JustDo/mill.db ./mill.db
```

## Git on the Pi (from VS Code terminal when connected)

```bash
git status
git add .
git commit -m "message"
git push
```

## Re-run SSH setup script

```bash
bash setup/vscode_pi_ssh_setup.sh
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Connection refused` | `sudo systemctl start ssh` on Pi |
| `Permission denied (publickey)` | Re-run `ssh-copy-id -i ~/.ssh/id_rsa.pub pi@192.168.2.11` |
| `No route to host` | Check both devices on 192.168.2.x network |
| VS Code stuck connecting | Kill TIA server on Pi: `ssh justdo-pi "rm -rf ~/.vscode-server"` |
| Flask not accessible | Make sure tunnel is open: `ssh -L 5000:localhost:5000 justdo-pi` |

## Key files on Pi

| Path | What it is |
|---|---|
| `/home/pi/JustDo/app.py` | Main Flask application |
| `/home/pi/JustDo/mill.db` | SQLite database |
| `/home/pi/JustDo/scheduler.py` | Background job scheduler |
| `/home/pi/JustDo/static/index.html` | Frontend |
