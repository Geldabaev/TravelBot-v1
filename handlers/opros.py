from cgitb import handler
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from create_bot import dp, bot
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher.filters import Text
import time
import datetime
from keyboards import sko_vz_markup, kb_today_tomorrow, pos_bes_markup, kb_tel, dop_in, kb_ver_isp, zz_zayav, net_markup
from handlers.client import sp_phone
import os.path
import re
from excel_loader import loader
from excel_loader import edit2, correct_number
from handlers.client import msg_id_user, msg_id_bot, name_sud_vrem
from keyboards import kb_client_menu
import asyncio


user_name = {}
sp_tur = {}
data_day = {}
vz_sk = {}
stoim_vz = {}
posadoch = {}
besplat = {}
stoim_chi_1 = {}
naz_bes = {}
nom_tel_tur = {}
dop_inf = {}

edit = {'is': 0}

# создадим список на команд кторый должен сработать данный хендлер
commands_data = ['Красная Поляна', 'Обзорная Сочи', '33 Водопада', 'Воронцовские пещеры', 'Каньоны Псахо (джип-тур)',
                 'Мамонтово Ущелье (джип-тур)', 'Золотое Кольцо',
                 'Абхазское застолье', 'Термальные Источники', 'Абхазский драйв (джип-тур)', 'Морская прогулка',
                 'Рыбалка в море', 'Дайвинг', 'АРЕНДА ЯХТ',
                 'Параплан', 'Шашлыки (индивидуальный)', 'Вечеринка в лесу',
                 'Билеты на мероприятия', 'Эпоха времени', 'Солохаул (джип-тур)', 'Квадроциклы',
                 'Конные Прогулки', 'Аквапарк', 'Сафари Парк', 'Форт Боярд', 'Квесты', 'ДРУГОЕ', 'Рафтинг']

# список исключений
commands_excep = ['АРЕНДА ЯХТ', 'Вертолёт']#, 'ИНДИВИДУАЛЬНЫЙ ТУР', ]

dataButtons = ['Индивид.', 'ДРУГОЕ']

# сегодня завтра
# @dp.message_handler(commands='укажите...', state=None)
async def dat_ukaz(message : types.Message):
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)
    print("oooooooooooo")
    global user_name, sp_tur
    user_name[message.chat.id] = message.from_user.first_name
    sp_tur[message.chat.id] = message.text
    msgBot = await bot.send_message(message.chat.id, 'Выберите ДАТУ', reply_markup=kb_today_tomorrow)
    msg_id_bot.append(msgBot)


# сработает на сегодня или завтра
class FSMAdvvod(StatesGroup):
    # окна ввода данных
    today_or_tomorrow = State()
    vzrosl_skok = State()
    posad = State()
    besp_stoim = State()
    stoim_chid_1 = State()
    naz_bes = State()
    naz_ost = State()
    nom_tel_tur = State()
    dop_inf = State()


# @dp.message_handler(content_types=['text'], state=FSMAdvvod.data_vod)
async def today_or_tomorrow(message: types.Message):
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)
    # ждем следующий
    await FSMAdvvod.vzrosl_skok.set()
    user_name[message.chat.id] = message.from_user.first_name
    if message.text == 'Сегодня':
        # актуальная дата
        today = datetime.datetime.now()
        today = today.strftime('%d.%m.%Y')
        data_day[message.chat.id] = today
    elif message.text == 'Завтра':
        # завтращний дата
        today2 = datetime.date.today()
        tomorrow = today2 + datetime.timedelta(days=1)
        tomorrow = tomorrow.strftime('%d.%m.%Y')
        data_day[message.chat.id] = tomorrow
    # временно показываем дату
    msgBot = await bot.send_message(message.chat.id, f"Ваша дата: {data_day[message.chat.id]}")
    msg_id_bot.append(msgBot)
    # time.sleep(1)
    # и удаляем
    # await msg.delete()

    msgBot = await bot.send_message(message.chat.id, "Сколько взрослых?", reply_markup=sko_vz_markup)
    msg_id_bot.append(msgBot)
    msgBot = await bot.send_message(message.chat.id, "Или отправьте свой вариант")
    msg_id_bot.append(msgBot)


