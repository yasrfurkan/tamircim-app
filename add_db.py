from tamircim import tamircim, db, Sehir, Ilce, UzmanlikAlani, Kullanici
from werkzeug.security import generate_password_hash

with tamircim.app_context():
    # Mevcut verileri temizle (opsiyonel)
    db.drop_all()
    db.create_all()
    
    # ŞEHİRLER
    sehirler_data = [
        'İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana', 'Konya', 
        'Şanlıurfa', 'Gaziantep', 'Kocaeli', 'Mersin', 'Diyarbakır', 'Hatay',
        'Manisa', 'Kayseri', 'Samsun', 'Balıkesir', 'Kahramanmaraş', 'Van',
        'Aydın', 'Tekirdağ', 'Sakarya', 'Denizli', 'Muğla', 'Eskişehir'
    ]
    
    sehirler = []
    for sehir_adi in sehirler_data:
        sehir = Sehir(isim=sehir_adi)
        sehirler.append(sehir)
        db.session.add(sehir)
    
    db.session.commit()
    
    # İLÇELER
    ilceler_data = {
        'İstanbul': ['Kadıköy', 'Beşiktaş', 'Şişli', 'Beyoğlu', 'Fatih', 'Üsküdar', 
                     'Bakırköy', 'Zeytinburnu', 'Maltepe', 'Pendik', 'Kartal', 'Ataşehir',
                     'Bahçelievler', 'Güngören', 'Esenler', 'Bağcılar', 'Küçükçekmece',
                     'Büyükçekmece', 'Başakşehir', 'Arnavutköy', 'Eyüpsultan', 'Gaziosmanpaşa'],
        'Ankara': ['Çankaya', 'Keçiören', 'Yenimahalle', 'Mamak', 'Sincan', 'Etimesgut',
                   'Altındağ', 'Gölbaşı', 'Pursaklar', 'Kahramankazan', 'Elmadağ', 'Akyurt'],
        'İzmir': ['Konak', 'Bornova', 'Buca', 'Karşıyaka', 'Alsancak', 'Bayraklı',
                  'Çiğli', 'Gaziemir', 'Balçova', 'Narlıdere', 'Güzelbahçe', 'Menderes'],
        'Bursa': ['Osmangazi', 'Nilüfer', 'Yıldırım', 'Mudanya', 'Gemlik', 'İnegöl',
                  'Orhangazi', 'Karacabey', 'Mustafakemalpaşa', 'Büyükorhan'],
        'Antalya': ['Muratpaşa', 'Kepez', 'Konyaaltı', 'Aksu', 'Döşemealtı', 'Alanya',
                    'Manavgat', 'Serik', 'Kumluca', 'Finike', 'Kaş', 'Kalkan']
    }
    
    for sehir in sehirler[:5]:  # İlk 5 şehir için ilçe ekle
        if sehir.isim in ilceler_data:
            for ilce_adi in ilceler_data[sehir.isim]:
                ilce = Ilce(isim=ilce_adi, sehir_id=sehir.id)
                db.session.add(ilce)
    
    # Diğer şehirler için genel ilçeler
    diger_ilceler = ['Merkez', 'Cumhuriyet', 'Atatürk', 'Fatih', 'Yenişehir', 'Bahçelievler']
    for sehir in sehirler[5:]:
        for ilce_adi in diger_ilceler[:4]:  # Her şehire 4 ilçe
            ilce = Ilce(isim=ilce_adi, sehir_id=sehir.id)
            db.session.add(ilce)
    
    db.session.commit()
    
    # UZMANLIK ALANLARI
    uzmanlik_alanlari_data = [
        'Motor Tamiri', 'Fren Sistemi', 'Elektrik Sistemi', 'Klima Sistemi',
        'Şanzıman Tamiri', 'Direksiyon Sistemi', 'Egzoz Sistemi', 'Lastik ve Jant',
        'Cam ve Ayna', 'Kaporta', 'Boya', 'İç Döşeme', 'Ses Sistemi',
        'Güvenlik Sistemi', 'Yakıt Sistemi', 'Soğutma Sistemi', 'Amortisör',
        'Fren Balata', 'Yağ Değişimi', 'Periyodik Bakım', 'Hasar Tespiti',
        'Ekspertiz', 'Araç Muayene', 'Modifikasyon', 'Tuning'
    ]
    
    uzmanlik_alanlari = []
    for alan_adi in uzmanlik_alanlari_data:
        alan = UzmanlikAlani(isim=alan_adi)
        uzmanlik_alanlari.append(alan)
        db.session.add(alan)
    
    db.session.commit()
    
    # MÜŞTERİLER
    musteri_isimleri = [
        'Ahmet Yılmaz', 'Mehmet Demir', 'Ayşe Kaya', 'Fatma Çelik', 'Ali Şahin',
        'Emine Yıldız', 'Mustafa Aksoy', 'Hatice Öztürk', 'İbrahim Koç', 'Zeynep Arslan',
        'Hüseyin Taş', 'Elif Polat', 'Ömer Erdoğan', 'Merve Kılıç', 'Kadir Aydın',
        'Seda Özkan', 'Serkan Güneş', 'Dilek Çiftçi', 'Burak Güler', 'Gül Yaman',
        'Erhan Şeker', 'Pınar Demirci', 'Cem Yıldırım', 'Sibel Özdemir', 'Tolga Karaca',
        'Başak Ünal', 'Deniz Kara', 'Canan Acar', 'Emre Koçak', 'Sevgi Turan'
    ]
    
    for i, isim in enumerate(musteri_isimleri):
        musteri = Kullanici(
            isim=isim,
            eposta=f'musteri{i+1}@example.com',
            telefon=f'05{50 + i:02d}{100 + i:03d}{200 + i:04d}',
            sifre=generate_password_hash('123456'),
            kullanici_tipi='customer'
        )
        db.session.add(musteri)
    
    # TAMİRCİLER
    tamirci_isimleri = [
        'Oto Servis Merkezi', 'Profesyonel Oto Tamir', 'Hızlı Bakım Merkezi',
        'Usta Oto Servisi', 'Güvenilir Tamirhane', 'Modern Oto Bakım',
        'Kaliteli Servis', 'Deneyimli Tamirci', 'Ekonomik Oto Tamir',
        'VIP Oto Servis', 'Ekspres Tamirhane', 'Aile Oto Bakımı',
        'Teknoloji Oto Servis', 'Premium Bakım', 'Hızlı Çözüm Merkezi',
        'Güler Yüz Oto Servisi', 'Nokta Atış Tamirhane', 'Usta Eller Servisi',
        'Çözüm Ortağı Oto', 'Garantili Tamir', 'Sürat Oto Bakım',
        'Kalite Oto Servisi', 'Güven Tamirhane', 'İhtisas Oto Merkezi',
        'Pratik Çözüm Servisi', 'Oto Doktoru', 'Hızır Oto Tamir',
        'Başarı Oto Servisi', 'Emek Tamirhane', 'Oto Uzmanı'
    ]
    
    import random
    
    for i, tamirci_adi in enumerate(tamirci_isimleri):
        # Rastgele şehir ve ilçe seç
        sehir = random.choice(sehirler[:5])  # İlk 5 şehirden seç (çünkü bunlarda ilçe var)
        ilceler = Ilce.query.filter_by(sehir_id=sehir.id).all()
        ilce = random.choice(ilceler)
        
        # Rastgele uzmanlık alanı seç
        uzmanlik = random.choice(uzmanlik_alanlari)
        
        # Rastgele puan ver
        ortalama_puan = round(random.uniform(3.5, 5.0), 1)
        puan_sayisi = random.randint(5, 50)
        
        tamirci = Kullanici(
            isim=tamirci_adi,
            eposta=f'tamirci{i+1}@example.com',
            telefon=f'05{30 + i:02d}{300 + i:03d}{400 + i:04d}',
            sifre=generate_password_hash('123456'),
            kullanici_tipi='mechanic',
            sehir=sehir.isim,
            ilce=ilce.isim,
            adres=f'{ilce.isim} Mahallesi, {random.randint(1, 100)}. Sokak No: {random.randint(1, 50)}',
            uzmanlik_alani=uzmanlik.isim,
            ortalama_puan=ortalama_puan,
            puan_sayisi=puan_sayisi
        )
        db.session.add(tamirci)
    
    db.session.commit()
    
    print("Veri ekleme tamamlandı!")
    print(f"- {len(sehirler_data)} şehir")
    print(f"- {Ilce.query.count()} ilçe") 
    print(f"- {len(uzmanlik_alanlari_data)} uzmanlık alanı")
    print(f"- {len(musteri_isimleri)} müşteri")
    print(f"- {len(tamirci_isimleri)} tamirci")