import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "secret_key_for_session"

# Database Initialization
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create stats table to track duplicates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            duplicate_count INTEGER DEFAULT 0
        )
    ''')
    # Initialize stats if empty
    cursor.execute('SELECT COUNT(*) FROM stats')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO stats (id, duplicate_count) VALUES (1, 0)')
    
    conn.commit()
    conn.close()

# Helper to get DB connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    total_records = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    duplicate_attempts = conn.execute('SELECT duplicate_count FROM stats WHERE id=1').fetchone()[0]
    conn.close()
    return render_template('index.html', total=total_records, duplicates=duplicate_attempts)

@app.route('/add', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        address = request.form['address'].strip()

        if not name or not email or not phone or not address:
            flash("All fields are required!", "danger")
            return redirect(url_for('add_data'))

        conn = get_db_connection()
        # Check if email or phone already exists
        existing_user = conn.execute(
            'SELECT * FROM users WHERE email = ? OR phone = ?', (email, phone)
        ).fetchone()

        if existing_user:
            # Increment duplicate counter
            conn.execute('UPDATE stats SET duplicate_count = duplicate_count + 1 WHERE id = 1')
            conn.commit()
            conn.close()
            flash("Duplicate data detected. Record already exists.", "danger")
            return redirect(url_for('add_data'))
        else:
            # Insert new record
            conn.execute(
                'INSERT INTO users (name, email, phone, address) VALUES (?, ?, ?, ?)',
                (name, email, phone, address)
            )
            conn.commit()
            conn.close()
            flash("Unique data added successfully.", "success")
            return redirect(url_for('records'))

    return render_template('add_data.html')

@app.route('/records')
def records():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('records.html', users=users)

@app.route('/delete/<int:id>')
def delete_record(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("Record deleted successfully.", "info")
    return redirect(url_for('records'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)