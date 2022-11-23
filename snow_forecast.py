from collections import defaultdict
from PIL import Image
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
from datetime import datetime as dt, timedelta, timezone
import os
import smtplib
import ssl
from time import sleep
import random
import requests
from email.message import EmailMessage
from dotenv import load_dotenv
import tempfile
import constants as const

load_dotenv()


def get_forecast_period(forecast_dt: dt, hrs: int) -> str:
    """
    Compute the forecast period based on forecast datetime and forecast length (hours)
    Args:
        forecast_dt: forecast datetime
        hrs: forecast length (24, 48, 72)

    Returns:
        formatted string for forecast period, e.g.
        Wed, 11/23/2022 05:00 to Sat, 11/26/2022 05:00
    """
    from_mt = forecast_dt.astimezone()
    from_mt_format = from_mt.strftime('%a, %m/%d/%Y %H:%M')
    to_mt = (forecast_dt + timedelta(hours=hrs)).astimezone()
    to_mt_format = to_mt.strftime('%a, %m/%d/%Y %H:%M')
    return f'{from_mt_format} to {to_mt_format}'


def get_snow_forecast(
        location: str, precip_band: np.array, temp_band: np.array,
        precip_palette: Dict[Tuple[int, int], float], temp_palette: Dict[Tuple[int, int], float],
        row_slice: Tuple[int, int], col_slice: Tuple[int, int]
) -> Optional[str]:
    """
    Compute the snow forecast from forecasted accumulated precipitation
    Args:
        location: location to compute forecast for
        precip_band: precipitation array from precipitation image
        temp_band: temperature array from temperature image
        precip_palette: precipitation palette
        temp_palette: temperature palette
        row_slice: rows to be used from arrays
        col_slice: columns to be used from arrays

    Returns:
        formatted forecast message if precipitation was forecasted within the row/col window, otherwise None, e.g.
        Peaceful Valley: 1.2in
    """
    rfrom, rto = row_slice
    cfrom, cto = col_slice
    precip_colors = precip_band[rfrom:rto, cfrom:cto].flatten()
    temp_colors = temp_band[rfrom:rto, cfrom:cto].flatten()
    stl_ratio = dict(zip(temp_band[const.TEMP_COLOR_PICKER[0], const.TEMP_COLOR_PICKER[1]], const.SNOW_TO_LIQUID))
    df = pd.DataFrame({
        'precip_colors': precip_colors,
        'temp_colors': temp_colors,
    })
    df['precip'] = df['precip_colors'].map(precip_palette)
    df['temp'] = df['temp_colors'].map(temp_palette)
    df['stl'] = df['temp_colors'].map(stl_ratio)
    df['snow'] = df['precip'] * df['stl']

    df_desc = df.describe()
    print(df_desc)
    if pd.isnull(df_desc['snow']['mean']):
        return None
    forecast_text = f"{location.title()}: {df_desc['snow']['mean']:.1f}in"
    return forecast_text


def item_exists(file_path: str) -> bool:
    """
    Checks if a forecast was already downloaded
    Args:
        file_path: datetime labeled forecast path to verify

    Returns:
        True if forecast was already processed in the past, otherwise False
    """
    return os.path.exists(file_path) and os.path.getsize(file_path)


def get_band_and_palette(
        raw_path: str, color_picker: List[List[int], List[int]], mean_scale: np.array
) -> Tuple[np.array, Dict[Tuple[int, int], float]]:
    """
    Reads a forecast image (PNG) and returns it as an array along with
    a dictionary of a reference to the precipitation/temperatures scales
    Args:
        raw_path: path to the PNG image
        color_picker: list of X/Y for scale pixels
        mean_scale: actual values array for precipitation/temperature

    Returns:
        the image as an array and a reference for the scales (truncated dict example: {(680, 42): 0.2})
    """
    image = Image.open(raw_path)
    band = np.array(image)
    palette = dict(zip(band[color_picker[0], color_picker[1]], mean_scale))
    return band, palette


def email_forecast(account: str, subject: str, forecast_message: str):
    """
    Sends the forecast email
    Args:
        account: email account to use when sending out the email (requires app password setup)
        subject: email subject
        forecast_message: message body
    """
    server, user, password = const.SMTP[account]
    context = ssl.create_default_context()
    with smtplib.SMTP(server, 587) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(user, password)

        msg = EmailMessage()
        msg['From'] = user
        msg['To'] = ', '.join(const.RECIPIENTS)
        msg['Subject'] = subject
        msg.set_content(forecast_message)
        smtp.send_message(msg)


