from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import aiohttp
import json
from keyboard import make_keyboard


API_KEY = "weather_api"
router = Router()

period = ['now', '1 day ahead', '2 days ahead', '3 days ahead', '4 days ahead']


class GetWeather(StatesGroup):
    choosing_period = State()
    choosing_location = State()


@router.message(StateFilter(None), Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    """
    Catch messages with command /start, when FSM state is None
    """
    await message.answer(
        text="Choose period: ",
        reply_markup=make_keyboard(period)
    )
    await state.set_state(GetWeather.choosing_period)


@router.message(StateFilter(GetWeather.choosing_period), F.text.in_(period))
async def cmd_period(message: Message, state: FSMContext):
    """
    Catch all messages with text in period-list, when FSM state is choosing period
    """
    await state.update_data(date = message.text.lower())
    try:
        with open('users_loc.json', 'r') as f:
            users = json.load(f)
    except:
        with open('users_loc.json', 'w') as f:
            users={}
            json.dump(users, f)    
    builder = ReplyKeyboardBuilder()
    button = KeyboardButton(text="Send my geo", request_location=True)
    builder.add(button)
    if str(message.from_user.id) in users:
        button1 = KeyboardButton(text=f"{users[str(message.from_user.id)][0]}")
        builder.add(button1)
    await message.answer(
        text="Type your city or send me your location to get weather",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.set_state(GetWeather.choosing_location)


@router.message(StateFilter(GetWeather.choosing_location), F.location|F.text)
async def cmd_location(message: Message, state: FSMContext):
    """
    Catch all messages with location data or text, when FSM state is choosing location
    """
    if message.text != None:
        place = (message.text.strip().lower(),)
    else:
        place = (message.location.latitude,message.location.longitude)
    period = await state.get_data()
    res = await weather_req(place, period['date'], state)
    with open('users_loc.json', 'r') as f:
        users = json.load(f)
    if str(message.from_user.id) in users and users[str(message.from_user.id)] == place:
        pass
    elif "city not found" != res[0:14:1]:
        place = await state.get_data()
        users[str(message.from_user.id)] = (place['place'],)
    with open('users_loc.json', 'w') as f:
        json.dump(users, f)
    await message.answer(
       res, 
       reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


async def weather_req(place, period, state: FSMContext):
    """
    Make request to openweather, parse response, return it to handler
    """
    if len(place) > 1: 
        query = f"lat={place[0]}&lon={place[1]}"
    else:
        query = f"q={place[0]}"
    if period == 'now':
        url = f'http://api.openweathermap.org/data/2.5/weather?{query}&appid={API_KEY}&units=metric'
        print(url)
    else:
        timest = int(period[0]) * 8
        url = f"http://api.openweathermap.org/data/2.5/forecast?{query}&cnt={timest}&appid={API_KEY}&units=metric"
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            res = await response.json()
    except Exception as e:
        return e

    with open('res.json', 'w') as f:
        json.dump(res, f, indent=4)
    
    resp = ''

    def parse(obj, t=None):
        """
        Parse json data to string
        """
        weather = obj["weather"][0]["description"]
        wind = obj["wind"]["speed"]
        feels = obj["main"]["feels_like"]
        q=''
        if t:
            q = obj["dt_txt"]
        ret = f'''{q}
Temp🌡: {obj["main"]["temp_min"]}-{obj["main"]["temp_max"]}
Feels: {feels}{'🥶' if feels<0 else '😰' if feels<5 else '😊'}
Weather: {weather}{'🌧' if 'rain' in weather else '❄️' if 'snow' in weather else '☁️'if 'cloud' in weather else ''}
Wind{'💨' if wind>7 else '🌬'if wind>3 else ''}: {wind}


'''
        return ret
    
    if int(res['cod']) < 300:
        if 'list' in res:
            for i in res['list']:
                resp += parse(i, True)
            await state.update_data(place=f"{res['city']['name']}, {res['city']['country']}")
        else:
            resp = parse(res)
            await state.update_data(place=f"{res['name']}, {res['sys']['country']}")
    else:
        resp = res["message"]
    return resp + '\n\n' + 'To one more request type "/start"' + '\n'