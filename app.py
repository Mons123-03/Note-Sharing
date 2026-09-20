import os
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production')

# MySQL Config — prefer env vars in production
app.config['MYSQL_HOST']     = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER']     = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'Monika$@2004moni')
app.config['MYSQL_DB']       = os.environ.get('MYSQL_DB', 'notes_db')
app.config['UPLOAD_FOLDER']  = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

mysql = MySQL(app)
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'png', 'jpg', 'jpeg', 'pptx'}

SUBJECT_CHOICES = [
    'Computer Science', 'Mathematics', 'Physics',
    'Chemistry', 'Biology', 'Business', 'History', 'Other'
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─── Index / Search ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    subject_filter = request.args.get('subject', '').strip()
    cur = mysql.connection.cursor()

    query = """
        SELECT notes.id, notes.title, notes.subject, notes.filename,
               notes.user_id, notes.upload_date, users.username,
               notes.total_rating, notes.rating_count, notes.download_count
        FROM notes
        JOIN users ON notes.user_id = users.id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (notes.title LIKE %s OR notes.subject LIKE %s OR users.username LIKE %s)"
        params += [f'%{search_query}%', f'%{search_query}%', f'%{search_query}%']

    if subject_filter:
        query += " AND notes.subject = %s"
        params.append(subject_filter)

    query += " ORDER BY notes.upload_date DESC"
    cur.execute(query, params)
    all_notes = cur.fetchall()
    cur.close()

    return render_template('index.html',
                           notes=all_notes,
                           search_query=search_query,
                           subject_filter=subject_filter,
                           subjects=SUBJECT_CHOICES)


# ─── Note Detail ─────────────────────────────────────────────────────────────

@app.route('/note/<int:note_id>')
def note_detail(note_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT notes.id, notes.title, notes.subject, notes.filename,
               notes.user_id, notes.upload_date, users.username,
               notes.total_rating, notes.rating_count, notes.download_count
        FROM notes JOIN users ON notes.user_id = users.id
        WHERE notes.id = %s
    """, [note_id])
    note = cur.fetchone()
    if not note:
        flash('Note not found.', 'danger')
        return redirect(url_for('index'))

    cur.execute("""
        SELECT comments.comment_text, comments.created_at, users.username
        FROM comments JOIN users ON comments.user_id = users.id
        WHERE comments.note_id = %s
        ORDER BY comments.created_at DESC
    """, [note_id])
    comments = cur.fetchall()
    cur.close()
    return render_template('note_detail.html', note=note, comments=comments)


# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form.get('email', '').strip()
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                (username, password, email)
            )
            mysql.connection.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print("REAL ERROR:", e)   # 👈 ADD THIS
            flash('Username or email already exists.', 'danger')
        finally:
            cur.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        pw = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[2], pw):
            session['user_id']  = user[0]
            session['username'] = user[1]
            flash(f'Welcome back, {user[1]}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─── Upload ──────────────────────────────────────────────────────────────────

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files.get('note_file')
    title   = request.form.get('title', '').strip()
    subject = request.form.get('subject', 'Other').strip()

    if not file or not allowed_file(file.filename):
        flash('Invalid file type. Allowed: pdf, txt, docx, pptx, png, jpg.', 'danger')
        return redirect(url_for('index'))

    if not title:
        flash('Title is required.', 'danger')
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    # Avoid collisions: prefix with user_id + timestamp
    import time
    unique_name = f"{session['user_id']}_{int(time.time())}_{filename}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO notes (title, subject, filename, user_id, download_count, total_rating, rating_count) "
        "VALUES (%s, %s, %s, %s, 0, 0, 0)",
        (title, subject, unique_name, session['user_id'])
    )
    mysql.connection.commit()
    cur.close()
    flash('Note uploaded successfully!', 'success')
    return redirect(url_for('index'))


# ─── Download ────────────────────────────────────────────────────────────────

# @app.route('/download/<int:note_id>/<filename>')
# def download(note_id, filename):
#     cur = mysql.connection.cursor()
#     # Security: verify filename belongs to this note_id
#     cur.execute("SELECT filename FROM notes WHERE id = %s", [note_id])
#     row = cur.fetchone()
#     if not row or row[0] != filename:
#         cur.close()
#         flash('File not found.', 'danger')
#         return redirect(url_for('index'))
#     cur.execute("UPDATE notes SET download_count = download_count + 1 WHERE id = %s", [note_id])
#     mysql.connection.commit()
#     cur.close()
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/download/<int:note_id>/<filename>')
def download(note_id, filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # increase download count (optional but good)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE notes SET download_count = download_count + 1 WHERE id = %s", (note_id,))
    mysql.connection.commit()
    cur.close()

    # 🔥 THIS FORCES DOWNLOAD
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True   # 👈 VERY IMPORTANT
    )

