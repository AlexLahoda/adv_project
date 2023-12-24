from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import aiohttp
import json
from keyboard import make_keyboard

API_KEY = ""
router = Router()

period = ['now', '1 day ahead', '2 days ahead', '3 days ahead', '4 days ahead']

class GetWeather(StatesGroup):
    choosing_period = State()
    choosing_location = State()


@router.message(StateFilter(None), Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        text="Choose period: ",
        reply_markup=make_keyboard(period)
    )
    await state.set_state(GetWeather.choosing_period)

@router.message(StateFilter(GetWeather.choosing_period), F.text.in_(period))
async def cmd_period(message: Message, state: FSMContext):
    await state.update_data(date = message.text.lower())
    button = KeyboardButton(text="Send my geo", request_location=True)
    builder = ReplyKeyboardBuilder()
    builder.add(button)
    await message.answer(
        text="Send me your location to get weather",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.set_state(GetWeather.choosing_location)

@router.message(StateFilter(GetWeather.choosing_location), F.location)
async def cmd_location(message: Message, state: FSMContext):
    place = (message.location.latitude,message.location.longitude)
    period = await state.get_data()
    res = await weather_req(place, period['date'])
    await message.answer(
       res
    )
    # Устанавливаем пользователю состояние "выбирает название"
    await state.clear()

@router.message(StateFilter(GetWeather.choosing_location), F.text)
async def cmd_text(message: Message, state: FSMContext):
    place = (message.text.strip().lower(),)
    period = await state.get_data()
    res = await weather_req(place, period['date'])
    await message.answer(
        res
    )
    # Устанавливаем пользователю состояние "выбирает название"
    await state.clear()

async def weather_req(place, period):
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
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        res = await response.json()
    
    with open('res.json', 'w') as f:
        json.dump(res, f, indent=4)
    
    resp = ''

    def parse(obj, t=None):
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
    
    if res['cod'] != '200':
        resp = res["message"]
        return resp
    if 'list' in res:
        for i in res['list']:
            resp += parse(i, True)
    else:
        resp = parse(res)
    return resp