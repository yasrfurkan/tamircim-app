import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, TextAreaField, SelectField, DateTimeField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash


# Basit Flask kurulumu
tamircim = Flask(__name__)
tamircim.config['SECRET_KEY'] = "basitanahtar14431331"
tamircim.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tamircim.db'
tamircim.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Veritabanı kurulumu
db = SQLAlchemy(tamircim)

# Veri modelleri
class Sehir(db.Model):
    __tablename__ = 'sehir'
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(50), nullable=False)
    
    # İlişkiler
    ilceler = db.relationship('Ilce', backref='sehir', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Sehir {self.isim}>'

class Ilce(db.Model):
    __tablename__ = 'ilce'
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(50), nullable=False)
    sehir_id = db.Column(db.Integer, db.ForeignKey('sehir.id'), nullable=False)
    
    def __repr__(self):
        return f'<Ilce {self.isim}>'

class UzmanlikAlani(db.Model):
    __tablename__ = 'uzmanlik_alani'
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f'<UzmanlikAlani {self.isim}>'

class Kullanici(db.Model):
    __tablename__ = 'kullanici'
    id = db.Column(db.Integer, primary_key=True)
    eposta = db.Column(db.String(120), unique=True, nullable=False)
    sifre = db.Column(db.String(256), nullable=False)
    kullanici_tipi = db.Column(db.String(20), nullable=False)  # 'musteri' veya 'tamirci'
    isim = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tamirciye özel alanlar
    sehir = db.Column(db.String(50))
    ilce = db.Column(db.String(50))
    adres = db.Column(db.Text)
    uzmanlik_alani = db.Column(db.String(100))
    ortalama_puan = db.Column(db.Float, default=0.0)
    puan_sayisi = db.Column(db.Integer, default=0)
    
    sent_messages = db.relationship('Mesaj', foreign_keys='Mesaj.gonderici_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Mesaj', foreign_keys='Mesaj.alici_id', backref='recipient', lazy='dynamic')
    
    def is_customer(self):
        return self.kullanici_tipi == 'customer'
    
    def is_mechanic(self):
        return self.kullanici_tipi == 'mechanic'

class Randevu(db.Model):
    __tablename__ = 'randevu'
    id = db.Column(db.Integer, primary_key=True)
    musteri_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    tamirci_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    randevu_date = db.Column(db.DateTime, nullable=False)
    arac_detay = db.Column(db.String(255))
    servis_aciklama = db.Column(db.Text)
    durum = db.Column(db.String(20), default='bekliyor')  # bekliyor, onaylandı, tamamlandı, iptal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    musteri_degerlendirdi = db.Column(db.Boolean, default=False)
    tamirci_feedback_verdi = db.Column(db.Boolean, default=False)

    customer = db.relationship('Kullanici', foreign_keys=[musteri_id], backref='musteri_randevular')
    mechanic = db.relationship('Kullanici', foreign_keys=[tamirci_id], backref='tamirci_randevular')

class Mesaj(db.Model):
    __tablename__ = 'mesaj'
    id = db.Column(db.Integer, primary_key=True)
    gonderici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    alici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    icerik = db.Column(db.Text, nullable=False)
    zaman_d = db.Column(db.DateTime, default=datetime.utcnow)
    okundu_mu = db.Column(db.Boolean, default=False)

class TamirciDegerlendirme(db.Model):
    __tablename__ = 'tamirci_degerlendirme'
    id = db.Column(db.Integer, primary_key=True)
    musteri_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    tamirci_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    randevu_id = db.Column(db.Integer, db.ForeignKey('randevu.id'), nullable=False)
    puan = db.Column(db.Integer, nullable=False)  # 1-5 arası puanlama
    yorum = db.Column(db.Text)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    musteri = db.relationship('Kullanici', foreign_keys=[musteri_id], backref='verilen_degerlendirmeler')
    tamirci = db.relationship('Kullanici', foreign_keys=[tamirci_id], backref='alinan_degerlendirmeler')
    randevu = db.relationship('Randevu', backref='degerlendirme')

