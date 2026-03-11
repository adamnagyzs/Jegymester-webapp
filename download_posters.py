"""
Download movie posters for the cinema database
"""
import os
import django
import requests
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinema_project.settings')
django.setup()

from django.core.files.base import ContentFile
from core.models import Movie


POSTER_URLS = {
    'A Keresztapa': 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
    'Csillagok Háborúja: Egy Új Remény': 'https://m.media-amazon.com/images/M/MV5BOTA5NjhiOTAtZWM0ZC00MWNhLThiMzEtZDFkOTk2OTU1ZDJkXkEyXkFqcGdeQXVyMTA4NDI1NTQx._V1_SX300.jpg',
    'Eredet': 'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_SX300.jpg',
    'A Sötét Lovag': 'https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg',
    'Toy Story 4': 'https://m.media-amazon.com/images/M/MV5BMTYzMDM4NzkxOV5BMl5BanBnXkFtZTgwNzM1Mzg2NzM@._V1_SX300.jpg',
    'Dűne': 'https://m.media-amazon.com/images/M/MV5BMDQ0NjgyN2YtNWViNS00YjA3LTkxNDktYzFkZTExZGMxZDkxXkEyXkFqcGdeQXVyODE5NzE3OTE@._V1_SX300.jpg',
}


posters_dir = Path('media/posters')
posters_dir.mkdir(parents=True, exist_ok=True)

print("Downloading movie posters...")
print("=" * 50)

for movie in Movie.objects.all():
    if movie.title in POSTER_URLS:
        url = POSTER_URLS[movie.title]
        
        try:
            print(f"Downloading: {movie.title}...", end=" ")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            

            filename = f"{movie.title.replace(' ', '_').replace(':', '').lower()}.jpg"
            

            movie.poster.save(filename, ContentFile(response.content), save=True)
            
            print(f"✓ Saved as {filename}")
            
        except requests.RequestException as e:
            print(f"✗ Failed: {e}")
    else:
        print(f"No URL for: {movie.title}")

print("=" * 50)
print("Done! Movie posters have been added.")