# Ловим первый ответ
# @dp.message_handler(state=FSMAdvvod.vzrosl_skok)
async def load_vzrosl_skok(message: types.Message, state: FSMContext):
    global vz_sk
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)
    try:
        iit = int(message.text)
    except Exception as ex:
        msgBot = await bot.send_message(message.chat.id, "Введите число!")
        msg_id_bot.append(msgBot)
        return  # чтобы преспрашивали

    async with state.proxy() as data:
        data["vzrosl_skok"] = message.text
        vz_sk[message.chat.id] = message.text
    await FSMAdvvod.next() # режим ожидания

    msgBot = await bot.send_message(message.chat.id, "Стоимость на одного взрослого?")
    msg_id_bot.append(msgBot)


# Ловим второй ответ
# @dp.message_handler(state=FSMAdvvod.posad)
async def load_stoim_vz(message: types.Message, state: FSMContext):
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)
    # принимает занчаени от 3 до 4 знаков, исключениями являются «ИНДИВИДУАЛЬНЫЕ ТУР», «АРЕНДА ЯХТ», «Вертолёт»
    if sp_tur[message.chat.id] not in commands_excep:
        try:
            iit = int(message.text)
            count = len(message.text)

            async with state.proxy() as data:
                data["stoim_vz"] = message.text
                stoim_vz[message.chat.id] = message.text
            await FSMAdvvod.next()  # режим ожидания

            msgBot = await bot.send_message(message.chat.id, "Сколько детей с посадочным местом?", reply_markup=pos_bes_markup)
            msg_id_bot.append(msgBot)

        except Exception as ex:
            msgBot = await bot.send_message(message.chat.id, "Введите число!")
            msg_id_bot.append(msgBot)
    else:
        try:
            iit = int(message.text)
            async with state.proxy() as data:
                data["stoim_vz"] = message.text
                stoim_vz[message.chat.id] = message.text
            await FSMAdvvod.next()  # режим ожидания

            msgBot = await bot.send_message(message.chat.id, "Сколько детей с посадочным местом?", reply_markup=pos_bes_markup)
            msg_id_bot.append(msgBot)
        except:
            msgBot = await bot.send_message(message.chat.id, "Введите число!")
            msg_id_bot.append(msgBot)





# Ловим третий ответ
# @dp.message_handler(state=FSMAdvvod.besp_stoim)
async def price_child_1_or_besplat(message: types.Message, state: FSMContext):
    global posadoch, besplat, punkt, stoim_chi_1
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)
    try:
        iit = int(message.text)
    except Exception as ex:
        msgBot = await bot.send_message(message.chat.id, "Введите число!")
        msg_id_bot.append(msgBot)
        return  # чтобы преспрашивали
    if message.text == '0':
        punkt = 1
        async with state.proxy() as data:
            data["price_child_1_or_besplat"] = message.text
            posadoch[message.chat.id] = message.text
        await FSMAdvvod.next() # режим ожидания

        msgBot = await bot.send_message(message.chat.id, "Сколько детей БЕСПЛАТНО?", reply_markup=pos_bes_markup)
        msg_id_bot.append(msgBot)
        # если стоимость на одного ребенка не спросили, то нужно указть пропуск, для excel заголовки для нее
        stoim_chi_1[message.chat.id] = "0"
    elif message.text != '0':
        punkt = 2
        async with state.proxy() as data:
            data["price_child_1_or_besplat"] = message.text
            posadoch[message.chat.id] = message.text
        await FSMAdvvod.next()  # режим ожидания

        msgBot = await bot.send_message(message.chat.id, "Стоимость на одного ребенка?")
        msg_id_bot.append(msgBot)


