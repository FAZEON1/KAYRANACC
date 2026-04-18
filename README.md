# 💳 KAYRANACC — Haftalık Ödeme Takip Sistemi

Streamlit ile geliştirilmiş, SQLite tabanlı haftalık ödeme yönetim uygulaması.

## Özellikler

- 📊 **Dashboard** — Özet metrikler, alarm sistemi, nakit durum
- 💳 **Haftalık Ödemeler** — Günlük takvim, ödeme işaretle, öncelik sırası
- 🏦 **Banka Bakiyeleri** — Çoklu hesap, otomatik bakiye güncelleme
- 💸 **Nakit Akış** — Günlük kümülatif analiz ve grafik
- 📋 **Firma Çekleri** — TL/USD çek takibi
- ✅ **Ödenenler** — Ödendi işaretlenen ödemeler
- 🕐 **Geçmiş** — Haftalık arşiv
- 📂 **Veri Yükleme** — Excel yükleme + Son Yüklenenler (Recents)

## Kurulum

```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub'a Push ve Streamlit Cloud Deployment

1. GitHub'da yeni bir repo oluşturun: `KAYRANACC`
2. Bu dosyaları push edin
3. [Streamlit Cloud](https://share.streamlit.io) → New App → Repo seçin
4. **Secrets** bölümünden kullanıcıları ekleyin (bkz. `SIFRE_KURULUM.md`)

## Excel Format

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| HAFTA ADI | - | - | - | - | - | - | - |
| (boş) | - | - | - | - | - | - | - |
| (boş) | FİRMA | AÇIKLAMA | (boş) | VADE | TUTAR TL | TUTAR USD | KATEGORİ |

**Kategoriler:** cek · kredi · kart · vergi · sgk · kira · sabit · cari · diger
