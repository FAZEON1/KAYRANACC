import os
import streamlit as st
from supabase import create_client, Client
from datetime import date

# ── Supabase bağlantısı ──────────────────────────────────────────────
def get_client() -> Client:
    url  = st.secrets["supabase"]["url"]
    key  = st.secrets["supabase"]["service_role_key"]
    return create_client(url, key)


def initialize_db():
    pass


# ════════════════════════════════════════════════════════════════════
# HAFTALAR
# ════════════════════════════════════════════════════════════════════

def get_tum_haftalar():
    sb = get_client()
    res = sb.table("haftalar").select("*").order("id", desc=True).execute()
    return res.data or []


def get_aktif_hafta():
    sb = get_client()
    res = sb.table("haftalar").select("*").eq("aktif", 1).limit(1).execute()
    return res.data[0] if res.data else None


def hafta_ekle(hafta_adi):
    sb = get_client()
    today = date.today().strftime("%d.%m.%Y")
    res = sb.table("haftalar").insert({
        "hafta_adi": hafta_adi,
        "yuklendi_tarih": today,
        "aktif": 0
    }).execute()
    return res.data[0]["id"] if res.data else None


def hafta_aktif_yap(hafta_id):
    sb = get_client()
    sb.table("haftalar").update({"aktif": 0}).neq("id", 0).execute()
    sb.table("haftalar").update({"aktif": 1}).eq("id", hafta_id).execute()


def hafta_sil(hafta_id):
    sb = get_client()
    sb.table("odemeler").delete().eq("hafta_id", hafta_id).execute()
    sb.table("haftalar").delete().eq("id", hafta_id).execute()


# ════════════════════════════════════════════════════════════════════
# ODEMELER
# ════════════════════════════════════════════════════════════════════

def get_hafta_odemeler(hafta_id):
    sb = get_client()
    res = sb.table("odemeler").select("*").eq("hafta_id", hafta_id).order("vade").execute()
    return res.data or []


def get_aktif_odemeler():
    hafta = get_aktif_hafta()
    if not hafta:
        return [], None
    odemeler = get_hafta_odemeler(hafta["id"])
    return odemeler, hafta


def get_hafta_ozet(hafta_id):
    odemeler = get_hafta_odemeler(hafta_id)
    return {
        "toplam": len(odemeler),
        "odendi": sum(1 for o in odemeler if o["durum"] == "odendi"),
        "tl_toplam": sum(o.get("tutar_tl") or 0 for o in odemeler),
        "usd_toplam": sum(o.get("tutar_usd") or 0 for o in odemeler),
    }


def _temizle(v):
    """None, NaN ve inf değerleri temizler."""
    if v is None:
        return None
    try:
        import math
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def odeme_ekle_bulk(hafta_id, odemeler):
    sb = get_client()
    rows = []
    for o in odemeler:
        tl  = _temizle(o.get("tl"))
        usd = _temizle(o.get("usd"))
        if tl is None and usd is None:
            continue  # tutarsız satırı atla
        rows.append({
            "hafta_id":   int(hafta_id),
            "firma":      str(o.get("firma") or "")[:500],
            "aciklama":   str(o.get("aciklama") or "")[:500],
            "cari_banka": str(o.get("cari_banka") or "")[:500],
            "vade":       str(o.get("vade") or ""),
            "tutar_tl":   tl,
            "tutar_usd":  usd,
            "kategori":   str(o.get("kategori") or "diger"),
            "manuel":     int(o.get("manuel") or 0),
            "durum":      "bekliyor",
        })
    # Supabase free tier için 100'er satır halinde gönder
    BATCH = 100
    for i in range(0, len(rows), BATCH):
        sb.table("odemeler").insert(rows[i:i+BATCH]).execute()


def odeme_ekle_manuel(hafta_id, firma, aciklama, cari_banka, vade, tutar_tl, tutar_usd, kategori):
    sb = get_client()
    sb.table("odemeler").insert({
        "hafta_id": hafta_id,
        "firma": firma,
        "aciklama": aciklama,
        "cari_banka": cari_banka or "",
        "vade": vade,
        "tutar_tl": tutar_tl or None,
        "tutar_usd": tutar_usd or None,
        "kategori": kategori,
        "manuel": 1,
        "durum": "bekliyor",
    }).execute()


def odeme_durum_guncelle(odeme_id, durum):
    sb = get_client()
    today = date.today().isoformat() if durum == "odendi" else None
    sb.table("odemeler").update({
        "durum": durum,
        "odendi_tarih": today,
    }).eq("id", odeme_id).execute()


def odeme_sil(odeme_id):
    sb = get_client()
    sb.table("odemeler").delete().eq("id", odeme_id).execute()


# ════════════════════════════════════════════════════════════════════
# BANKALAR
# ════════════════════════════════════════════════════════════════════

def get_bankalar():
    sb = get_client()
    res = sb.table("bankalar").select("*").order("id").execute()
    return res.data or []


def banka_ekle(hesap_adi, para_birimi, bakiye):
    sb = get_client()
    sb.table("bankalar").insert({
        "hesap_adi": hesap_adi,
        "para_birimi": para_birimi,
        "bakiye": bakiye,
    }).execute()


def banka_guncelle(banka_id, bakiye):
    sb = get_client()
    sb.table("bankalar").update({"bakiye": bakiye}).eq("id", banka_id).execute()


def banka_sil(banka_id):
    sb = get_client()
    sb.table("bankalar").delete().eq("id", banka_id).execute()


# ════════════════════════════════════════════════════════════════════
# CEKLER
# ════════════════════════════════════════════════════════════════════

def get_cekler(para_birimi="TL"):
    sb = get_client()
    res = sb.table("cekler").select("*").eq("para_birimi", para_birimi).order("vade").execute()
    return res.data or []


def cek_ekle_bulk(cekler, para_birimi="TL"):
    sb = get_client()
    rows = []
    for c in cekler:
        rows.append({
            "ref_no":      str(c.get("ref_no") or ""),
            "cek_no":      str(c.get("cek_no") or ""),
            "tarih":       str(c.get("tarih") or ""),
            "vade":        str(c.get("vade") or ""),
            "meblagh":     _temizle(c.get("meblagh")) or 0,
            "odenen":      _temizle(c.get("odenen")) or 0,
            "kalan":       _temizle(c.get("kalan")) or 0,
            "durum":       str(c.get("durum") or "Bekliyor"),
            "ch_kodu":     str(c.get("ch_kodu") or ""),
            "ch_ismi":     str(c.get("ch_ismi") or ""),
            "banka":       str(c.get("banka") or ""),
            "sube":        str(c.get("sube") or ""),
            "hesap_no":    str(c.get("hesap_no") or ""),
            "para_birimi": str(c.get("para_birimi") or para_birimi),
        })
    BATCH = 100
    for i in range(0, len(rows), BATCH):
        sb.table("cekler").insert(rows[i:i+BATCH]).execute()
