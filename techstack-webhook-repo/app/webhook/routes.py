from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from datetime import datetime, timezone

webhook = Blueprint('Webhook', __name__)

@webhook.route('/')
def index():
    return render_template('index.html')

@webhook.route('/api/events', methods=['GET'])
def get_events():
    collection = db['events']

    events = list(collection.find({}, {'_id': 0}).sort('_id', -1).limit(15))
    
    return jsonify(events), 200

@webhook.route('/receiver', methods=["POST"])
def handle_webhook():
    collection = db["events"]

    payload = request.json
    event_type = request.headers.get("X-Github-Event")

    event_data = {
        "request_id": "",
        "author": "",
        "action": "",
        "from_branch": "",
        "to_branch": "",
        "timestamp": datetime.now(timezone.utc).strftime("%d %B %Y %I:%M %p UTC")
    }                             

    if event_type == "pull_request":
        pr_data = payload.get("pull_request", {})
        action_status = payload.get("action")

        if action_status == 'closed' and pr_data.get('merged'):
            event_data['action'] = "MERGE"
        elif action_status in ['opened', 'reopened', 'synchronize']:
            event_data['action'] = "PULL_REQUEST"
        else:
            return jsonify({"message": "Pull request action ignored"}), 200
        
        event_data['author'] = payload.get('sender', {}).get('login', '')
        event_data['from_branch'] = pr_data.get('head', {}).get('ref', '')
        event_data['to_branch'] = pr_data.get('base', {}).get('ref', '')
        event_data['request_id'] = str(pr_data.get('id', ''))             

    elif event_type == 'push':
        if payload.get('deleted'):
            return jsonify({"message": "Branch deletion ignored"}), 200

        event_data['action'] = "PUSH"
        event_data['author'] = payload.get('pusher', {}).get('name', '')
        event_data['to_branch'] = payload.get('ref', '').split('/')[-1]
        event_data['request_id'] = payload.get('head_commit', {}).get('id', '')

    else:
        return jsonify({"message": "Event type not tracked"}), 200

    collection.insert_one(event_data)

    event_data.pop('_id', None)
    
    return jsonify({
        "message": "Event successfully recorded", 
        "data": event_data
    }), 201


