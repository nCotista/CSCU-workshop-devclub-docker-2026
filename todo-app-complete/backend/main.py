from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import json
import uuid

app = Flask(__name__)
# อนุญาตให้ Frontend ข้าม Port มาคุยได้
CORS(app) 

# เชื่อมต่อ Database (ใช้ชื่อ Service 'redis-db' จาก docker-compose)
db = redis.Redis(host='redis-db', port=6379, decode_responses=True)

@app.route('/todos', methods=['GET'])
def get_todos():
    todos = [json.loads(db.get(key)) for key in db.keys('todo:*')]
    # เรียงลำดับให้ของใหม่ขึ้นก่อน
    return jsonify(sorted(todos, key=lambda x: x.get('id', ''), reverse=True))

@app.route('/todos', methods=['POST'])
def add_todo():
    todo_id = f"todo:{uuid.uuid4()}"
    data = request.json
    data['id'] = todo_id
    # Default ค่า completed เป็น false ถ้าไม่ได้ส่งมา
    data['completed'] = data.get('completed', False) 
    db.set(todo_id, json.dumps(data))
    return jsonify(data), 201

# --- ฟีเจอร์ที่เพิ่มใหม่: รับคำสั่งแก้ไข (Edit / Mark Completed) ---
@app.route('/todos/<todo_id>', methods=['PUT'])
def update_todo(todo_id):
    existing_data_str = db.get(todo_id)
    if existing_data_str:
        existing_data = json.loads(existing_data_str)
        new_data = request.json
        
        # อัปเดตข้อมูลเก่าด้วยข้อมูลใหม่
        existing_data['task'] = new_data.get('task', existing_data['task'])
        existing_data['completed'] = new_data.get('completed', existing_data['completed'])
        
        db.set(todo_id, json.dumps(existing_data))
        return jsonify(existing_data), 200
    return jsonify({'error': 'Todo not found'}), 404
# -----------------------------------------------------------------

@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    db.delete(todo_id)
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)