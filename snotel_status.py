import smtplib
import ssl
import tempfile
import constants as const
from datetime import datetime as dt
import pandas as pd
import requests
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def read_snotel(station: str, url: str):
    snoreq = requests.get(url, headers=const.HEADERS)
    if snoreq.status_code != 200:
        return None
    with tempfile.TemporaryFile() as tmp:
        tmp.write(snoreq.content)
        tmp.seek(0)
        df = pd.read_csv(tmp, comment='#')
    df['Snow Depth (in)'] = df['Snow Depth (in)'].clip(0, None)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index(df['Date'])
    roll_df = df['Snow Depth (in)'].rolling('3h').mean().dropna()
    return roll_df.iloc[-1]


def email_snow_depth(account: str, subject: str, message: str):
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
        msg.set_content(message)
        smtp.send_message(msg)


def main():
    date_label = const.NOW.strftime('%b %d, %H:%M')
    depths = []
    for station, url in const.SNOTEL.items():
        depths.append(f'{station.title()}: {read_snotel(station, url):.1f}')
    subject = f'Snow depth {date_label}'
    message = ' | '.join(depths)
    print(f'{subject}: {message}')
    email_snow_depth('GMAIL', subject, message)


if __name__ == '__main__':
    main()
