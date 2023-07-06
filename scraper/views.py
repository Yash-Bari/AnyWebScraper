import os
import shutil
import tempfile
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import requests
import youtube_dl
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# Function to create a directory if it doesn't exist
def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_image(url, directory):
    response = requests.get(url)
    filename = os.path.basename(url)

    # Remove unsupported characters from the file name
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    with open(os.path.join(directory, filename), 'wb') as f:
        f.write(response.content)



def scrape_website_data(url, option):
    # Create a directory for the chosen option
    create_directory(option)

    if option == 'images':
        # Scrape and download images
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img')
        for image in images:
            image_url = urljoin(url, image['src'])
            download_image(image_url, option)

    elif option == 'videos':
        # Scrape and download videos using youtube-dl
        ydl_opts = {
            'outtmpl': os.path.join(option, '%(title)s.%(ext)s'),
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    elif option == 'text':
        # Scrape and save text
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        # Fix encoding issue by specifying 'utf-8' encoding when writing to file
        with open(os.path.join(option, 'text.txt'), 'w', encoding='utf-8') as f:
            f.write(text)

    else:
        print("Invalid option. Please choose 'images', 'videos', or 'text'.")



def index(request):
    return render(request, 'index.html')


@csrf_exempt
def scrape(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        option = request.POST.get('option')

        # Scrape the website
        scrape_website_data(url, option)

        # Create a temporary directory to store the scraped files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Move the scraped files to the temporary directory
            shutil.move(option, temp_dir)

            # Create a zip file of the temporary directory
            shutil.make_archive(temp_dir, 'zip', temp_dir)

            # Read the zip file
            with open(temp_dir + '.zip', 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename= scraped_file.zip'
                return response

    return HttpResponse('Invalid request.')
