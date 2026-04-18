# 🔐 Şifre Kurulum Rehberi — KAYRANACC

## Streamlit Cloud'da Kullanıcı Şifresi Ayarlama

1. **Streamlit Cloud** → `https://share.streamlit.io` adresine gidin
2. **KAYRANACC** uygulamanızı bulun
3. **Settings** → **Secrets** sekmesine tıklayın
4. Aşağıdaki formatı ekleyin:

```toml
[kullanicilar]
ibrahim = "sifreniz123"
ekip_uyesi = "baska_sifre"
```

5. **Save** butonuna tıklayın — uygulama otomatik yeniden başlar.

---

## Yeni Kullanıcı Eklemek

`[kullanicilar]` bloğuna yeni satır ekleyin:

```toml
[kullanicilar]
ibrahim = "sifre1"
muhasebe = "sifre2"
yonetici = "sifre3"
```

---

## Yerel Test İçin

Proje klasöründe `.streamlit/secrets.toml` dosyası oluşturun:

```toml
[kullanicilar]
test = "test123"
```

> ⚠️ `.streamlit/secrets.toml` dosyasını **asla** GitHub'a push etmeyin!  
> `.gitignore` dosyasına eklenmiştir.