# Ловим четвертый ответ
# @dp.message_handler(state=FSMAdvvod.stoim_chid_1)
async def load_stoim_bespl(message: types.Message, state: FSMContext):
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)
    # чтобы принимал только в цифрах
    try:
        number = int(message.text)
    except:
        msgBot = await bot.send_message(message.chat.id, "Введите число!")
        msg_id_bot.append(msgBot)
        return
    # если равно 1, значит он попал в пункт сколько детей бесплатно
    if punkt == 1:
        async with state.proxy() as data:
            data["besplat"] = message.text
            besplat[message.chat.id] = message.text
        msgBot = await bot.send_message(message.chat.id, "Введите название остановки")
        print("Введите 1")
        msg_id_bot.append(msgBot)
    # если равно 1, значит он попав в пункт стоимость на одного ребенка, в таком случае его нужно спросить сколько детей бесплатно
    elif punkt == 2:
        async with state.proxy() as data:
            data["stoim_chi_1"] = message.text
            stoim_chi_1[message.chat.id] = message.text
            msgBot = await bot.send_message(message.chat.id, "Сколько детей БЕСПЛАТНО?")
            msg_id_bot.append(msgBot)
    await FSMAdvvod.next()  # режим ожидания


# Ловим четвертый пятый
# @dp.message_handler(state=FSMAdvvod.naz_bes)
async def spr_naz_zvat_bespl(message: types.Message, state: FSMContext):
    global naz_bes
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)

    try:
        iit = int(message.text)
    except Exception as ex:
        msgBot = await bot.send_message(message.chat.id, "Введите число!")
        msg_id_bot.append(msgBot)
        return  # чтобы преспрашивали
    # берем название остановки
    if punkt == 1:
        async with state.proxy() as data:
            data["naz_bes"] = message.text
            naz_bes[message.chat.id] = message.text
            # так как ничего в данном хендлере не нужно от пользователя, то хендлер будет стоять пока он ничего не отправит...
            # чтобы этого не произошло вызываем хендлер как обычную функцию
            await ber_naz(message, state)
    # берем сколько детей бесплатно и говорим ведите название остановки
    elif punkt == 2:
        async with state.proxy() as data:
            data["stoim_chi_1"] = message.text
            besplat[message.chat.id] = message.text
            msgBot = await bot.send_message(message.chat.id, "Введите название остановки")
            msg_id_bot.append(msgBot)
    await FSMAdvvod.next()  # режим ожидания


# Ловим шестой ответ
# @dp.message_handler(state=FSMAdvvod.naz_ost)
async def ber_naz(message: types.Message, state: FSMContext):
    if punkt == 2:
        msgUser = message  # берем msg пользователя, чтобы потом удалить его
        msg_id_user.append(msgUser)
    async with state.proxy() as data:
        data["naz_ost"] = message.text
        naz_bes[message.chat.id] = message.text
    msgBot = await bot.send_message(message.chat.id, "Введите номер телефона туриста", reply_markup=kb_tel)
    msg_id_bot.append(msgBot)
    await FSMAdvvod.next() # режим ожидания


# Ловим седьмой ответ
# @dp.message_handler(state=FSMAdvvod.nom_tel_tur)
async def load_nom_tel_tur(message: types.Message, state: FSMContext):
    global nom_tel_tur
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)
    # result = re.match(r'\b\+?[7,8](\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2})\b', message.text)
    result = re.match(r'(\+7|8|7).*?(\d{3}).*?(\d{3}).*?(\d{2}).*?(\d{2})', message.text)
    result = bool(result)
    if result:
        async with state.proxy() as data:
            data["nom_tel_tur"] = message.text
            nom_tel_tur[message.chat.id] = message.text
        await FSMAdvvod.next() # режим ожидания
        if 1 in name_sud_vrem:
            msgBot = await bot.send_message(message.chat.id, "Номер телефона принят")
            print(msgBot, "Номер телефона принят111")
            msg_id_bot.append(msgBot)
        else:
            msgBot = await bot.send_message(message.chat.id, "Номер телефона принят", reply_markup=net_markup)
            print(msgBot, "Номер телефона принят222")
            msg_id_bot.append(msgBot)
        if 1 in name_sud_vrem:
            msgBot = await bot.send_message(message.chat.id, "Введите название судна и время отправления")
            msg_id_bot.append(msgBot)
        else:
            msgBot = await bot.send_message(message.chat.id, "Дополнительная информация", reply_markup=dop_in)
            msg_id_bot.append(msgBot)
    else:
        msgBot = await bot.send_message(message.chat.id, "Некорректный номер")
        msg_id_bot.append(msgBot)


