import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.utils import secure_filename
from models import db, User, Note, NoteImage, Comment

# Configurazione dell'applicazione
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appunti.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Inizializza database e login manager
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crea il database se non esiste
with app.app_context():
    db.create_all()

# Funzione helper per validare estensioni file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Rotta: Home con ricerca e visualizzazione note pubbliche
default_methods = ['GET', 'POST']
@app.route('/', methods=default_methods)
def home():
    query = request.form.get('search', '')
    if query:
        notes = Note.query.filter(
            Note.public == True,
            (Note.title.contains(query)) | (Note.macro_tematiche.contains(query))
        ).all()
    else:
        notes = Note.query.filter_by(public=True).all()
    return render_template('home.html', notes=notes)


# Rotta: Registrazione utente
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        e = request.form['email']
        p = request.form['password']
        if User.query.filter((User.email == e) | (User.username == u)).first():
            flash('Username o email già in uso', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=u, email=e, password=p)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrazione effettuata', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Rotta: Login utente
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Credenziali errate', 'danger')
    return render_template('login.html')

# Rotta: Logout utente
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato', 'info')
    return redirect(url_for('home'))

# Rotta: Dashboard utente
@app.route('/dashboard')
@login_required
def dashboard():
    notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', notes=notes)

# Rotta: Carica nuovo appunto
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        macro = request.form['macro_tematiche']
        pub = 'public' in request.form
        cover_file = request.files.get('cover')
        cover_filename = None
        if cover_file and allowed_file(cover_file.filename):
            cover_filename = secure_filename(cover_file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            cover_file.save(os.path.join(app.config['UPLOAD_FOLDER'], cover_filename))
        note = Note(title=title, content=content, macro_tematiche=macro,
                    public=pub, user_id=current_user.id,
                    cover_image=cover_filename)
        db.session.add(note)
        db.session.commit()
        # Gestione allegati
        for file in request.files.getlist('attachments'):
            if file and allowed_file(file.filename):
                fn = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                db.session.add(NoteImage(image=fn, note_id=note.id))
        db.session.commit()
        flash('Appunto caricato', 'success')
        return redirect(url_for('dashboard'))
    return render_template('upload_note.html')

# Rotta: Dettaglio appunto con commenti
@app.route('/note/<int:note_id>', methods=['GET', 'POST'])
def note_detail(note_id):
    note = Note.query.get_or_404(note_id)
    if request.method == 'POST' and current_user.is_authenticated:
        comment_text = request.form['comment']
        if comment_text:
            new_comment = Comment(comment_text=comment_text, note_id=note.id, user_id=current_user.id)
            db.session.add(new_comment)
            db.session.commit()
            flash('Commento aggiunto', 'success')
            return redirect(url_for('note_detail', note_id=note.id))
    return render_template('note_detail.html', note=note)

# Rotta: Modifica appunto
@app.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash('Permesso negato', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']
        note.macro_tematiche = request.form['macro_tematiche']
        note.public = 'public' in request.form
        cover = request.files.get('cover')
        if cover and allowed_file(cover.filename):
            fn = secure_filename(cover.filename)
            cover.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
            note.cover_image = fn
        # Aggiungi nuovi allegati
        for file in request.files.getlist('attachments'):
            if file and allowed_file(file.filename):
                fn = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                db.session.add(NoteImage(image=fn, note_id=note.id))
        db.session.commit()
        flash('Modifiche salvate', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_note.html', note=note)

# Rotta: Elimina appunto
@app.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id == current_user.id:
        db.session.delete(note)
        db.session.commit()
        flash('Appunto eliminato', 'info')
    return redirect(url_for('dashboard'))

# Rotta: Elimina immagine allegata
@app.route('/delete_image/<int:image_id>', methods=['GET','POST'])
@login_required
def delete_image(image_id):
    img = NoteImage.query.get_or_404(image_id)
    if request.method == 'POST' and img.note.user_id == current_user.id:
        path = os.path.join(app.config['UPLOAD_FOLDER'], img.image)
        if os.path.exists(path): os.remove(path)
        db.session.delete(img)
        db.session.commit()
        flash('Immagine eliminata', 'info')
        return redirect(url_for('edit_note', note_id=img.note_id))
    return render_template('delete_image.html', image=img)

# Avvio dell'applicazione
if __name__ == '__main__':
    app.run(debug=True)