# ─── Delete ──────────────────────────────────────────────────────────────────

@app.route('/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT filename, user_id FROM notes WHERE id = %s", [note_id])
    row = cur.fetchone()
    if not row:
        flash('Note not found.', 'danger')
        cur.close()
        return redirect(url_for('index'))
    if row[1] != session['user_id']:
        flash('You can only delete your own notes.', 'danger')
        cur.close()
        return redirect(url_for('index'))

    # Remove file from disk
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], row[0])
    if os.path.exists(filepath):
        os.remove(filepath)

    cur.execute("DELETE FROM comments WHERE note_id = %s", [note_id])
    cur.execute("DELETE FROM notes WHERE id = %s", [note_id])
    mysql.connection.commit()
    cur.close()
    flash('Note deleted.', 'success')
    return redirect(url_for('my_notes'))


# ─── My Notes ────────────────────────────────────────────────────────────────

@app.route('/my-notes')
@login_required
def my_notes():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, title, subject, filename, upload_date,
               total_rating, rating_count, download_count
        FROM notes WHERE user_id = %s ORDER BY upload_date DESC
    """, [session['user_id']])
    notes = cur.fetchall()
    cur.close()
    return render_template('my_notes.html', notes=notes)


# ─── Rate ────────────────────────────────────────────────────────────────────

@app.route('/rate/<int:note_id>', methods=['POST'])
@login_required
def rate_note(note_id):
    stars = int(request.form.get('stars', 0))
    if not 1 <= stars <= 5:
        flash('Invalid rating.', 'danger')
        return redirect(url_for('index'))
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE notes SET total_rating = total_rating + %s, rating_count = rating_count + 1 WHERE id = %s",
        (stars, note_id)
    )
    mysql.connection.commit()
    cur.close()
    flash(f'Rated {stars} star{"s" if stars > 1 else ""}!', 'success')
    return redirect(request.referrer or url_for('index'))


# ─── Comment ─────────────────────────────────────────────────────────────────

# @app.route('/comment/<int:note_id>', methods=['POST'])
# @login_required
# def comment(note_id):
#     text = request.form.get('comment', '').strip()
#     if not text:
#         flash('Comment cannot be empty.', 'danger')
#         return redirect(url_for('note_detail', note_id=note_id))
#     cur = mysql.connection.cursor()
#     cur.execute(
#         "INSERT INTO comments (note_id, user_id, comment_text) VALUES (%s, %s, %s)",
#         (note_id, session['user_id'], text)
#     )
#     mysql.connection.commit()
#     cur.close()
#     flash('Comment posted!', 'success')
#     return redirect(url_for('note_detail', note_id=note_id))

# @app.route('/comment/<int:note_id>', methods=['POST'])
# @login_required
# def comment(note_id):
#     text = request.form.get('comment', '').strip()

#     if not text:
#         flash('Comment cannot be empty.', 'danger')
#         return redirect(url_for('note_detail', note_id=note_id))

#     user_id = session.get('user_id')

#     print("USER_ID:", user_id)
#     print("NOTE_ID:", note_id)
#     print("TEXT:", text)

#     cur = mysql.connection.cursor()

#     try:
#         cur.execute(
#             "INSERT INTO comments (note_id, user_id, comment_text) VALUES (%s, %s, %s)",
#             (note_id, user_id, text)
#         )
#         mysql.connection.commit()

#     except Exception as e:
#         print("FULL ERROR:", e)   # 🔥 THIS IS KEY
#         flash('Error posting comment.', 'danger')

#     finally:
#         cur.close()

#     return redirect(url_for('note_detail', note_id=note_id))

@app.route('/comment/<int:note_id>', methods=['POST'])
@login_required
def comment(note_id):
    text = request.form.get('comment', '').strip()
    user_id = session.get('user_id')

    if not user_id:
        flash('Session error. Please login again.', 'danger')
        return redirect(url_for('login'))

    if not text:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('note_detail', note_id=note_id))

    cur = mysql.connection.cursor()

    try:
        cur.execute(
            "INSERT INTO comments (note_id, user_id, comment_text) VALUES (%s, %s, %s)",
            (note_id, user_id, text)
        )
        mysql.connection.commit()

    except Exception as e:
        print("REAL ERROR:", e)
        flash('Error posting comment.', 'danger')

    finally:
        cur.close()

    return redirect(url_for('note_detail', note_id=note_id))


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)