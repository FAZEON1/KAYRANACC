import sqlite3
import os
from datetime import datetime

DB_PATH = "kayranacc.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    conn = get_conn()
    c = conn.cursor()

    # Haftalar tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS haftalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hafta_adi TEXT NOT NULL,
            yuklendi_tarih TEXT NOT NULL,
            aktif INTEGER DEFAULT 0
        )
    """)

    # Ödemeler tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS odemeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hafta_id INTEGER NOT NULL,
            firma TEXT NOT NULL,
            aciklama TEXT,
            cari_banka TEXT,
            vade TEXT,
            tutar_tl REAL,
            tutar_usd REAL,
            kategori TEXT DEFAULT 'diger',
            manuel INTEGER DEFAULT 0,
            durum TEXT DEFAULT 'bekliyor',
            odendi_tarih TEXT,
            FOREIGN KEY (hafta_id) REFERENCES haftalar(id)
        )
    """)

    # Banka hesapları tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS bankalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hesap_adi TEXT NOT NULL,
            bakiye REAL DEFAULT 0,
            para_birimi TEXT DEFAULT 'TL'
        )
    """)

    # Çekler tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS cekler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hafta_id INTEGER,
            ref_no TEXT,
            vade TEXT,
            meblagh REAL,
            kalan REAL,
            alici TEXT,
            durum TEXT DEFAULT 'Bekliyor',
            para_birimi TEXT DEFAULT 'TL',
            tarih TEXT,
            yuklendi_tarih TEXT
        )
    """)

    # Banka işlemleri log tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS banka_islemler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banka_id INTEGER,
            odeme_id INTEGER,
            miktar REAL,
            para_birimi TEXT,
            islem_tarih TEXT,
            aciklama TEXT
        )
    """)

    conn.commit()
    conn.close()


# ── HAFTA İŞLEMLERİ ──────────────────────────────────────────────────

def get_tum_haftalar():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM haftalar ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_aktif_hafta():
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM haftalar WHERE aktif=1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def hafta_ekle(hafta_adi):
    """Yeni hafta ekle ve aktif yap."""
    conn = get_conn()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    # Tüm haftaları pasif yap
    conn.execute("UPDATE haftalar SET aktif=0")
    # Aynı isimde hafta varsa güncelle
    existing = conn.execute(
        "SELECT id FROM haftalar WHERE hafta_adi=?", (hafta_adi,)
    ).fetchone()
    if existing:
        hafta_id = existing["id"]
        conn.execute(
            "UPDATE haftalar SET aktif=1, yuklendi_tarih=? WHERE id=?",
            (now, hafta_id)
        )
        # Mevcut ödemeleri sil (üzerine yaz)
        conn.execute("DELETE FROM odemeler WHERE hafta_id=?", (hafta_id,))
    else:
        cur = conn.execute(
            "INSERT INTO haftalar (hafta_adi, yuklendi_tarih, aktif) VALUES (?,?,1)",
            (hafta_adi, now)
        )
        hafta_id = cur.lastrowid
    conn.commit()
    conn.close()
    return hafta_id


def hafta_aktif_yap(hafta_id):
    conn = get_conn()
    conn.execute("UPDATE haftalar SET aktif=0")
    conn.execute("UPDATE haftalar SET aktif=1 WHERE id=?", (hafta_id,))
    conn.commit()
    conn.close()


def hafta_sil(hafta_id):
    conn = get_conn()
    conn.execute("DELETE FROM odemeler WHERE hafta_id=?", (hafta_id,))
    conn.execute("DELETE FROM cekler WHERE hafta_id=?", (hafta_id,))
    conn.execute("DELETE FROM haftalar WHERE id=?", (hafta_id,))
    conn.commit()
    conn.close()


# ── ÖDEME İŞLEMLERİ ──────────────────────────────────────────────────

def odeme_ekle_bulk(hafta_id, odemeler):
    conn = get_conn()
    for o in odemeler:
        conn.execute("""
            INSERT INTO odemeler (hafta_id, firma, aciklama, cari_banka, vade, tutar_tl, tutar_usd, kategori, manuel)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            hafta_id,
            o.get("firma", ""),
            o.get("aciklama", ""),
            o.get("cari_banka", ""),
            o.get("vade", ""),
            o.get("tl"),
            o.get("usd"),
            o.get("kategori", "diger"),
            o.get("manuel", 0)
        ))
    conn.commit()
    conn.close()


def odeme_ekle_manuel(hafta_id, firma, aciklama, vade, tutar_tl, tutar_usd, kategori):
    conn = get_conn()
    conn.execute("""
        INSERT INTO odemeler (hafta_id, firma, aciklama, vade, tutar_tl, tutar_usd, kategori, manuel)
        VALUES (?,?,?,?,?,?,?,1)
    """, (hafta_id, firma, aciklama, vade, tutar_tl, tutar_usd, kategori))
    conn.commit()
    conn.close()


