from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from enum import Enum
from datetime import datetime
from database import *


app = FastAPI()
templates = Jinja2Templates(directory="templates")

class Action(str, Enum):
    PUSH = "push"
    PULL = "pull"
    MERGE = "merge"

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
    
@app.post("/webhook")
async def webhookEvent(request: Request):
    try:
        event_type = request.headers.get('X-GitHub-Event')
        payload = await request.json()

        action = None
        author = None
        from_branch = None
        to_branch = None
        timedate =  datetime.utcnow()
        

        if event_type == 'push':
            action = Action.PUSH
            author = payload.get('pusher', {}).get('name')
            request_id = payload.get('after')
            to_branch = payload.get('ref', '').split('/')[-1]
            timestamp = payload.get('updated_at', timedate)

        elif event_type == 'pull_request':
            pull_action = payload.get('action')
            author = payload.get('pull_request', {}).get('user', {}).get('login')
            request_id = payload.get('after')
            from_branch = payload.get('pull_request', {}).get('head', {}).get('ref')
            to_branch = payload.get('pull_request', {}).get('base', {}).get('ref')
            timestamp = payload.get('updated_at', timedate)

            if pull_action == 'opened':
                action = Action.PULL
            elif pull_action == 'closed' and payload.get('pull_request', {}).get('merged'):
                action = Action.MERGE

        if action:
            events_collection.insert_one({
                "action": action.value,
                "author": author,
                "request_id" : request_id,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            })
            print(f"Event saved: {action.value} by {author}")

        else:
            print("No matching action to save.")

        return {"status": "ok"}

    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

    
@app.get("/events")
def git_events():
    events = events_collection.find().sort("time", -1).limit(10)
    event_msg = []
    for event in events:
        timestamp = event["timestamp"].strftime("%d %B %Y - %I:%M %p UTC")
        if event["action"] == "push":
            msg = f'"{event["author"]}" pushed to "{event["to_branch"]}" on {timestamp}'
        elif event["action"] == "pull":
            msg = f'"{event["author"]}" submitted a pull request from "{event["from_branch"]}" to "{event["to_branch"]}" on {timestamp}'
        elif event["action"] == "merge":
            msg = f'"{event["author"]}" merged "{event["from_branch"]}" into "{event["to_branch"]}" on {timestamp}'
        else:
            msg = "Unknown action"
        event_msg.append (msg)
    return event_msg
