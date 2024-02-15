import json
from telethon import events
import asyncio
import string 
import random
import concurrent.futures

from bot import bot
import re
import redis

from snappfood.requests import Request
from proxies import Proxies

db = redis.Redis('localhost', port=6379, db=0)

admins = [
    'admins chatid'
]

req = Request()
proxie = Proxies()

def voucher_checker(user_id, code):
    print("start voucher_checker")
    db.set("tested_codes", 0)
    for line in code:
        db.incr("tested_codes")
        if line == "":
            continue
        try:
            res = req.check_voucher(line)
            data = json.loads(res)
            if 'error' in data:
                print(data['error']['message'])
                pass
            elif data:
                db.hset("correct_codes", line, True)
                bot.send_message(user_id, "یک کد تخفیف پیدا شد: "+str(line))
        except json.decoder.JSONDecodeError:
            print(res)
        except IndexError:
            print(res)
        except TypeError:
            print("type error: ",type(res))
            print("error data:",res)
        except Exception as e:
            print(type(e))
            bot.send_message(user_id, str(e))
    bot.send_message(user_id, "لیست تمام شد")
    return

def rebuild_basket(user_id):
    try:
        res = req.get_resturant_list()
        bot.send_message(user_id, "رستوران ها لیست شدند")
        res = req.get_products_id()
        bot.send_message(user_id, "محصولات از داخل رستوران بیرون کشیده شد")
        res = req.create_basket()
        bot.send_message(user_id, "با هر محصول و رستوران سفارش انجام دادیم و سبد خرید ساخته شد")
    except Exception as e:
        return "build error: "+str(e)
    return "انجام شد!" if res == True else res["error"]["message"]

