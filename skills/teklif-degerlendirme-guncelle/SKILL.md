---
name: teklif-degerlendirme-guncelle
description: Teklif değerlendirme paketinin GitHub'daki kararlı sürümünü kontrol eder; açık kurulum veya güncelleme isteğinde ana skill ile güncelleme skill'ini birlikte yükler. Yalnız sürüm kontrolü istendiğinde dosyaları değiştirmez.
metadata:
  version: "3.0.1"
---

# Teklif Değerlendirme Güncelle

Resmî depo `ozanbesinci/teklif-degerlendirme`; ana skill ile bu skill aynı sürümde
kurulur. Bu akış deterministiktir; alt ajan veya model çağrısı gerekmez. Luna yoktur.

## Yetki ve akış

1. İsteği ayır: sürümü öğren/kontrol et → `check`; kur/güncelle → açık yazma yetkisi.
   Sadece skill'in adının anılması veya analiz talebi güncelleme yetkisi vermez.
2. Bu skill'in fiziksel klasörünü çöz. Üst klasör ortak `skills` köküdür; keşif
   junction'ının kendisini değiştirme. İlk kurulumda kullanıcı hedefini esas al.
3. `scripts/guncelle.py check --root "<ortak-skill-koku>"` çalıştır. Ağ/kimlik hatasını
   'güncel' diye yorumlama. Release yoksa yayın yoktur; tahmin sürüm üretme.
4. Açık güncelleme isteğinde `scripts/guncelle.py update --root "<ortak-skill-koku>"`
   çalıştır. Bu komut yalnız daha yeni kararlı sürümü indirip doğrular ve iki skill'i
   birlikte değiştirir. Şu an çalışan analiz varken güncelleme yapılmaz.
5. Kurulu sürümleri ve `verify` çıktısını doğrula. Yeni skill sonraki turda kullanılabilir.
   Hata, kısmi işlem veya kurtarma gereği varsa 'güncellendi' deme.

Komutların başına ortamın Python 3.11+ çalıştırıcısını, script yoluna bu klasörün
tam yolunu koy. Kullanıcıya gereksiz komut dökmek yerine sonucu ve engeli anlat.
Ağ/yazma izinleri gerekiyorsa platformun izin mekanizmasını kullan; atlatma yapma.

## İlk kurulum ve kaynak kopyasını kaydetme

Resmî GitHub Release'ten `teklif-degerlendirme-vX.Y.Z.zip` ve aynı adlı `.sha256`
dosyasını al. Release/tag/paket sürümü aynı olmalı. Kullanıcının seçtiği ortak köke:

```text
python guncelle.py install --root "<skills>" --archive "<paket.zip>" --sha256 "<64-karakter-sha256>"
```

Bu komut var olan yönetimsiz klasörün üzerine yazmaz. Bir önceki kaynak kurulumu
paketle **tam eşleşiyorsa** (örneğin skill-installer ile iki yol birden kurulduysa):

```text
python guncelle.py register --root "<skills>" --archive "<paket.zip>" --sha256 "<64-karakter-sha256>"
python guncelle.py verify --root "<skills>"
```

`register` skill dosyalarını değiştirmez; eşleşen dosya/sürüm envanterini kaydeder.
v2 ile v3 eşleşmez; register bunu aşmak için kullanılmaz. Eski/yerel değişikliği
koruyarak v3'e geçiş için ayrı, açık kapsamlı düzenleme gerekir.

## Güvenlik sınırları

- Yalnız resmî HTTPS Release adresleri; hash ve paket içi dosya manifesti doğrulanır.
  SHA-256 bağımsız yayıncı imzası değildir; GitHub hesap/depo güveni ayrıca önemlidir.
- Kaynak teklif, rapor, kimlik bilgisi veya hafıza hiçbir sunucuya gönderilmez.
- Yalnız iki skill dizini yönetilir. Yerel değişiklik ve bilinmeyen dosyada işlem durur;
  kullanıcı dosyaları, junction/symlink ve başka skill'ler üzerine yazılmaz.
- Analiz/güncelleme kilidini görürse durur. Eski kilit otomatik silinmez.
- ZIP yol kaçışı, bağlantı, yinelenmiş dosya, büyük paket ve sürüm tutarsızlığı reddedilir.
- Her iki yeni klasör hazır ve doğrulanmış olmadan mevcut kurulum değiştirilmez.
  Yakalanan işlem hatasında eski sürüm geri konur. Güç kesintisi/süreç öldürülmesinde
  işlem günlüğü ve kilit korunabilir; elle inceleme olmadan yeni işlem başlatma.
- Sürüm düşürme/ön sürüm/yabancı depo/uzaktaki kurulum kodu çalıştırma yoktur.
  Periyodik kontrol veya otomasyon kendiliğinden kurulmaz.

Tam paket ve platform notları: `../teklif-degerlendirme/KURULUM.md`.