def get_forecast_list(now_utc: dt) -> List[dt]:
    """
    Builds a list of possibly available forecasts based on current date.
    It checks current local day and next day (forecasts are released at UTC)
    Args:
        now_utc: current UTC datetime

    Returns:
        a list of possibly available forecast datetime (maximum 8 to be queried)
    """
    year = now_utc.year
    month = now_utc.month
    day = now_utc.day
    nearest_forecast_list = [
        dt(year, month, day - i, hr, tzinfo=timezone.utc) for i in [0, 1] for hr in range(18, -1, -6)
    ]
    return nearest_forecast_list


def get_local_time(now_utc: dt) -> str:
    """
    Converts UTC time to local time zone
    Args:
        now_utc: current UTC datetime

    Returns:
        formatted local datetime
    """
    now_utc = now_utc.replace(tzinfo=timezone.utc)
    local = now_utc.astimezone()
    return local.strftime('%b %d, %H:%M')


def main():
    for forecast in get_forecast_list(const.NOW):
        forecast_sms = defaultdict(list)
        forecast_period = {}
        for hrs in [24, 48, 72]:
            sleep(random.randint(1, 3) + random.random())
            label = f'{forecast.year}{forecast.month:02d}{forecast.day:02d}{forecast.hour:02d}_{hrs:03d}'
            for z, name in const.ZONES.items():
                precip_raw_file = f'{const.DATA_PATH}/precip_raw/raw_{name}_forecast_{label}.png'
                temp_raw_file = f'{const.DATA_PATH}/temp_raw/raw_{name}_forecast_{label}.png'
                if item_exists(precip_raw_file) and item_exists(temp_raw_file):
                    continue
                for i in range(1, 5):
                    sleep(random.randint(1, 3) + random.random())
                    p_url = const.PRECIP_URL.format(
                        i, forecast.year, forecast.month, forecast.day, forecast.hour, hrs, z
                    )
                    try:
                        preq = session.get(p_url, headers=const.HEADERS)
                        break
                    except requests.exceptions.RequestException as e:
                        continue
                for i in range(1, 5):
                    sleep(random.randint(1, 3) + random.random())
                    t_url = const.TEMP_URL.format(
                        i, forecast.year, forecast.month, forecast.day, forecast.hour, hrs, z
                    )
                    try:
                        treq = session.get(t_url, headers=const.HEADERS)
                        break
                    except requests.exceptions.RequestException as e:
                        continue
                if preq.status_code == 200 and treq.status_code == 200:
                    with open(precip_raw_file, 'wb') as raw_image:
                        raw_image.write(preq.content)
                    with open(temp_raw_file, 'wb') as raw_image:
                        raw_image.write(treq.content)
                    p_band, p_palette = get_band_and_palette(
                        precip_raw_file, const.PRECIP_COLOR_PICKER, const.PRECIP_MEAN_SCALE
                    )
                    t_band, t_palette = get_band_and_palette(
                        temp_raw_file, const.TEMP_COLOR_PICKER, const.TEMP_MEAN_SCALE
                    )
                    forecast_period[hrs] = get_forecast_period(forecast, hrs)
                    for area, rc_slice in const.SLICES[z].items():
                        snow_forecast = get_snow_forecast(
                            area, p_band, t_band, p_palette, t_palette, rc_slice['row'], rc_slice['col']
                        )
                        if not snow_forecast:
                            print(f'No precipitation expected in the forecasted area: {area}.')
                            continue
                        msg = f'{snow_forecast}'
                        forecast_sms[hrs].append(msg)
        all_msg = '\n'.join([f'{k}hr:{forecast_period[k]}: ' + ';'.join(v) for k, v in sorted(forecast_sms.items())])
        if all_msg.strip():
            email_forecast('GMAIL', f'Snow forecast {get_local_time(const.NOW)}', all_msg)


# build a global requests Session so cookies are available to all requests
session = requests.Session()
base_req = session.get('https://weather.us', headers=const.HEADERS)

if __name__ == '__main__':
    main()
