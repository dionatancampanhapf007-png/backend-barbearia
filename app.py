from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime, time

app = Flask(__name__)
CORS(app)

DB = "agenda.db"

BARBEIROS = ["Arthur", "Alan"]
HORA_ABERTURA = time(9, 0)
HORA_FECHAMENTO = time(20, 0)

def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    with conectar() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            barbeiro TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL
        )
        """)

criar_tabela()

def horario_valido(horario_str):
    h = datetime.strptime(horario_str, "%H:%M").time()
    return HORA_ABERTURA <= h < HORA_FECHAMENTO

def dia_valido(data_str):
    data = datetime.strptime(data_str, "%Y-%m-%d")
    return data.weekday() != 6

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/agendar", methods=["POST"])
def agendar():
    dados = request.json

    cliente = dados.get("cliente")
    barbeiro = dados.get("barbeiro")
    data = dados.get("data")
    horario = dados.get("horario")

    if not all([cliente, barbeiro, data, horario]):
        return jsonify({"erro": "Dados incompletos"}), 400

    if barbeiro not in BARBEIROS:
        return jsonify({"erro": "Barbeiro inválido"}), 400

    if not dia_valido(data):
        return jsonify({"erro": "Não abrimos aos domingos"}), 400

    if not horario_valido(horario):
        return jsonify({"erro": "Horário fora do funcionamento"}), 400

    with conectar() as conn:
        conflito = conn.execute("""
        SELECT 1 FROM agendamentos
        WHERE barbeiro=? AND data=? AND horario=?
        """, (barbeiro, data, horario)).fetchone()

        if conflito:
            return jsonify({"erro": "Horário indisponível"}), 409

        conn.execute("""
        INSERT INTO agendamentos (cliente, barbeiro, data, horario)
        VALUES (?, ?, ?, ?)
        """, (cliente, barbeiro, data, horario))

    return jsonify({"msg": "Agendamento confirmado"}), 201

@app.route("/agenda", methods=["GET"])
def listar_agendamentos():
    data = request.args.get("data")

    query = "SELECT cliente, barbeiro, data, horario FROM agendamentos"
    params = []

    if data:
        query += " WHERE data = ?"
        params.append(data)

    query += " ORDER BY data, horario"

    with conectar() as conn:
        dados = conn.execute(query, params).fetchall()

    return jsonify([dict(row) for row in dados]), 200

if __name__ == "__main__":
    app.run()