class MusteriFeedback(db.Model):
    __tablename__ = 'musteri_feedback'
    id = db.Column(db.Integer, primary_key=True)
    musteri_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    tamirci_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    randevu_id = db.Column(db.Integer, db.ForeignKey('randevu.id'), nullable=False)
    tip = db.Column(db.String(50), nullable=False)  # Örn: "randevu_zamanlama", "davranis"
    deger = db.Column(db.Boolean, nullable=False)  # True: Olumlu, False: Olumsuz
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    musteri = db.relationship('Kullanici', foreign_keys=[musteri_id], backref='alinan_feedbackler')
    tamirci = db.relationship('Kullanici', foreign_keys=[tamirci_id], backref='verilen_feedbackler')
    randevu = db.relationship('Randevu', backref='musteri_feedbackler')

# Simple forms
class GirisForm(FlaskForm): #https://stackoverflow.com/questions/46092054/flask-login-documentation-GirisForm
    eposta = StringField('E-posta', validators=[DataRequired()])
    sifre = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('Giriş Yap')

class MusteriKayitForm(FlaskForm):
    isim = StringField('Ad Soyad', validators=[DataRequired()])
    eposta = StringField('E-posta', validators=[DataRequired()])
    telefon = StringField('Telefon', validators=[DataRequired()])
    sifre = PasswordField('Şifre', validators=[DataRequired()])
    onay_sifre = PasswordField('Şifreyi Doğrula', validators=[DataRequired(), EqualTo('sifre', message='Şifreler eşleşmiyor!')])
    submit = SubmitField('Kayıt Ol')

class TamirciKayitForm(FlaskForm):
    isim = StringField('Tamirhane Adı', validators=[DataRequired()])
    eposta = StringField('E-posta', validators=[DataRequired(), Email()])
    telefon = StringField('Telefon', validators=[DataRequired()])
    sehir = SelectField('Şehir', coerce=int, validators=[DataRequired()])
    ilce = SelectField('İlçe', validators=[DataRequired()])
    adres = TextAreaField('Adres', validators=[DataRequired()])
    uzmanlik_alani = SelectField('Uzmanlık Alanı', coerce=int, validators=[DataRequired()])
    sifre = PasswordField('Şifre', validators=[DataRequired()])
    onay_sifre = PasswordField('Şifreyi Doğrula', validators=[DataRequired(), EqualTo('sifre', message='Şifreler eşleşmiyor!')])
    submit = SubmitField('Kayıt Ol')
    
    def validate_eposta(self, eposta):
        user = Kullanici.query.filter_by(eposta=eposta.data).first()
        if user:
            raise ValidationError('Bu e-posta zaten kullanılıyor. Lütfen başka bir e-posta adresi girin.')

