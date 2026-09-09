"""
TaskFlow API
A tiny task-management REST API used as the sample workload for the
TaskFlow CI/CD pipeline demo (Jenkins -> SonarQube -> Trivy -> Docker -> Kubernetes).
"""

from flask import Flask, jsonify, request
from datetime import datetime, timezone
import uuid

app = Flask(__name__)

# In-memory store (fine for a demo app; swap for a real DB in production)
tasks = {}


@app.route("/health", methods=["GET"])
def health():
    """Used by the Kubernetes liveness/readiness probes."""
    return jsonify({"status": "ok", "time": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/tasks", methods=["GET"])
def list_tasks():
    return jsonify(list(tasks.values())), 200


@app.route("/tasks", methods=["POST"])
def create_task():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not title:
        return jsonify({"error": "title is required"}), 400

    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tasks[task_id] = task
    return jsonify(task), 201


@app.route("/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "task not found"}), 404

    body = request.get_json(silent=True) or {}
    if "done" in body:
        tasks[task_id]["done"] = bool(body["done"])
    if "title" in body:
        tasks[task_id]["title"] = body["title"]

    return jsonify(tasks[task_id]), 200


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "task not found"}), 404
    del tasks[task_id]
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
