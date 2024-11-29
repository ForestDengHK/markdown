from flask import Flask, send_from_directory, request, jsonify
import redis
import os
from datetime import datetime

app = Flask(__name__)

# Configure static file serving
app.static_folder = 'static'
app.static_url_path = ''

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL')
redis_client = None

if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL)
        print("Connected to Redis")
    except Exception as e:
        print(f"Redis connection error: {e}")
        redis_client = None

def get_visitor_ip():
    return request.headers.get('x-forwarded-for', request.remote_addr)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/help')
def help_page():
    return send_from_directory('.', 'help.html')

@app.route('/markdown-guide')
def markdown_guide():
    return send_from_directory('.', 'markdown-guide.html')

@app.route('/visitors')
def get_visitors():
    if not redis_client:
        return jsonify({
            'total_visitors': 0,
            'current_visitor': get_visitor_ip()
        })

    try:
        # Increment visitor count
        visitor_count = redis_client.incr('visitor_count')
        # Store current visitor's IP
        current_ip = get_visitor_ip()
        redis_client.set('current_visitor', current_ip)

        return jsonify({
            'total_visitors': visitor_count,
            'current_visitor': current_ip
        })
    except Exception as e:
        print(f"Redis error in /visitors: {e}")
        return jsonify({
            'total_visitors': 0,
            'current_visitor': get_visitor_ip()
        })

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
