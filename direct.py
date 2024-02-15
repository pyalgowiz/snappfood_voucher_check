from proxies import update_available_proxies
import time 

while True:
    update_available_proxies()
    time.sleep(10*60)
