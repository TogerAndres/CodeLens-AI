"""
run.py
Ejecuta con: python run.py
(o con gunicorn en producción: gunicorn run:app)
"""
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
