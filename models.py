from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Inizializza l'istanza di SQLAlchemy
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """
    Modello utente: username, email, password e relazioni con Note e Commenti
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Note(db.Model):
    """
    Modello appunto: titolo, contenuto, macro-tematiche, stato pubblico, cover image
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    macro_tematiche = db.Column(db.String(150), nullable=True)
    public = db.Column(db.Boolean, default=False)
    cover_image = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    images = db.relationship('NoteImage', backref='note', lazy=True)
    comments = db.relationship('Comment', backref='note', lazy=True)

class NoteImage(db.Model):
    """
    Modello immagine allegata a un appunto
    """
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(100), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False)

class Comment(db.Model):
    """
    Modello commento: testo, timestamp, relazioni con Note e User
    """
    id = db.Column(db.Integer, primary_key=True)
    comment_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)