from flask import Flask, send_from_directory, request, jsonify
import redis
from datetime import datetime
import os

app = Flask(__name__)

# Configure static file serving
app.static_folder = '.'
app.static_url_path = ''

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL')  # Will be set in Vercel
redis_client = None

if REDIS_URL:  # Production (Vercel) with Upstash Redis
    try:
        redis_client = redis.from_url(REDIS_URL)
        print("Connected to Upstash Redis")
    except Exception as e:
        print(f"Failed to connect to Upstash Redis: {e}")
elif not os.getenv('VERCEL_ENV'):  # Local development
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        print("Connected to local Redis")
    except Exception as e:
        print(f"Failed to connect to local Redis: {e}")

@app.route('/')
def index():
    try:
        if redis_client:
            # Increment visitor count
            visitor_count = redis_client.incr('visitor_count')
            # Store current visitor's IP
            ip_address = request.headers.get('x-real-ip') or request.remote_addr
            redis_client.set('current_visitor', ip_address)
    except Exception as e:
        print(f"Redis error: {e}")
    
    return send_from_directory('.', 'index.html')

@app.route('/help')
def help_page():
    return send_from_directory('.', 'help.html')

@app.route('/markdown-guide')
def markdown_guide():
    return send_from_directory('.', 'markdown-guide.html')

@app.route('/visitors')
def get_visitors():
    try:
        if redis_client:
            visitor_count = redis_client.get('visitor_count')
            current_visitor = redis_client.get('current_visitor')
            return jsonify({
                'total_visitors': int(visitor_count) if visitor_count else 0,
                'current_visitor': current_visitor.decode('utf-8') if current_visitor else 'Unknown'
            })
    except Exception as e:
        print(f"Redis error: {e}")
    
    return jsonify({
        'total_visitors': 0,
        'current_visitor': request.headers.get('x-real-ip') or request.remote_addr
    })

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