# ловим восьмой последний ответ и используем полученные данные
# @dp.message_handler(state=FSMAdvvod.dop_inf)
async def load_dop_inf(message: types.Message, state: FSMContext):
    global msg, isp
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)
    async with state.proxy() as data:
        data["dop_inf"] = message.text

        dop_inf[message.chat.id] = message.text

    isp = await bot.send_message(message.chat.id, f"Проверьте данные:\n"
                        f"Агент: {user_name[message.chat.id]} {sp_phone[message.chat.id]}\n"
                        f"Тур: {sp_tur[message.chat.id]}\n"
                        f"Дата: {data_day[message.chat.id]}\n"
                        f"Взрослые: {vz_sk[message.chat.id]} x {stoim_vz[message.chat.id]}\n"
                        f"Дети (платно): {posadoch[message.chat.id]} x {stoim_chi_1[message.chat.id]}\n"
                        f"Дети (бесплатно: {besplat[message.chat.id]}\n"
                        f"Остановка: {naz_bes[message.chat.id]}\n"
                        f"Телефон туриста: {nom_tel_tur[message.chat.id]}\n"
                        f"Доп. информация: {dop_inf[message.chat.id]}", reply_markup=kb_ver_isp)


    # sql_add(state)
    await state.finish() # выходим из состояний


#после подверждения правильности данных даем номер заявки
# @dp.message_handler(lambda message: 'ВСЁ ВЕРНО' in message.text)
async def verno(message : types.Message):
    global number
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)

    for i in msg_id_bot:  # удаляем все лишнее сообщения от бота
        # await asyncio.sleep(0.5)
        print(i.text, "Удаляю...................")
        await i.delete()
    msg_id_bot.clear()


    for i in msg_id_user: # удаляем все лишнее сообщения от пользователя
        if i is not None:
            # await asyncio.sleep(0.4)
            print(i.text, "Удаляю...................2")
            await i.delete()
        else:
            continue
    msg_id_user.clear()



    # чтобы не добавлялся к номеру заявки, и не отправлял что ваша заявка на однин больше, так как мы эту ячейку не трогаем при корректировки
    if edit['is'] == 0:
        # создаем файл с номером заявки и каждым разом беря оттуда номер, увеличивая на одну будем перезаписывать
        # сначала проверим есть ли такой файл, если есть перезапишем, если нет создадим
        check_file = os.path.exists('file_number.txt')
        if check_file:
            # файл есть, откроем, преведем значение в int, и прибавим 1
            with open('file_number.txt', 'r', encoding='utf-8') as file:
                file = file.read()
            number = int(file) + 1
            # перезапишем новое значение
            with open('file_number.txt', 'w', encoding='utf-8') as file:
                file.write(str(number))
        else:
            number = '1'
            # фала нет, создадим с значением 1
            with open('file_number.txt', 'w', encoding='utf-8') as file:
                file.write(number)

        # пресылаем в группу
        group_id = '-1001632324261'
        # next_id = msg.message_id
        # await bot.forward_message(group_id, message.chat.id, next_id)
        # # Отпрвляем сообщение в группу
        await bot.send_message(group_id, f"Агент: {user_name[message.chat.id]} {sp_phone[message.chat.id]}")
        await bot.send_message(group_id, f"Номер заявки: {number}\n"
                                         f"Тур: {sp_tur[message.chat.id]}\n"
                                         f"Дата: {data_day[message.chat.id]}\n"
                                         f"Взрослые: {vz_sk[message.chat.id]} x {stoim_vz[message.chat.id]}\n"
                                         f"Дети (платно): {posadoch[message.chat.id]} x {stoim_chi_1[message.chat.id]}\n"
                                         f"Дети (бесплатно): {besplat[message.chat.id]}\n"
                                         f"Остановка: {naz_bes[message.chat.id]}\n"
                                         f"Телефон туриста: {nom_tel_tur[message.chat.id]}\n"
                                         f"Доп. информация: {dop_inf[message.chat.id]}")

        # # Сохраним данные
        text_im = loader(edit, message.chat.id, user_name[message.chat.id], sp_phone[message.chat.id], sp_tur[message.chat.id],
                         data_day[message.chat.id], vz_sk[message.chat.id], stoim_vz[message.chat.id], posadoch[message.chat.id],
                         stoim_chi_1[message.chat.id], besplat[message.chat.id], naz_bes[message.chat.id],
                         nom_tel_tur[message.chat.id], dop_inf[message.chat.id], number)
        # сообшим что заявка передана диспетчеру
        await bot.send_message(message.chat.id, text_im)

        # await bot.send_message(message.chat.id, f"ЗАЯВКА ПЕРЕДАНА ДИСПЕТЧЕРУ")
        await bot.send_message(message.chat.id, f"Номер вашей заявки: {number}", reply_markup=zz_zayav)





    else:
        # # Сохраним данные
        text_im = loader(edit, message.chat.id, user_name[message.chat.id], sp_phone[message.chat.id],
                         sp_tur[message.chat.id],
                         data_day[message.chat.id], vz_sk[message.chat.id], stoim_vz[message.chat.id],
                         posadoch[message.chat.id],
                         stoim_chi_1[message.chat.id], besplat[message.chat.id], naz_bes[message.chat.id],
                         nom_tel_tur[message.chat.id], dop_inf[message.chat.id])
        # сообшим что заявка передана диспетчеру
        await bot.send_message(message.chat.id, "Ваша заявка изменена!", reply_markup=zz_zayav)
        group_id = '-1001632324261'
        edit['is'] = 0
        edit2['is'] = 0
        """********************************"""
        # сообщим в группе что заявка скорретирована
        await bot.send_message(group_id, f"Агент: {user_name[message.chat.id]} {sp_phone[message.chat.id]}")
        await bot.send_message(group_id, f"Заявка {correct_number['cor']} скорректирована:\n"
                                                      f"Тур: {sp_tur[message.chat.id]}\n"
                                                      f"Дата: {data_day[message.chat.id]}\n"
                                                      f"Взрослые: {vz_sk[message.chat.id]} x {stoim_vz[message.chat.id]}\n"
                                                      f"Дети (платно): {posadoch[message.chat.id]} x {stoim_chi_1[message.chat.id]}\n"
                                                      f"Дети (бесплатно): {besplat[message.chat.id]}\n"
                                                      f"Остановка: {naz_bes[message.chat.id]}\n"
                                                      f"Телефон туриста: {nom_tel_tur[message.chat.id]}\n"
                                                      f"Доп. информация: {dop_inf[message.chat.id]}"
                                     )


