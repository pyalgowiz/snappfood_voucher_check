from lxml.html import fromstring
import requests
import http.client
import random
import time

class freeProxyList():
    def __init__(self):
        pass

    def get(self): # FIND PROXIES
        url = 'https://free-proxy-list.net/'
        response = requests.get(url)
        parser = fromstring(response.text)
        proxies = []
        for i in parser.xpath('//tbody/tr')[:300]:   #300 proxies max
            ip = i.xpath('.//td[1]/text()')[0]
            port = i.xpath('.//td[2]/text()')[0]
            https = i.xpath('.//td[7]/text()')[0]
            if https == 'yes':
                proxies.append([ip, port])
        return proxies

class Proxies(freeProxyList):
    def __init__(self):
        self.path = 'files/proxy_list.txt'

    def choose(self):
        elem = []
        with open(self.path, "r") as f:
            proxiy_list = f.read()
            elem = proxiy_list.split("\n")
            while len(elem) <= 1:
                print(f"there is no proxy in {self.path}")
                time.sleep(10*60)
                proxiy_list = f.read()
                elem = proxiy_list.split("\n")
            chosen_elem = random.choice(elem)
            ip, port = chosen_elem.split(":")
            f.close()
        return ip, port

def update_available_proxies():
    prox = Proxies()
    chosen = {}
    output = ""

    proxies = prox.get()
    with open(prox.path, "r") as f:
        proxiy_list = f.read()
        for elem in proxiy_list.split("\n"):
            if elem:
                ip, port = elem.split(":") 
                proxies.append([ip, port])
        f.close()

    print(f"checking snappfood {len(proxies)} proxies!")
    for proxy in proxies:
        ip, port = proxy[0], proxy[1]
        # print(ip,":",port)
        conn = http.client.HTTPSConnection(str(ip), int(port), timeout= 10) 
        conn.set_tunnel("snappfood.ir")
        try:
            header= {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            }
            conn.request("GET","/", '', headers=header)
            res = conn.getresponse()
            data = res.read()
            if res.status == 200:
                print("done", res.status)
                chosen[ip] = port
        except Exception as e:
            pass
            # print(e)
    print(f"checking finished, good proxies: {len(chosen)}")
    for ip in chosen:
        port = chosen[ip]
        output += f'{ip}:{port}\n'
    with open(prox.path, "w") as f:
        f.write(output)
        f.close()