@bot.on(events.NewMessage(func=lambda e: e.out == False))
async def inComeMessages(event):
    user_id = event.chat_id
    message_text = event.text.lower()
    combo_file = event.document
    loop = await asyncio.get_event_loop()

    if str(user_id) not in admins:
        await event.respond('شما ادمین نیستید!')
        return

    match message_text:
        case "/start":
            snpfood_user = db.hgetall("accounts")
            if len(snpfood_user) > 0:
                for k,v in snpfood_user.items():
                    phone = k.decode()
                    username = v.decode()
                text = f"""در حال حاضر حساب دارید:\nشماره تلفن: {phone}\nیوزرنیم اسنپ: {username}"""
                await event.respond(text)
                return
            else:
                async with bot.conversation(user_id) as conv:
                    await conv.send_message('شما در اسنپ ثبت نام نکردید، لطفا شماره تلفن خود را وارد کنید')
                    resp1 = await conv.get_response()
                    while len(resp1.text) != 11:
                        await conv.send_message('لطفا حتما شماره 11 رقمی وارد کنید')
                        resp1 = await conv.get_response()
                    try:
                        user = req.login(str(resp1.text))
                    except Exception as e:
                        await event.respond(e)
                        return
                    if user == True:
                        await conv.send_message('کد ارسال شده را وارد نمایید (5 رقمی)')
                        resp2 = await conv.get_response()
                        while len(resp2.text) != 5:
                            await conv.respond("کد وارد شده باید حتما 5 رقم باشد")
                            resp2 = await conv.get_response()
                        try:
                            user = req.authenticate(resp1.text, resp2.text)
                        except Exception as e:
                            await event.respond(str(e))
                            return
                        count = 5
                        while user == False:
                            count -= 1
                            await conv.send_message(f'کد اشتباه است، تعداد تلاش های مجاز باقی مانده: {count}')
                            resp2 = await conv.get_response()
                            try:
                                user = req.authenticate(resp1.text, resp2)
                            except Exception as e:
                                await event.respond(e)
                                return
                    else:
                        await conv.respond("ثبت شماره تلفن با خطا روبرو شد، لطفا دوباره تلاش کنید.")
                if user != False:
                    text = f"""ثبت نام انجام شد:\nشماره تلفن: {user['data']['user']["username"]}\nیوزرنیم اسنپ: {user['data']['user']["id"]}"""
                    await event.respond(text)
                    return
                await event.respond("couldn't login!")
                return
        case "/reset":
            async with bot.conversation(user_id) as conv:
                await conv.send_message('جهت ثبت نام در اسنپ فود، لطفا شماره تلفن خود را وارد کنید')
                resp1 = await conv.get_response()
                while len(resp1.text) != 11:
                    await conv.send_message('لطفا حتما شماره 11 رقمی وارد کنید')
                    resp1 = await conv.get_response()
                try:
                    user = req.login(str(resp1.text))
                except Exception as e:
                    await event.respond(e)
                    return
                if user == True:
                    await conv.send_message('کد ارسال شده را وارد نمایید (5 رقمی)')
                    resp2 = await conv.get_response()
                    while len(resp2.text) != 5:
                        await conv.respond("کد وارد شده باید حتما 5 رقم باشد")
                        resp2 = await conv.get_response()
                    try:
                        user = req.authenticate(resp1.text, resp2.text)
                    except Exception as e:
                        await event.respond(str(e))
                        return
                    count = 5
                    while user == False:
                        count -= 1
                        await conv.send_message(f'کد اشتباه است، تعداد تلاش های مجاز باقی مانده: {count}')
                        resp2 = await conv.get_response()
                        try:
                            user = req.authenticate(resp1.text, resp2)
                        except Exception as e:
                            await event.respond(e)
                            return
                else:
                    await conv.respond("ثبت شماره تلفن با خطا روبرو شد، لطفا دوباره تلاش کنید.")
            if user != False:
                text = f"""ثبت نام انجام شد:\nشماره تلفن: {user['data']['user']["username"]}\nیوزرنیم اسنپ: {user['data']['user']["id"]}"""
                await event.respond(text)
                return
            await event.respond("couldn't login!")
            return
        case "tasks":
            pending = asyncio.all_tasks()
            print(pending)
        case "/update_proxy":
            await req.check_connection()
            await event.respond("done!")
        case "/build":
            message = await event.reply("در حال پردازش...")
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(pool, rebuild_basket, user_id)
            await bot.edit_message(user_id, message, str(result))
        case "استارت":
            path = 'files/combo_sample.txt'
            with open(path, 'r') as f:
                datas = f.read()
                text_lines = datas.split('\n')
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = await loop.run_in_executor(pool, voucher_checker, user_id, text_lines)
            await event.respond("چک کد تخفیف شروع شد")
        case "استپ":
            for task in asyncio.all_tasks():
                if task.get_name() == "vouchering":
                    result = task.cancel()
                    print(result)
            await event.respond("برنامه متوقف شد")
        case "دیتا":
            await event.respond("لیست کد های تخفیف")
            for i in db.hgetall("correct_codes"):
                await event.respond(i.decode())
            await event.respond("پایان لیست")
        case "آمار":
            tested_codes = db.get("tested_codes")
            correct_codes = db.hlen("correct_codes")
            path = 'files/combo_sample.txt'
            with open(path, 'r') as f:
                datas = f.read()
                text_lines = datas.split('\n')
                line_count = len(text_lines)
            text = f"""تعداد کد های تست شده: {tested_codes.decode()}
تعداد کد های درست: {correct_codes}
تعداد کل کد ها: {line_count}"""
            await event.respond(text)

    if '/combo' in event.raw_text:
        path = 'files/combo.txt'
        code = re.search(r"(\w|\d)*\:(\w|\d)*", event.raw_text).group()
        length = re.search(r"\s\d+\s*", event.raw_text).group()
        if code:
            all_possible = code.split(":")
            static = all_possible[0]
            dynamic = all_possible[1]
            pattern = []
            while len(pattern) < int(length):
                res = ""
                for char in dynamic:
                    if char in string.ascii_letters[:]:
                        res += random.choice(string.ascii_letters[:]).lower()
                    elif int(char) in range(10):
                        res += str(random.randint(0,9))
                pattern.append(static + res)
            result = ""
            for elem in pattern:
                result += elem + "\n"
            with open(path, "w") as f:
                f.write(str(result))
                f.close()
            await bot.send_file(user_id, path)

    if combo_file:
        path = 'files/combo_sample.txt'
        await event.download_media(path)
        await event.respond("فایل کمبو ذخیره شد")

    if "/check_voucher" in event.raw_text:
        command = event.raw_text
        code = command.replace("/check_voucher ", "")
        res = req.check_voucher(str(code))
        if 'error' in res:
            await event.reply(res["error"]["message"])
        else:
            await event.reply("کد تخفیف فعال است")
        return