# после подверждения правильности данных даем номер заявки
# @dp.message_handler(lambda message: 'ИСПРАВИТЬ' in message.text)
async def ispravit(message : types.Message):
    msgUser = message  # берем msg пользователя, чтобы потом удалить его
    msg_id_user.append(msgUser)

    msgBot = await bot.send_message(message.chat.id, f"Повторите заявку", reply_markup=kb_client_menu)
    msg_id_bot.append(isp)
    msg_id_bot.append(msgBot)


# Регистрируем хендлеры
def register_handlers_opros(dp : Dispatcher):
    dp.register_message_handler(dat_ukaz, lambda message: message.text in commands_data or message.text in dataButtons)
    # машинное состояние
    dp.register_message_handler(today_or_tomorrow, lambda message: message.text in 'Сегодня' or message.text in 'Завтра', state=None)
    dp.register_message_handler(load_vzrosl_skok, state=FSMAdvvod.vzrosl_skok)
    dp.register_message_handler(load_stoim_vz, state=FSMAdvvod.posad)
    dp.register_message_handler(price_child_1_or_besplat, state=FSMAdvvod.besp_stoim)
    dp.register_message_handler(load_stoim_bespl, state=FSMAdvvod.stoim_chid_1)
    dp.register_message_handler(spr_naz_zvat_bespl, state=FSMAdvvod.naz_bes)
    dp.register_message_handler(ber_naz, state=FSMAdvvod.naz_ost)
    dp.register_message_handler(load_nom_tel_tur, state=FSMAdvvod.nom_tel_tur)
    dp.register_message_handler(load_dop_inf, state=FSMAdvvod.dop_inf)
    dp.register_message_handler(verno, lambda message: 'ВСЁ ВЕРНО' in message.text)
    dp.register_message_handler(ispravit, lambda message: 'ИСПРАВИТЬ' in message.text)

