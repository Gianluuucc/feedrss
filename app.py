from flask import Flask, request, Response, render_template_string
from scraper import get_news
from email.utils import format_datetime
import time
import socket

app = Flask(__name__)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'

@app.route('/')
def index():
    suggested_base = request.host_url.rstrip('/')
    
    return render_template_string('''
        <!doctype html>
        <html>
        <head>
            <title>Generatore Feed RSS Comune</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                input[type=text] { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
                input[type=submit] { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
                .result { margin-top: 20px; padding: 15px; background: #f0f0f0; word-break: break-all; }
                label { font-weight: bold; margin-top: 15px; display: block; }
                .hint { font-size: 0.8em; color: #666; margin-bottom: 5px; }
            </style>
        </head>
        <body>
            <h1>Generatore Feed RSS per Comuni</h1>
            <form method="get" action="/generate">
                <label>1. Link delle notizie del Comune:</label>
                <input type="text" name="url" placeholder="https://www.comune.matelica.mc.it/..." required>
                
                <label>2. Indirizzo del tuo Server (Base URL):</label>
                <div class="hint">Modifica questo se vuoi usare un IP pubblico o un dominio diverso da localhost.</div>
                <input type="text" name="base_url" value="{{ suggested_base }}">
                
                <br><br>
                <input type="submit" value="Genera Link RSS">
            </form>
        </body>
        </html>
    ''', suggested_base=suggested_base)

@app.route('/generate')
def generate():
    target_url = request.args.get('url')
    base_url = request.args.get('base_url')
    
    if not target_url:
        return "URL mancante", 400
    
    if not base_url:
        base_url = request.url_root.rstrip('/')
    else:
        base_url = base_url.rstrip('/')
    
    # Construct the feed URL
    feed_url = base_url + '/feed?url=' + target_url
    
    return render_template_string('''
        <!doctype html>
        <html>
        <head>
            <title>Feed RSS Generato</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .result { margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 5px; }
                code { font-size: 1.2em; color: #d63384; }
                a { color: #007bff; text-decoration: none; }
            </style>
        </head>
        <body>
            <h1>Ecco il tuo Feed RSS</h1>
            <p>Copia questo link e usalo nel tuo lettore RSS o sistema di invio notizie:</p>
            <div class="result">
                <code>{{ feed_url }}</code>
            </div>
            <p><a href="{{ feed_url }}" target="_blank">Anteprima Feed</a></p>
            <p><a href="/">Torna indietro</a></p>
        </body>
        </html>
    ''', feed_url=feed_url)

@app.route('/feed')
def feed():
    target_url = request.args.get('url')
    if not target_url:
        return "URL mancante", 400
        
    news_items = get_news(target_url)
    
    # Build XML
    xml = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    xml += '<rss version="2.0">\n'
    xml += '<channel>\n'
    xml += f'<title>Notizie da {target_url}</title>\n'
    xml += f'<link>{target_url}</link>\n'
    xml += '<description>Feed RSS generato automaticamente</description>\n'
    
    for item in news_items:
        # Clean title and description to remove invalid XML characters
        title_clean = item["title"].replace(']]>', ']]&gt;')
        desc_clean = item["description"].replace(']]>', ']]&gt;')
        
        xml += '<item>\n'
        xml += f'<title><![CDATA[{title_clean}]]></title>\n'
        xml += f'<link>{item["link"]}</link>\n'
        xml += f'<guid>{item["link"]}</guid>\n'
        # Format date for RSS
        pub_date = format_datetime(item['pubDate'])
        xml += f'<pubDate>{pub_date}</pubDate>\n'
        xml += f'<description><![CDATA[{desc_clean}]]></description>\n'
        xml += '</item>\n'
        
    xml += '</channel>\n'
    xml += '</rss>'
    
    return Response(xml, mimetype='application/xml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
