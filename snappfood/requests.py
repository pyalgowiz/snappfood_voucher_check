import ast
import http.client
from http.client import ResponseNotReady, CannotSendRequest, RemoteDisconnected
import random
import redis
import json
from codecs import encode
from proxies import Proxies

r = redis.Redis(host='localhost', port=6379, db=0)
proxies = Proxies()

class Request():
    def __init__(self) -> None:
        print("starting request")
        self.Host = "snappfood.ir"
        self.dataList = []
        self.boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            "Accept-Encoding": "utf-8",
            'Content-type': f'multipart/form-data; boundary={self.boundary}',
            "Host": self.Host
        }
        self.check_connection()
        # logging.basicConfig(level=logging.DEBUG)

    def delete_proxy(self):
        Host = self.Host
        self.conn = http.client.HTTPSConnection(Host)

    def set_proxy(self):
        flag = True
        while flag:
            try:
                ip, port = proxies.choose()
                flag = False
            except Exception as e:
                print(e)
        self.conn = http.client.HTTPSConnection(str(ip), int(port), timeout=10) 
        self.conn.set_tunnel(self.Host)
        return True

    def set_dataList(self, data: dict):
        dataList = self.dataList
        boundary = self.boundary
        dataList.append(encode('Content-Disposition: form-data; name=cellphone;'))
        dataList.append(encode('Content-Type: text/plain'))
        dataList.append(encode(''))
        for elem in data:
            dataList.append(encode(f'--{boundary}'))
            dataList.append(encode(f'Content-Disposition: form-data; name={elem};'))
            dataList.append(encode('Content-Type: text/plain'))
            dataList.append(encode(''))
            dataList.append(encode(data[elem]))
        dataList.append(encode(''))
        out = b'\r\n'.join(dataList)
        return out

    def login(self, phone: str):
        session = self.conn
        data = self.set_dataList({'cellphone': phone})
        session.request("POST", '/mobile/v2/user/loginMobileWithNoPass', body= data, headers= self.headers)
        response = session.getresponse()
        response.read()
        if int(response.status) == 200:
            return True
        return False

    def authenticate(self, phone, otp_code):
        data = self.set_dataList({'cellphone': phone, 'code': otp_code})
        session = self.conn
        session.request("POST", "/mobile/v2/user/loginMobileWithToken?client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1", data, headers= self.headers)
        res = session.getresponse()
        data = res.read()
        if int(res.status) == 200:
            set_cookie_header = res.getheader("Set-Cookie")
            cookie_parts = set_cookie_header.split(",")
            phpsessid = cookie_parts[0].split(";")[0]
            remember = cookie_parts[1].split(";")[0]
            cookie = str(phpsessid) + ";" + str(remember)
            data = json.loads(data.decode())
            r.hset("accounts", "phone", data['data']['user']["username"])
            r.hset("accounts", "id", data['data']['user']["id"])
            r.hset("accounts", "cookie", str(cookie))
            return data
        return False

    def check_connection(self):
        flag = True
        self.set_proxy()
        while flag:
            try:
                session = self.conn
                session.request("GET", '/', '') 
                response = session.getresponse()
                print(response.status)
                data = response.read()
                flag = False
            except Exception as e:
                self.set_proxy()
                print('snapfood test error: ', e)
        if response.status == 200:
            print(data)

    def get_resturant_list(self):
        r.delete("data_store")
        url = "/search/api/v1/desktop/vendors-list?lat=36.353&long=59.529&page=0&page_size=200"
        session = self.conn
        flag = True
        while flag:
            try:
                session.request("GET", url)
                res = session.getresponse()
                if res.status == 200:
                    data = json.loads(res.read().decode())
                    for elem in data["data"]["finalResult"]:
                        r.hset("data_store", elem['data']['id'], elem['data']['code'])
                else:
                    return "error in request: " + str(res.status)
                flag = False
                return True
            except Exception as e:
                self.check_connection()
                print("get_resturant_list error:", e)
    
    def get_products_id(self):
        r.delete("stores_id")
        session = self.conn
        for i in r.hgetall("data_store").values():
            while True:
                try:
                    url = f"/mobile/v2/restaurant/details/dynamic?optionalClient=WEBSITE&vendorCode={i.decode()}"
                    session.request("GET", url)
                    res = session.getresponse()
                    if res.status == 200:
                        data = json.loads(res.read().decode())
                        prod = data["data"]["menus"][0]["products"][0]["id"]
                        r.hset("stores_id", i.decode(), prod)
                        break
                    else:
                        return "error in request: " + str(res.status)
                except Exception as e:
                    self.check_connection()
                    break
        return True

    def create_basket(self):
        r.delete("baskets")
        url = "/mobile/v2/basket/" 
        session = self.conn
        cookie = r.hget("accounts", "cookie")
        self.headers['Content-type'] = "application/json"
        self.headers['Cookie'] = cookie.decode()
        # POST BODY:
        out = []
        for i in r.hgetall("stores_id"):
            while True:
                try:
                    value = r.hget("stores_id", i)
                    payload = json.dumps({
                        "actions": [
                            {
                                "action": "setVendor",
                                "argument": {
                                    "vendor_code": i.decode()
                                }
                            },
                            {
                                "action": "setSource",
                                "argument": {
                                    "source": "WEBSITE"
                                }
                            },
                            {
                                "action": "setProducts",
                                "argument": {
                                    "id": int(value.decode()),
                                    "count": 5,
                                    "toppings": []
                                }
                            }
                        ]
                    })
                    session.request("POST", url, payload, self.headers)
                    res = session.getresponse()
                    if res.status == 200:
                        resread = res.read().decode()
                        data = json.loads(resread)
                        user = data["data"]["basket"]["id"]
                        out.append(user)
                        break
                    else:
                        return "error in this request: " + str(res.status)
                except Exception as e:
                    break
        r.set("baskets", str(out))
        return True

    def check_voucher(self, code):
        session = self.conn
        payload = json.dumps({
            "actions": [
                {
                    "action": "setVoucher",
                    "argument": {
                        "voucher_code": str(code)
                    }
                }
            ]
        })
        basket = r.get('baskets').decode()
        basket = ast.literal_eval(basket)
        if len(basket) == 0 :
            print("there is no basket")
            return
        flag = True
        while flag:
            try:
                user = random.choice(basket)
                session.request("PUT", f"/mobile/v2/basket/{user}", payload, self.headers)
                res = session.getresponse()
                data = res.read()
                if res.status != 200:
                    print("res status:", res.status)
                    continue
                flag = False
            except RemoteDisconnected:
                self.check_connection()
            except ResponseNotReady:
                print("error in basket, recreating")
                self.create_basket()
            except CannotSendRequest:
                self.check_connection()
                print("cannot send request")
        return data.decode()

