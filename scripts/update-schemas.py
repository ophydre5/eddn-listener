#!/usr/bin/env python3

import os
import io
import json
import requests

__configfile_fd = os.open("eddnlistener-config.json", os.O_RDONLY)
__configfile = os.fdopen(__configfile_fd)
__config = json.load(__configfile)
os.close(__configfile_fd)

for s in __config['schemas']:
  r = requests.get(s['message_schema'])
  if (r.status_code == 200):
    sf = io.open("schemas/" + s['local_schema'], "w")
    sf.writelines(r.text)
    sf.close()
