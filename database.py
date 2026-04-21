# Geçici test - Supabase bağlantısı devre dışı

def initialize_db(): pass

def get_tum_haftalar(): return []
def get_aktif_hafta(): return None
def hafta_ekle(x): return 1
def hafta_aktif_yap(x): pass
def hafta_sil(x): pass

def get_hafta_odemeler(x): return []
def odeme_ekle_bulk(x, y): pass
def odeme_ekle_manuel(*a, **k): pass
def odeme_durum_guncelle(*a, **k): pass
def odeme_sil(x): pass
def get_hafta_ozet(x): return {"toplam":0, "odendi":0, "tl_toplam":0, "usd_toplam":0}

def get_bankalar(): return []
def banka_ekle(*a, **k): pass
def banka_guncelle(*a, **k): pass
def banka_sil(x): pass

def get_cekler(x="TL"): return []
def cek_ekle_bulk(*a, **k): pass
def cek_sil(x): pass
def cek_sil_hepsi(*a, **k): pass
