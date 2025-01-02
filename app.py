from flask import Flask, send_from_directory, request, jsonify, render_template
import redis
import os
from datetime import datetime

app = Flask(__name__)

# Configure static file serving
app.static_folder = '.'
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

def track_visit():
    if not redis_client:
        return

    try:
        # Get visitor information
        ip = get_visitor_ip()
        timestamp = datetime.now().isoformat()
        path = request.path
        
        # Increment total visits
        redis_client.incr('total_visits')
        
        # Track unique visitors by IP (daily)
        today = datetime.now().strftime('%Y-%m-%d')
        redis_client.sadd(f'unique_visitors:{today}', ip)
        
        # Track all-time unique visitors
        redis_client.sadd('all_unique_visitors', ip)
        
        # Track page views
        redis_client.hincrby('page_views', path, 1)
    except Exception as e:
        print(f"Error tracking visit: {e}")

@app.route('/')
def index():
    track_visit()
    return send_from_directory('.', 'index.html')

@app.route('/help')
def help_page():
    track_visit()
    return send_from_directory('.', 'help.html')

@app.route('/markdown-guide')
def markdown_guide():
    track_visit()
    return send_from_directory('.', 'markdown-guide.html')

@app.route('/author')
def author_page():
    track_visit()
    return send_from_directory('.', 'author.html')

@app.route('/admin/stats')
def admin_stats():
    if not redis_client:
        return jsonify({
            'error': 'Redis not connected'
        })

    try:
        # Get total visits
        total_visits = int(redis_client.get('total_visits') or 0)
        
        # Get today's unique visitors
        today = datetime.now().strftime('%Y-%m-%d')
        unique_visitors_today = redis_client.scard(f'unique_visitors:{today}')
        
        # Get all-time unique visitors
        all_unique_visitors = redis_client.scard('all_unique_visitors')
        
        # Get page views
        page_views = redis_client.hgetall('page_views')
        
        return jsonify({
            'total_visits': total_visits,
            'unique_visitors_today': unique_visitors_today,
            'total_unique_visitors': all_unique_visitors,
            'page_views': {k.decode(): int(v) for k, v in page_views.items()}
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        })

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
    track_visit()
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
