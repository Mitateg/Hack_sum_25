"""
Simple web dashboard for monitoring the Telegram Promo Bot
Provides real-time statistics and system status
"""

import asyncio
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify
from config import config
from storage import storage

app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Telegram Promo Bot Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2196F3; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #2196F3; }
        .stat-label { color: #666; margin-top: 5px; }
        .status { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
        .status-value { font-weight: bold; }
        .online { color: #4CAF50; }
        .offline { color: #f44336; }
        .refresh-btn { background: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-top: 20px; }
        .refresh-btn:hover { background: #1976D2; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Telegram Promo Bot Dashboard</h1>
            <p>Real-time monitoring and statistics</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="total-users">0</div>
                <div class="stat-label">Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-messages">0</div>
                <div class="stat-label">Messages Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-promos">0</div>
                <div class="stat-label">Promos Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-posts">0</div>
                <div class="stat-label">Channel Posts</div>
            </div>
        </div>
        
        <div class="status">
            <h2>System Status</h2>
            <div class="status-item">
                <span>Bot Status</span>
                <span class="status-value online" id="bot-status">Online</span>
            </div>
            <div class="status-item">
                <span>Web Dashboard</span>
                <span class="status-value online">Running</span>
            </div>
            <div class="status-item">
                <span>Data Storage</span>
                <span class="status-value online" id="storage-status">Active</span>
            </div>
            <div class="status-item">
                <span>Last Updated</span>
                <span class="status-value" id="last-updated">-</span>
            </div>
            <div class="status-item">
                <span>Uptime</span>
                <span class="status-value" id="uptime">-</span>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
    </div>
    
    <script>
        let startTime = new Date();
        
        function refreshData() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-users').textContent = data.total_users || 0;
                    document.getElementById('total-messages').textContent = data.total_messages || 0;
                    document.getElementById('total-promos').textContent = data.total_promos_generated || 0;
                    document.getElementById('total-posts').textContent = data.total_posts_to_channels || 0;
                    document.getElementById('last-updated').textContent = new Date(data.last_updated).toLocaleString();
                    
                    // Update uptime
                    let uptime = Math.floor((new Date() - startTime) / 1000);
                    let hours = Math.floor(uptime / 3600);
                    let minutes = Math.floor((uptime % 3600) / 60);
                    let seconds = uptime % 60;
                    document.getElementById('uptime').textContent = `${hours}h ${minutes}m ${seconds}s`;
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    document.getElementById('bot-status').textContent = 'Error';
                    document.getElementById('bot-status').className = 'status-value offline';
                });
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def api_stats():
    """API endpoint for bot statistics."""
    try:
        stats = storage.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

async def start_dashboard():
    """Start the web dashboard."""
    if config.web_dashboard_enabled:
        app.run(
            host=config.web_dashboard_host,
            port=config.web_dashboard_port,
            debug=config.debug_mode,
            use_reloader=False
        ) 