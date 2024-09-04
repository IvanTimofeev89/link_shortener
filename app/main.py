from flask import Blueprint, render_template, request, redirect, send_file

import os
import pandas as pd
from dotenv import load_dotenv
import aiohttp
import asyncio
import io

load_dotenv()

main_bp = Blueprint('main', __name__)

FINAL_FILE_NAME = os.getenv('FINAL_FILE_NAME')

VK_TOKEN = os.getenv('VK_TOKEN')
BASE_URL = os.getenv('BASE_URL')
VK_API_VERSION = os.getenv('VK_API_VERSION')



@main_bp.route('/', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'GET':
        return render_template('upload_file.html')

    if request.method == 'POST':
        if request.files['file'].filename == '':
            return redirect(request.url)

        file = request.files['file']

        df = pd.read_excel(file, usecols=[0], header=None)
        links = df.iloc[:, 0].tolist()
        dict_links = dict.fromkeys(links)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        shortened_links = loop.run_until_complete(fetch_shortened_links(dict_links))

        df_shortened = pd.DataFrame(list(shortened_links.items()), columns=['Original Link', 'Shortened Link'])

        output = io.BytesIO()
        df_shortened.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name=FINAL_FILE_NAME,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


async def fetch_shortened_links(links_dict):
    semaphore = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_link(session, semaphore, link) for link in links_dict.keys()]
        results = await asyncio.gather(*tasks)
    return dict(zip(links_dict.keys(), results))

async def fetch_link(session, semaphore, link):
    async with semaphore:
        async with session.get(BASE_URL, params={'access_token': VK_TOKEN, 'v': VK_API_VERSION, 'url': link}) as response:
            if response.status == 200:
                data = await response.json()
                return data['response'].get('short_url', link)
            else:
                return link