class RandevuForm(FlaskForm):
    tamirci_id = HiddenField('Tamirhane ID', validators=[DataRequired()])
    randevu_date = DateTimeField('Randevu Tarihi ve Saati', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    arac_detay = StringField('Araç Bilgileri', validators=[DataRequired()])
    servis_aciklama = TextAreaField('Servis Açıklaması', validators=[DataRequired()])
    submit = SubmitField('Randevu Al')

class MesajForm(FlaskForm):
    alici_id = HiddenField('Alıcı ID', validators=[DataRequired()])
    icerik = TextAreaField('Mesaj', validators=[DataRequired()])
    submit = SubmitField('Gönder')

class AramaForm(FlaskForm):
    sehir = SelectField('Şehir', coerce=int)
    ilce = SelectField('İlçe', coerce=str)
    uzmanlik_alani = SelectField('Uzmanlık Alanı', coerce=int)
    submit = SubmitField('Ara')

# Tamirci Değerlendirme Formu (müşteriler için)
class TamirciDegerlendirmeForm(FlaskForm):
    puan = SelectField('Puan', choices=[(1, '1 Yıldız'), (2, '2 Yıldız'), (3, '3 Yıldız'), (4, '4 Yıldız'), (5, '5 Yıldız')], coerce=int, validators=[DataRequired()])
    yorum = TextAreaField('Yorumunuz', validators=[DataRequired()])
    randevu_id = HiddenField('Randevu ID', validators=[DataRequired()])
    tamirci_id = HiddenField('Tamirci ID', validators=[DataRequired()])
    submit = SubmitField('Değerlendirmeyi Gönder')

# Müşteri Feedback Formu (tamirciler için)
# Müşteri Feedback Formu (tamirciler için)
class MusteriFeedbackForm(FlaskForm):
    randevu_zamanlama = RadioField('Randevu Zamanlaması', 
                           choices=[
                               ('positive', 'Randevuya zamanında geldi'), 
                               ('negative', 'Randevuya geç geldi')
                           ], validators=[DataRequired(message="Lütfen bir seçenek belirtin.")])
    
    davranis = RadioField('Davranış', 
                 choices=[
                     ('positive', 'Nazik ve saygılıydı'), 
                     ('negative', 'Kaba veya sorunluydu')
                 ], validators=[DataRequired(message="Lütfen bir seçenek belirtin.")])
    
    isbirligi = RadioField('İşbirliği', 
                  choices=[
                      ('positive', 'İşbirliğine açıktı'), 
                      ('negative', 'İşbirliği yapmadı')
                  ], validators=[DataRequired(message="Lütfen bir seçenek belirtin.")])
    
    randevu_id = HiddenField('Randevu ID', validators=[DataRequired()])
    musteri_id = HiddenField('Müşteri ID', validators=[DataRequired()])
    submit = SubmitField('Feedback Gönder')

# Yardımcı Fonksiyonlar.
def giris_sart(f): #https://pythonprogramming.net/decorator-wrappers-flask-tutorial-login-required/#google_vignette
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'kullanici_id' not in session:
            flash('Giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def musteri_sart(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'kullanici_id' not in session or session['kullanici_tipi'] != 'customer':
            flash('Bu sayfa sadece müşteriler içindir.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def tamirci_sart(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'kullanici_id' not in session or session['kullanici_tipi'] != 'mechanic':
            flash('Bu sayfa sadece tamirciler içindir.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Basic date formatter for templates
@tamircim.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    return value.strftime(format)

# Routes
@tamircim.route('/')
def index():
    form = AramaForm()
    
    # Form seçeneklerini doldur
    sehirler = Sehir.query.all()
    form.sehir.choices = [(0, 'Tüm Şehirler')] + [(sehir.id, sehir.isim) for sehir in sehirler]
    
    uzmanlik_alanlari = UzmanlikAlani.query.all()
    form.uzmanlik_alani.choices = [(0, 'Tüm Uzmanlıklar')] + [(alan.id, alan.isim) for alan in uzmanlik_alanlari]
    
    form.ilce.choices = [(0, 'Tüm İlçeler')]
    
    # Filtre uygulama
    query = Kullanici.query.filter_by(kullanici_tipi='mechanic')
    
    sehir_id = request.args.get('sehir', type=int)
    ilce_id = request.args.get('ilce', type=int)
    uzmanlik_id = request.args.get('uzmanlik_alani', type=int)
    
    if sehir_id and sehir_id > 0:
        form.sehir.data = sehir_id
        sehir = Sehir.query.get(sehir_id)
        if sehir:
            query = query.filter(Kullanici.sehir == sehir.isim)
        
        # Seçilen şehir için ilçeleri yükle
        ilceler = Ilce.query.filter_by(sehir_id=sehir_id).all()
        form.ilce.choices = [(0, 'Tüm İlçeler')] + [(ilce.id, ilce.isim) for ilce in ilceler]
        
        if ilce_id and ilce_id > 0:
            form.ilce.data = ilce_id
            ilce = Ilce.query.get(ilce_id)
            if ilce:
                query = query.filter(Kullanici.ilce == ilce.isim)
    
    if uzmanlik_id and uzmanlik_id > 0:
        form.uzmanlik_alani.data = uzmanlik_id
        uzmanlik = UzmanlikAlani.query.get(uzmanlik_id)
        if uzmanlik:
            query = query.filter(Kullanici.uzmanlik_alani == uzmanlik.isim)
    
    # Pagination ekle
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    tamirciler = pagination.items
    
    return render_template('index.html', 
                           form=form, 
                           tamirciler=tamirciler,
                           pagination=pagination)

@tamircim.route('/get_districts/<int:sehir_id>')
def ilceleri_getir(sehir_id):
    ilceler = Ilce.query.filter_by(sehir_id=sehir_id).all()
    return jsonify({
        'districts': [{'id': d.id, 'isim': d.isim, 'name': d.isim} for d in ilceler]
    })

@tamircim.route('/login', methods=['GET', 'POST'])
def login():
    if 'kullanici_id' in session:
        if session['kullanici_tipi'] == 'customer':
            return redirect(url_for('musteri_panel'))
        else:
            return redirect(url_for('tamirci_panel'))
    
    form = GirisForm()
    if form.validate_on_submit():
        user = Kullanici.query.filter_by(eposta=form.eposta.data).first()
        
        # Şifre kontrolü ile doğrulama
        if user and check_password_hash(user.sifre, form.sifre.data):
            session['kullanici_id'] = user.id
            session['kullanici_tipi'] = user.kullanici_tipi
            session['isim'] = user.isim
            
            flash(f'Hoş geldiniz, {user.isim}!', 'success')
            
            if user.is_customer():
                return redirect(url_for('musteri_panel'))
            else:
                return redirect(url_for('tamirci_panel'))
        else:
            flash('E-posta veya şifre hatalı!', 'danger')
    
    return render_template('login.html', form=form)


@tamircim.route('/logout')
def cikis():
    session.clear()
    flash('Çıkış yapıldı!', 'success')
    return redirect(url_for('index'))

@tamircim.route('/register/customer', methods=['GET', 'POST'])
def kayit_musteri():
    form = MusteriKayitForm()
    if form.validate_on_submit():
        user = Kullanici(
            isim=form.isim.data,
            eposta=form.eposta.data,
            telefon=form.telefon.data,
            sifre=generate_password_hash(form.sifre.data),
            kullanici_tipi='customer'
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_customer.html', form=form)

@tamircim.route('/register/mechanic', methods=['GET', 'POST'])
def kayit_tamirci():
    form = TamirciKayitForm()
    
    # Form seçeneklerini doldur
    sehirler = Sehir.query.all()
    form.sehir.choices = [(sehir.id, sehir.isim) for sehir in sehirler]
    
    uzmanlik_alanlari = UzmanlikAlani.query.all()
    form.uzmanlik_alani.choices = [(alan.id, alan.isim) for alan in uzmanlik_alanlari]
    
    # Seçili şehre göre ilçeleri doldur
    if form.sehir.data:
        ilceler = Ilce.query.filter_by(sehir_id=form.sehir.data).all()
        form.ilce.choices = [(ilce.id, ilce.isim) for ilce in ilceler]
    else:
        form.ilce.choices = [('', 'Önce şehir seçin')]
    
    if form.validate_on_submit():
        # Şehir, ilçe ve uzmanlık alanı isimlerini al
        sehir = Sehir.query.get(form.sehir.data)
        ilce = Ilce.query.get(form.ilce.data)
        uzmanlik = UzmanlikAlani.query.get(form.uzmanlik_alani.data)
        
        user = Kullanici(
            isim=form.isim.data,
            eposta=form.eposta.data,
            telefon=form.telefon.data,
            sifre=generate_password_hash(form.sifre.data),
            kullanici_tipi='mechanic',
            sehir=sehir.isim if sehir else None,
            ilce=ilce.isim if ilce else None,
            adres=form.adres.data,
            uzmanlik_alani=uzmanlik.isim if uzmanlik else None
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_mechanic.html', form=form)

@tamircim.route('/customer/dashboard')
@giris_sart
@musteri_sart
def musteri_panel():
    kullanici_id = session.get('kullanici_id')
    randevular = Randevu.query.filter_by(musteri_id=kullanici_id).order_by(Randevu.randevu_date.desc()).all()
    mesajlar = Mesaj.query.filter_by(alici_id=kullanici_id).order_by(Mesaj.zaman_d.desc()).limit(3).all()
    okunmamis_mesajlar = Mesaj.query.filter_by(alici_id=kullanici_id, okundu_mu=False).count()
    
    return render_template('customer_dashboard.html', 
                           randevular=randevular,
                           mesajlar=mesajlar, 
                           okunmamis_mesajlar=okunmamis_mesajlar)

@tamircim.route('/mechanic/dashboard')
@giris_sart
@tamirci_sart
def tamirci_panel():
    kullanici_id = session.get('kullanici_id')
    tamirci = Kullanici.query.get_or_404(kullanici_id)
    randevular = Randevu.query.filter_by(tamirci_id=kullanici_id).order_by(Randevu.randevu_date.desc()).all()
    mesajlar = Mesaj.query.filter_by(alici_id=kullanici_id).order_by(Mesaj.zaman_d.desc()).limit(3).all()
    okunmamis_mesajlar = Mesaj.query.filter_by(alici_id=kullanici_id, okundu_mu=False).count()
    
    return render_template('mechanic_dashboard.html', 
                           tamirci=tamirci,
                           randevular=randevular,
                           mesajlar=mesajlar, 
                           okunmamis_mesajlar=okunmamis_mesajlar)

@tamircim.route('/mechanic/<int:tamirci_id>')
def tamirci_profil(tamirci_id):
    tamirci = Kullanici.query.filter_by(id=tamirci_id, kullanici_tipi='mechanic').first_or_404()
    form = RandevuForm()
    form.tamirci_id.data = tamirci_id
    
    # Tamircinin değerlendirmelerini al
    degerlendirmeler = TamirciDegerlendirme.query.filter_by(tamirci_id=tamirci_id).order_by(TamirciDegerlendirme.tarih.desc()).all()
    
    return render_template('mechanic_profile.html', tamirci=tamirci, form=form, degerlendirmeler=degerlendirmeler)

@tamircim.route('/book-appointment/<int:tamirci_id>', methods=['GET', 'POST'])
@giris_sart
@musteri_sart
def book_appointment(tamirci_id): #chatgpt'den destek alınmıştır.
    tamirci = Kullanici.query.filter_by(id=tamirci_id, kullanici_tipi='mechanic').first_or_404()
    form = RandevuForm()
    form.tamirci_id.data = tamirci_id
    
    if form.validate_on_submit():
        musteri_id = session.get('kullanici_id')
        
        randevu = Randevu(
            musteri_id=musteri_id,
            tamirci_id=tamirci_id,
            randevu_date=form.randevu_date.data,
            arac_detay=form.arac_detay.data,
            servis_aciklama=form.servis_aciklama.data,
            durum='bekliyor'
        )
        
        db.session.add(randevu)
        db.session.commit()
        
        flash('Randevu talebiniz oluşturuldu. Tamirci onayı bekleniyor.', 'success')
        return redirect(url_for('musteri_panel'))
    
    return render_template('book_appointment.html', form=form, tamirci=tamirci)
    
@tamircim.route('/appointment/create', methods=['GET', 'POST'])
@giris_sart
@musteri_sart
def randevu_olustur():
    # GET istekleri için tamirci_id URL parametresinden al
    tamirci_id = request.args.get('tamirci_id', type=int)
    if not tamirci_id:
        flash('Tamirci ID bulunamadı.', 'danger')
        return redirect(url_for('index'))
        
    # Tamircinin var olup olmadığını kontrol et
    tamirci = Kullanici.query.filter_by(id=tamirci_id, kullanici_tipi='mechanic').first_or_404()
    
    # Form oluştur
    form = RandevuForm()
    form.tamirci_id.data = tamirci_id
    
    # POST istekleri için
    if form.validate_on_submit():
        musteri_id = session.get('kullanici_id')
        tamirci_id = form.tamirci_id.data
        
        randevu = Randevu(
            musteri_id=musteri_id,
            tamirci_id=tamirci_id,
            randevu_date=form.randevu_date.data,
            arac_detay=form.arac_detay.data,
            servis_aciklama=form.servis_aciklama.data,
            durum='bekliyor'
        )
        
        db.session.add(randevu)
        db.session.commit()
        
        flash('Randevu talebiniz oluşturuldu. Tamirci onayı bekleniyor.', 'success')
        return redirect(url_for('musteri_panel'))
    
    # Hata durumunda
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
        return redirect(url_for('index'))
    
    # GET isteği için form görüntüleme
    return render_template('book_appointment.html', form=form, tamirci=tamirci)

@tamircim.route('/appointment/<int:appointment_id>/<string:action>')
@giris_sart
def randevu_guncelle(appointment_id, action):
    randevu = Randevu.query.get_or_404(appointment_id)
    
    # Yetkinin kontrol edilmesi
    if session['kullanici_tipi'] == 'mechanic' and randevu.tamirci_id != session['kullanici_id']:
        flash('Bu randevu için işlem yapamazsınız.', 'danger')
        return redirect(url_for('tamirci_panel'))
    
    if session['kullanici_tipi'] == 'customer' and randevu.musteri_id != session['kullanici_id']:
        flash('Bu randevu için işlem yapamazsınız.', 'danger')
        return redirect(url_for('musteri_panel'))
    
    # İşlemin uygulanması
    if action == 'onay' and session['kullanici_tipi'] == 'mechanic':
        randevu.durum = 'onaylandı'
        flash('Randevu onaylandı.', 'success')
    elif action == 'iptal':
        randevu.durum = 'iptal'
        flash('Randevu iptal edildi.', 'success')
    elif action == 'tamamla' and session['kullanici_tipi'] == 'mechanic':
        randevu.durum = 'tamamlandı'
        flash('Randevu tamamlandı olarak işaretlendi.', 'success')
    else:
        flash('Geçersiz işlem.', 'danger')
    
    db.session.commit()
    
    # Yönlendirmenin yapılması
    if session['kullanici_tipi'] == 'mechanic':
        return redirect(url_for('tamirci_panel'))
    else:
        return redirect(url_for('musteri_panel'))

@tamircim.route('/customer/appointments')
@giris_sart
@musteri_sart
def musteri_randevular():
    kullanici_id = session.get('kullanici_id')
    randevular = Randevu.query.filter_by(musteri_id=kullanici_id).order_by(Randevu.randevu_date.desc()).all()
    return render_template('customer_appointments.html', randevular=randevular)

@tamircim.route('/mechanic/appointments')
@giris_sart
@tamirci_sart
def tamirci_randevular():
    kullanici_id = session.get('kullanici_id')
    randevular = Randevu.query.filter_by(tamirci_id=kullanici_id).order_by(Randevu.randevu_date.desc()).all()
    return render_template('mechanic_appointments.html', randevular=randevular)

@tamircim.route('/customer/messages')
@giris_sart
@musteri_sart
def musteri_mesajları():
    kullanici_id = session.get('kullanici_id')
    
    # Müşterinin mesajlaştığı tamircileri bul
    tamirciler = []
    mesajlar = Mesaj.query.filter(
        (Mesaj.gonderici_id == kullanici_id) | (Mesaj.alici_id == kullanici_id)
    ).all()
    
    tamirci_idleri = set()
    for mesaj in mesajlar:
        if mesaj.gonderici_id != kullanici_id:
            tamirci_idleri.add(mesaj.gonderici_id)
        elif mesaj.alici_id != kullanici_id:
            tamirci_idleri.add(mesaj.alici_id)
    
    for tamirci_id in tamirci_idleri:
        tamirci = Kullanici.query.filter_by(id=tamirci_id, kullanici_tipi='mechanic').first()
        if tamirci:
            son_mesaj = Mesaj.query.filter(
                ((Mesaj.gonderici_id == kullanici_id) & (Mesaj.alici_id == tamirci_id)) |
                ((Mesaj.gonderici_id == tamirci_id) & (Mesaj.alici_id == kullanici_id))
            ).order_by(Mesaj.zaman_d.desc()).first()
            
            okunmamis = Mesaj.query.filter_by(
                gonderici_id=tamirci_id, 
                alici_id=kullanici_id, 
                okundu_mu=False
            ).count()
            
            tamirciler.append({
                'id': tamirci.id,
                'isim': tamirci.isim,
                'son_mesaj': son_mesaj,
                'okunmamis': okunmamis
            })
    
    return render_template('customer_messages.html', tamirciler=tamirciler)

@tamircim.route('/mechanic/messages')
@giris_sart
@tamirci_sart
def tamirci_mesajları():
    kullanici_id = session.get('kullanici_id')
    
    # Tamircinin mesajlaştığı müşterileri bul
    musteriler = []
    mesajlar = Mesaj.query.filter(
        (Mesaj.gonderici_id == kullanici_id) | (Mesaj.alici_id == kullanici_id)
    ).all()
    
    musteri_idleri = set()
    for mesaj in mesajlar:
        if mesaj.gonderici_id != kullanici_id:
            musteri_idleri.add(mesaj.gonderici_id)
        elif mesaj.alici_id != kullanici_id:
            musteri_idleri.add(mesaj.alici_id)
    
    for musteri_id in musteri_idleri:
        musteri = Kullanici.query.filter_by(id=musteri_id, kullanici_tipi='customer').first()
        if musteri:
            son_mesaj = Mesaj.query.filter(
                ((Mesaj.gonderici_id == kullanici_id) & (Mesaj.alici_id == musteri_id)) |
                ((Mesaj.gonderici_id == musteri_id) & (Mesaj.alici_id == kullanici_id))
            ).order_by(Mesaj.zaman_d.desc()).first()
            
            okunmamis = Mesaj.query.filter_by(
                gonderici_id=musteri_id, 
                alici_id=kullanici_id, 
                okundu_mu=False
            ).count()
            
            musteriler.append({
                'id': musteri.id,
                'isim': musteri.isim,
                'son_mesaj': son_mesaj,
                'okunmamis': okunmamis
            })
    
    return render_template('mechanic_messages.html', musteriler=musteriler)

@tamircim.route('/conversation/<int:alici_id>', methods=['GET', 'POST'])
@giris_sart
def view_conversation(alici_id):
    kullanici_id = session.get('kullanici_id')
    kullanici = Kullanici.query.get_or_404(kullanici_id)
    alici = Kullanici.query.get_or_404(alici_id)
    
    # Kullanıcı türleri kontrolü
    if kullanici.kullanici_tipi == alici.kullanici_tipi:
        flash('Geçersiz alıcı.', 'danger')
        return redirect(url_for('index'))
    
    form = MesajForm()
    form.alici_id.data = alici_id
    
    if form.validate_on_submit():
        mesaj = Mesaj(
            gonderici_id=kullanici_id,
            alici_id=alici_id,
            icerik=form.icerik.data,
            okundu_mu=False
        )
        
        db.session.add(mesaj)
        db.session.commit()
        
        flash('Mesaj gönderildi.', 'success')
        return redirect(url_for('view_conversation', alici_id=alici_id))
    
    # Konuşma geçmişini getir
    mesajlar = Mesaj.query.filter(
        ((Mesaj.gonderici_id == kullanici_id) & (Mesaj.alici_id == alici_id)) |
        ((Mesaj.gonderici_id == alici_id) & (Mesaj.alici_id == kullanici_id))
    ).order_by(Mesaj.zaman_d).all()
    
    # Okunmamış mesajları okundu olarak işaretle
    for mesaj in mesajlar:
        if mesaj.alici_id == kullanici_id and not mesaj.okundu_mu:
            mesaj.okundu_mu = True
    
    db.session.commit()
    
    return render_template('view_conversation.html', 
                           mesajlar=mesajlar, 
                           alici=alici, 
                           form=form)

# Musteri Profil route'u yalnızca tamirciler tarafından görülebilir
@tamircim.route('/customer/<int:musteri_id>')
@giris_sart
@tamirci_sart
def musteri_profil(musteri_id):
    musteri = Kullanici.query.filter_by(id=musteri_id, kullanici_tipi='customer').first_or_404()
    
    # Müşteri hakkındaki feedbackleri al
    feedbackler = db.session.query(
        MusteriFeedback.tip,
        MusteriFeedback.deger,
        db.func.count(MusteriFeedback.id).label('toplam')
    ).filter_by(musteri_id=musteri_id).group_by(MusteriFeedback.tip, MusteriFeedback.deger).all()
    
    # Feedbackleri organize et
    musteri_feedbackler = {
        'randevu_zamanlama': {'positive': 0, 'negative': 0},
        'davranis': {'positive': 0, 'negative': 0},
        'isbirligi': {'positive': 0, 'negative': 0}
    }
    
    for feedback in feedbackler:
        if feedback.deger:
            musteri_feedbackler[feedback.tip]['positive'] = feedback.toplam
        else:
            musteri_feedbackler[feedback.tip]['negative'] = feedback.toplam
    
    return render_template('customer_profile.html', musteri=musteri, feedbackler=musteri_feedbackler)

# Tamirci Değerlendirme (Müşteri tarafından)
@tamircim.route('/tamirci/degerlendirme/<int:tamirci_id>/<int:randevu_id>', methods=['GET', 'POST'])
@giris_sart
@musteri_sart
def tamirci_degerlendirme(tamirci_id, randevu_id):
    # Randevu bilgilerini al
    randevu = Randevu.query.get_or_404(randevu_id)
    tamirci = Kullanici.query.get_or_404(tamirci_id)
    
    # Randevunun müşteriye ait olup olmadığını ve tamamlanmış olduğunu kontrol et
    if randevu.musteri_id != session['kullanici_id'] or randevu.tamirci_id != tamirci_id:
        flash('Bu randevuyu değerlendirme yetkiniz yok.', 'danger')
        return redirect(url_for('musteri_randevular'))
    
    # Randevunun tamamlanmış olup olmadığını kontrol et
    if randevu.durum != 'tamamlandı':
        flash('Sadece tamamlanmış randevuları değerlendirebilirsiniz.', 'warning')
        return redirect(url_for('musteri_randevular'))
    
    # Zaten değerlendirilmiş mi kontrol et
    if randevu.musteri_degerlendirdi:
        flash('Bu randevu için zaten değerlendirme yapmışsınız.', 'info')
        return redirect(url_for('musteri_randevular'))
    
    form = TamirciDegerlendirmeForm()
    form.tamirci_id.data = tamirci_id
    form.randevu_id.data = randevu_id
    
    if form.validate_on_submit():
        degerlendirme = TamirciDegerlendirme(
            musteri_id=session['kullanici_id'],
            tamirci_id=tamirci_id,
            randevu_id=randevu_id,
            puan=form.puan.data,
            yorum=form.yorum.data
        )
        
        # Tamircinin ortalama puanını güncelle
        tamirci.puan_sayisi += 1
        yeni_ortalama = ((tamirci.ortalama_puan * (tamirci.puan_sayisi - 1)) + form.puan.data) / tamirci.puan_sayisi
        tamirci.ortalama_puan = yeni_ortalama
        
        # Randevuyu değerlendirildi olarak işaretle
        randevu.musteri_degerlendirdi = True
        
        db.session.add(degerlendirme)
        db.session.commit()
        
        flash('Değerlendirmeniz için teşekkürler!', 'success')
        return redirect(url_for('musteri_randevular'))
    
    return render_template('tamirci_degerlendirme.html', form=form, tamirci=tamirci, randevu=randevu)

# Müşteri Feedback (Tamirci tarafından)
@tamircim.route('/musteri/feedback/<int:musteri_id>/<int:randevu_id>', methods=['GET', 'POST'])
@giris_sart
@tamirci_sart
def musteri_feedback(musteri_id, randevu_id):
    # Randevu bilgilerini al
    randevu = Randevu.query.get_or_404(randevu_id)
    musteri = Kullanici.query.get_or_404(musteri_id)
    
    # Randevunun tamirciye ait olup olmadığını ve tamamlanmış olduğunu kontrol et
    if randevu.tamirci_id != session['kullanici_id'] or randevu.musteri_id != musteri_id:
        flash('Bu müşteri için feedback verme yetkiniz yok.', 'danger')
        return redirect(url_for('tamirci_randevular'))
    
    # Randevunun tamamlanmış olup olmadığını kontrol et
    if randevu.durum != 'tamamlandı':
        flash('Sadece tamamlanmış randevular için feedback verebilirsiniz.', 'warning')
        return redirect(url_for('tamirci_randevular'))
    
    # Zaten feedback verilmiş mi kontrol et
    if randevu.tamirci_feedback_verdi:
        flash('Bu randevu için zaten feedback vermişsiniz.', 'info')
        return redirect(url_for('tamirci_randevular'))
    
    form = MusteriFeedbackForm()
    form.musteri_id.data = musteri_id
    form.randevu_id.data = randevu_id
    
    if form.validate_on_submit():
        print("Form validation successful!")  # Debug için
        print(f"Zamanlama: {form.randevu_zamanlama.data}")  # Debug için
        print(f"Davranış: {form.davranis.data}")  # Debug için
        print(f"İşbirliği: {form.isbirligi.data}")  # Debug için
        
        # Randevu zamanlaması feedback'i ekle
        randevu_zamanlama = MusteriFeedback(
            musteri_id=musteri_id,
            tamirci_id=session['kullanici_id'],
            randevu_id=randevu_id,
            tip='randevu_zamanlama',
            deger=(form.randevu_zamanlama.data == 'positive')
        )
        
        # Davranış feedback'i ekle
        davranis = MusteriFeedback(
            musteri_id=musteri_id,
            tamirci_id=session['kullanici_id'],
            randevu_id=randevu_id,
            tip='davranis',
            deger=(form.davranis.data == 'positive')
        )
        
        # İşbirliği feedback'i ekle
        isbirligi = MusteriFeedback(
            musteri_id=musteri_id,
            tamirci_id=session['kullanici_id'],
            randevu_id=randevu_id,
            tip='isbirligi',
            deger=(form.isbirligi.data == 'positive')
        )
        
        # Randevuyu feedback verildi olarak işaretle
        randevu.tamirci_feedback_verdi = True
        
        db.session.add_all([randevu_zamanlama, davranis, isbirligi])
        db.session.commit()
        
        flash('Feedback\'iniz için teşekkürler!', 'success')
        return redirect(url_for('tamirci_randevular'))
    elif request.method == 'POST':
        print("Form validation failed!")  # Debug için
        print(form.errors)  # Debug için
    
    return render_template('musteri_feedback.html', form=form, musteri=musteri, randevu=randevu)

if __name__ == '__main__':
    tamircim.run(host='0.0.0.0', port=5000, debug=True)
