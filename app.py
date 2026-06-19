from flask import Flask, jsonify, request

app = Flask(__name__)

# Enes'in Güvenlik Veritabanı
KULLANICILAR = {
    "enes_admin": {
        "sifre": "EnesUzmanYazilimci2026",
        "home_id": "EV_BURSA_16"
    }
}

ev_durumu = {
    "EV_BURSA_16": {
        "kapi_kilitli": True,
        "wifi_aktif": True
    }
}

@app.route('/')
def ana_sayfa():
    return "🔒 Enes Güvenlik Sunucusu Dünyaya Açık ve Aktif!"

@app.route('/ev/kontrol', methods=['POST'])
def ev_kontrol():
    veri = request.json
    kullanici = veri.get("kullanici")
    sifre = veri.get("sifre")
    home_id = veri.get("home_id")
    islem = veri.get("islem")

    if kullanici in KULLANICILAR and KULLANICILAR[kullanici]["sifre"] == sifre:
        if KULLANICILAR[kullanici]["home_id"] == home_id:
            if islem == "kapi":
                ev_durumu[home_id]["kapi_kilitli"] = not ev_durumu[home_id]["kapi_kilitli"]
                durum = "KİLİTLİ" if ev_durumu[home_id]["kapi_kilitli"] else "AÇIK"
                return jsonify({"durum": "Başarılı", "mesaj": f"Kapı: {durum}"}), 200
            elif islem == "wifi":
                ev_durumu[home_id]["wifi_aktif"] = not ev_durumu[home_id]["wifi_aktif"]
                durum = "AKTİF" if ev_durumu[home_id]["wifi_aktif"] else "KAPALI"
                return jsonify({"durum": "Başarılı", "mesaj": f"Wi-Fi: {durum}"}), 200
        return jsonify({"durum": "Hata", "mesaj": "Yetkisiz Ev Kimliği!"}), 403
    return jsonify({"durum": "Hata", "mesaj": "Giriş Bilgileri Yanlış."}), 401