def get_hafta_odemeler(hafta_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM odemeler WHERE hafta_id=? ORDER BY vade, id",
        (hafta_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def odeme_durum_guncelle(odeme_id, durum, banka_id=None, kur=38.5):
    conn = get_conn()
    now = datetime.now().strftime("%d.%m.%Y %H:%M") if durum == "odendi" else None
    conn.execute(
        "UPDATE odemeler SET durum=?, odendi_tarih=? WHERE id=?",
        (durum, now, odeme_id)
    )
    # Banka bakiyesini düş
    if durum == "odendi" and banka_id is not None:
        odeme = conn.execute("SELECT * FROM odemeler WHERE id=?", (odeme_id,)).fetchone()
        banka = conn.execute("SELECT * FROM bankalar WHERE id=?", (banka_id,)).fetchone()
        if odeme and banka:
            if odeme["tutar_tl"]:
                if banka["para_birimi"] == "TL":
                    yeni = max(0, banka["bakiye"] - odeme["tutar_tl"])
                elif banka["para_birimi"] == "USD":
                    yeni = max(0, banka["bakiye"] - (odeme["tutar_tl"] / kur))
                else:
                    yeni = banka["bakiye"]
            elif odeme["tutar_usd"]:
                if banka["para_birimi"] == "USD":
                    yeni = max(0, banka["bakiye"] - odeme["tutar_usd"])
                elif banka["para_birimi"] == "TL":
                    yeni = max(0, banka["bakiye"] - (odeme["tutar_usd"] * kur))
                else:
                    yeni = banka["bakiye"]
            else:
                yeni = banka["bakiye"]
            conn.execute("UPDATE bankalar SET bakiye=? WHERE id=?", (yeni, banka_id))
            conn.execute("""
                INSERT INTO banka_islemler (banka_id, odeme_id, miktar, para_birimi, islem_tarih, aciklama)
                VALUES (?,?,?,?,?,?)
            """, (
                banka_id, odeme_id,
                odeme["tutar_tl"] or odeme["tutar_usd"],
                "TL" if odeme["tutar_tl"] else "USD",
                now,
                f"{odeme['firma']} ödemesi"
            ))
    conn.commit()
    conn.close()


def odeme_sil(odeme_id):
    conn = get_conn()
    conn.execute("DELETE FROM odemeler WHERE id=?", (odeme_id,))
    conn.commit()
    conn.close()


# ── BANKA İŞLEMLERİ ──────────────────────────────────────────────────

def get_bankalar():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM bankalar ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def banka_ekle(hesap_adi, bakiye, para_birimi):
    conn = get_conn()
    conn.execute(
        "INSERT INTO bankalar (hesap_adi, bakiye, para_birimi) VALUES (?,?,?)",
        (hesap_adi, bakiye, para_birimi)
    )
    conn.commit()
    conn.close()


def banka_guncelle(banka_id, hesap_adi, bakiye, para_birimi):
    conn = get_conn()
    conn.execute(
        "UPDATE bankalar SET hesap_adi=?, bakiye=?, para_birimi=? WHERE id=?",
        (hesap_adi, bakiye, para_birimi, banka_id)
    )
    conn.commit()
    conn.close()


def banka_sil(banka_id):
    conn = get_conn()
    conn.execute("DELETE FROM bankalar WHERE id=?", (banka_id,))
    conn.commit()
    conn.close()


# ── ÇEK İŞLEMLERİ ────────────────────────────────────────────────────

def cek_ekle_bulk(hafta_id, cekler, para_birimi="TL"):
    conn = get_conn()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    for c in cekler:
        conn.execute("""
            INSERT INTO cekler (hafta_id, ref_no, vade, meblagh, kalan, alici, durum, para_birimi, tarih, yuklendi_tarih)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            hafta_id,
            c.get("ref", ""),
            c.get("vade", ""),
            c.get("meblagh", 0),
            c.get("kalan", 0),
            c.get("alici", ""),
            c.get("durum", "Bekliyor"),
            para_birimi,
            c.get("tarih", ""),
            now
        ))
    conn.commit()
    conn.close()


def get_cekler(para_birimi=None):
    conn = get_conn()
    if para_birimi:
        rows = conn.execute(
            "SELECT * FROM cekler WHERE para_birimi=? ORDER BY vade",
            (para_birimi,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM cekler ORDER BY vade").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hafta_ozet(hafta_id):
    conn = get_conn()
    odemeler = conn.execute(
        "SELECT * FROM odemeler WHERE hafta_id=?", (hafta_id,)
    ).fetchall()
    conn.close()
    tl_toplam = sum(o["tutar_tl"] or 0 for o in odemeler)
    usd_toplam = sum(o["tutar_usd"] or 0 for o in odemeler)
    odendi = sum(1 for o in odemeler if o["durum"] == "odendi")
    bekliyor = sum(1 for o in odemeler if o["durum"] == "bekliyor")
    return {
        "toplam": len(odemeler),
        "odendi": odendi,
        "bekliyor": bekliyor,
        "tl_toplam": tl_toplam,
        "usd_toplam": usd_toplam,
    }
