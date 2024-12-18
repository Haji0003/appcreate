from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    with sqlite3.connect("training.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS training (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            day_of_week TEXT NOT NULL,
            training_content TEXT NOT NULL,
            sets INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE
        )
        """)

# 初期化
init_db()

class Training(BaseModel):
    week_number: int
    day_of_week: str
    training_content: str
    sets: int
    completed: Optional[bool] = False

class TrainingResponse(Training):
    id: int

# トレーニングメニューを追加するエンドポイント
@app.post("/trainings", response_model=TrainingResponse)
def add_training(training: Training):
    with sqlite3.connect("training.db") as conn:
        cursor = conn.execute("""
        INSERT INTO training (week_number, day_of_week, training_content, sets, completed)
        VALUES (?, ?, ?, ?, ?)
        """, (training.week_number, training.day_of_week, training.training_content, training.sets, training.completed))
        training_id = cursor.lastrowid
    return {**training.dict(), "id": training_id}

@app.get("/trainings")
def get_trainings():
    with sqlite3.connect("training.db") as conn:
        trainings = conn.execute("SELECT * FROM training").fetchall()
        return [{"id": t[0], "week_number": t[1], "day_of_week": t[2], "training_content": t[3], "sets": t[4], "completed": bool(t[5])} for t in trainings]

@app.put("/trainings/{training_id}")
def update_training(training_id: int, training: Training):
    with sqlite3.connect("training.db") as conn:
        cursor = conn.execute("""
        UPDATE training
        SET week_number = ?, day_of_week = ?, training_content = ?, sets = ?, completed = ?
        WHERE id = ?
        """, (training.week_number, training.day_of_week, training.training_content, training.sets, training.completed, training_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Training not found")
        return {**training.dict(), "id": training_id}

@app.delete("/trainings/{training_id}")
def delete_training(training_id: int):
    with sqlite3.connect("training.db") as conn:
        cursor = conn.execute("DELETE FROM training WHERE id = ?", (training_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Training not found")
        return {"message": "Training deleted"}

@app.get("/trainings/{training_id}", response_model=TrainingResponse)
def get_training(training_id: int):
    with sqlite3.connect("training.db") as conn:
        training = conn.execute("SELECT * FROM training WHERE id = ?", (training_id,)).fetchone()
        if training is None:
            raise HTTPException(status_code=404, detail="Training not found")
        return {
            "id": training[0],
            "week_number": training[1],
            "day_of_week": training[2],
            "training_content": training[3],
            "sets": training[4],
            "completed": bool(training[5])
        }
