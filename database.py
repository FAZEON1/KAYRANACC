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


def odeme_ekle_bulk(hafta_id, odemeler):
    sb = get_client()
    rows = []
    for o in odemeler:
        rows.append({
            "hafta_id": hafta_id,
            "firma": o.get("firma", ""),
            "aciklama": o.get("aciklama", ""),
            "cari_banka": o.get("cari_banka", ""),
            "vade": o.get("vade", ""),
            "tutar_tl": o.get("tl"),
            "tutar_usd": o.get("usd"),
            "kategori": o.get("kategori", "diger"),
            "manuel": o.get("manuel", 0),
            "durum": "bekliyor",
        })
    if rows:
        sb.table("odemeler").insert(rows).execute()


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
            "ref_no":    c.get("ref_no", ""),
            "cek_no":    c.get("cek_no", ""),
            "tarih":     c.get("tarih", ""),
            "vade":      c.get("vade", ""),
            "meblagh":   c.get("meblagh", 0),
            "odenen":    c.get("odenen", 0),
            "kalan":     c.get("kalan", 0),
            "durum":     c.get("durum", "Bekliyor"),
            "ch_kodu":   c.get("ch_kodu", ""),
            "ch_ismi":   c.get("ch_ismi", ""),
            "banka":     c.get("banka", ""),
            "sube":      c.get("sube", ""),
            "hesap_no":  c.get("hesap_no", ""),
            "para_birimi": para_birimi,
        })
    if rows:
        sb.table("cekler").insert(rows).execute()
