# Get Atome Direct Energie informations to Domoticz

## Install

```bash
sudo apt-get install python3 python3-bs4
pip install requests
git clone https://github.com/k20human/domoticz-atome.git
```

Copy ``config.json.exemple`` to ``config.json`` and fill with your Domoticz and Atome informations

Add to your cron tab (with ``crontab -e``):
```bash
59,29 * * * * cd /home/pi/domoticz-atome && python3 execute.py
```
