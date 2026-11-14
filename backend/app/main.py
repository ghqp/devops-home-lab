import os

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="DevOps Home Lab API")


def get_connection():
    return psycopg.connect(
        host="database",
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        row_factory=dict_row,
    )


class StatusCreate(BaseModel):
    service_name: str
    status: str


@app.get("/health")
def health():
    with get_connection() as conn:
        conn.execute("SELECT 1")

    return {"status": "healthy", "database": "connected"}


@app.get("/status")
def get_status():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM lab_status ORDER BY id"
        ).fetchall()

    return rows


@app.post("/status")
def create_status(item: StatusCreate):
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO lab_status (service_name, status)
            VALUES (%s, %s)
            RETURNING *
            """,
            (item.service_name, item.status),
        ).fetchone()

    return row
