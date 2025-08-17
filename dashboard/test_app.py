#!/usr/bin/env python3

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Dashboard is working!"

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "message": "Service is healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
