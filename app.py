import os
import threading
import re
import unicodedata
from flask import Flask, render_template_string, send_from_directory, request, jsonify
import yt_dlp

app = Flask(__name__)

# Railway'de geçici dosya yazma izni olan dizin
DOWNLOAD_DIR = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def clean_filename(title):
    nfkd_form = unicodedata.normalize('NFKD', title)
    title = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    title = re.sub(r'[^\w\s-]', '', title).strip()
    title = re.sub(r'[-\s]+', '_', title)
    return title

@app.route('/icon.png')
def icon():
    return send_from_directory('static', 'icon.png')

@app.route('/')
def index():
    # Daha önce kullandığımız modern HTML şablonunu buraya yapıştırabilirsin
    return render_template_string(HTML_TEMPLATE) # HTML_TEMPLATE yukarıdaki şık arayüz olsun

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    video_url = data.get('url')
    choice = data.get('format')
    
    ydl_opts = {'quiet': True, 'no_warnings': True}

    if choice == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        })
    else:
        ydl_opts.update({'format': 'bestvideo+bestaudio/best/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            clean_title = clean_filename(info.get('title', 'video'))
            ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f"{clean_title}.%(ext)s")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_real:
                ydl_real.download([video_url])
            
            return jsonify({"status": "success", "message": f"İndirildi: {clean_title}"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Hata: " + str(e)[:50]})

if __name__ == '__main__':
    # Railway PORT değişkenini otomatik atar
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))