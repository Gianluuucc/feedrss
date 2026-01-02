from flask import Flask, request, Response, render_template_string
from scraper import get_news
from email.utils import format_datetime
import time
import socket
import xml.etree.ElementTree as ET
import io

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
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                input[type=text] { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
                input[type=submit], button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; border-radius: 4px; }
                button.delete { background: #dc3545; padding: 5px 10px; font-size: 0.8em; }
                .result { margin-top: 20px; padding: 15px; background: #f0f0f0; word-break: break-all; }
                label { font-weight: bold; margin-top: 15px; display: block; }
                .hint { font-size: 0.8em; color: #666; margin-bottom: 5px; }
                .saved-feeds { margin-top: 40px; border-top: 1px solid #ccc; padding-top: 20px; }
                .feed-item { background: #f8f9fa; padding: 10px; margin-bottom: 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
                .feed-info { flex-grow: 1; }
                .feed-name { font-weight: bold; display: block; }
                .feed-url { font-size: 0.8em; color: #666; word-break: break-all; }
            </style>
        </head>
        <body>
            <h1>Generatore Feed RSS per Comuni</h1>
            <form method="get" action="/generate">
                <label>1. Nome del Comune/Feed (opzionale):</label>
                <div class="hint">Es: "Matelica - Novità" (serve solo per memorizzarlo)</div>
                <input type="text" name="feed_name" placeholder="Nome del feed">

                <label>2. Link delle notizie del Comune:</label>
                <input type="text" name="url" placeholder="https://www.comune.matelica.mc.it/..." required>
                
                <label>3. Indirizzo del tuo Server (Base URL):</label>
                <div class="hint">Modifica questo se vuoi usare un IP pubblico o un dominio diverso da localhost.</div>
                <input type="text" name="base_url" value="{{ suggested_base }}">
                
                <br><br>
                <input type="submit" value="Genera Link RSS">
            </form>

            <div class="saved-feeds" id="savedSection" style="display:none;">
                <h2>I tuoi Feed Salvati</h2>
                <div id="feedsList"></div>
            </div>

            <script>
                function loadFeeds() {
                    const feeds = JSON.parse(localStorage.getItem('myFeeds') || '[]');
                    const container = document.getElementById('feedsList');
                    const section = document.getElementById('savedSection');
                    
                    if (feeds.length > 0) {
                        section.style.display = 'block';
                        container.innerHTML = '';
                        feeds.forEach((feed, index) => {
                            const div = document.createElement('div');
                            div.className = 'feed-item';
                            div.innerHTML = `
                                <div class="feed-info">
                                    <span class="feed-name">${feed.name}</span>
                                    <a href="${feed.url}" target="_blank" class="feed-url">${feed.url}</a>
                                </div>
                                <button class="delete" onclick="deleteFeed(${index})">Elimina</button>
                            `;
                            container.appendChild(div);
                        });
                    } else {
                        section.style.display = 'none';
                    }
                }

                function deleteFeed(index) {
                    const feeds = JSON.parse(localStorage.getItem('myFeeds') || '[]');
                    feeds.splice(index, 1);
                    localStorage.setItem('myFeeds', JSON.stringify(feeds));
                    loadFeeds();
                }

                loadFeeds();
            </script>
        </body>
        </html>
    ''', suggested_base=suggested_base)

@app.route('/generate')
def generate():
    target_url = request.args.get('url')
    base_url = request.args.get('base_url')
    feed_name = request.args.get('feed_name') or 'Feed senza nome'
    
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
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .result { margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 5px; }
                code { font-size: 1.2em; color: #d63384; word-break: break-all; }
                a { color: #007bff; text-decoration: none; }
                button { padding: 10px 20px; background: #28a745; color: white; border: none; cursor: pointer; border-radius: 4px; margin-top: 10px; }
            </style>
        </head>
        <body>
            <h1>Ecco il tuo Feed RSS</h1>
            <p>Copia questo link e usalo nel tuo lettore RSS o sistema di invio notizie:</p>
            <div class="result">
                <code>{{ feed_url }}</code>
            </div>
            
            <button onclick="saveAndHome()">Salva nei miei feed e torna alla Home</button>
            
            <p><a href="{{ feed_url }}" target="_blank">Anteprima Feed</a></p>
            <p><a href="/">Torna indietro senza salvare</a></p>

            <script>
                function saveAndHome() {
                    const feedName = "{{ feed_name }}";
                    const feedUrl = "{{ feed_url }}";
                    
                    const feeds = JSON.parse(localStorage.getItem('myFeeds') || '[]');
                    feeds.push({ name: feedName, url: feedUrl });
                    localStorage.setItem('myFeeds', JSON.stringify(feeds));
                    
                    window.location.href = '/';
                }
            </script>
        </body>
        </html>
    ''', feed_url=feed_url, feed_name=feed_name)

@app.route('/feed')
def feed():
    target_url = request.args.get('url')
    if not target_url:
        return "URL mancante", 400
        
    news_items = get_news(target_url)
    
    # Build XML using ElementTree to ensure valid XML structure
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    
    ET.SubElement(channel, 'title').text = f'Notizie da {target_url}'
    ET.SubElement(channel, 'link').text = target_url
    ET.SubElement(channel, 'description').text = 'Feed RSS generato automaticamente'
    
    for item in news_items:
        item_node = ET.SubElement(channel, 'item')
        ET.SubElement(item_node, 'title').text = item["title"]
        ET.SubElement(item_node, 'link').text = item["link"]
        ET.SubElement(item_node, 'guid').text = item["link"]
        
        # Format date for RSS
        pub_date = format_datetime(item['pubDate'])
        ET.SubElement(item_node, 'pubDate').text = pub_date
        
        ET.SubElement(item_node, 'description').text = item["description"]
        
    # Serialize to string
    f = io.BytesIO()
    tree = ET.ElementTree(rss)
    tree.write(f, encoding='utf-8', xml_declaration=True)
    xml_output = f.getvalue()
    
    return Response(xml_output, mimetype='application/xml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
