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
        user_agent = request.headers.get('User-Agent', 'Unknown')
        path = request.path
        
        # Increment total visits
        redis_client.incr('total_visits')
        
        # Store visit details
        visit_data = {
            'ip': ip,
            'timestamp': timestamp,
            'user_agent': user_agent,
            'path': path
        }
        
        # Store last 100 visits
        redis_client.lpush('recent_visits', str(visit_data))
        redis_client.ltrim('recent_visits', 0, 99)
        
        # Track unique visitors by IP (daily)
        today = datetime.now().strftime('%Y-%m-%d')
        redis_client.sadd(f'unique_visitors:{today}', ip)
        
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
    return render_template('guide.html')

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
        
        # Get page views
        page_views = redis_client.hgetall('page_views')
        
        # Get recent visits
        recent_visits = redis_client.lrange('recent_visits', 0, 9)  # Last 10 visits
        
        return jsonify({
            'total_visits': total_visits,
            'unique_visitors_today': unique_visitors_today,
            'page_views': {k.decode(): int(v) for k, v in page_views.items()},
            'recent_visits': [eval(v.decode()) for v in recent_visits]
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
