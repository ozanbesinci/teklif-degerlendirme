# Teklif Değerlendirme v2.0.3

Bu etiket, 7 Eylül 2026 tarihli **tarihsel v2.0.3** skill kaynağıdır.

Yeni kurulumlarda güncel kararlı sürüm önerilir. Bu sürüm yalnız önceki davranışa
dönmesi gereken kullanıcılar için yayımlanmıştır.

## Kurulum

Codex'e şu isteği verin:

> `ozanbesinci/teklif-degerlendirme` deposunun `v2.0.3` etiketindeki
> `skills/teklif-degerlendirme` yolunu kur.

Komut satırındaki sistem `skill-installer` aracı için karşılığı:

```text
python <skill-installer>/scripts/install-skill-from-github.py \
  --repo ozanbesinci/teklif-degerlendirme \
  --ref v2.0.3 \
  --path skills/teklif-degerlendirme
```

Kurucu mevcut hedef klasörün üzerine yazmaz. Halen v3 kuruluysa kullanıcı eski
sürüme dönmeyi açıkça istemeli; mevcut `teklif-degerlendirme` ve v3'e ait
`teklif-degerlendirme-guncelle` kurulumlarının kaldırılması ayrı ve bilinçli bir
işlem olarak yapılmalıdır.

## v3'ten farkı

- Yalnız `teklif-degerlendirme` skill'i vardır.
- `teklif-degerlendirme-guncelle` bu sürümde yoktur.
- Sol/Terra/Astra çok ajan politikası, yeni deterministik motor ve v3 teslim kapısı yoktur.
- v3 güncelleyicisi sürüm düşürmez ve v2.0.3'ü otomatik kurmaz.

Release ZIP'i tarihsel paketin byte düzeyinde aynısıdır; yalnız dosya adı standart
Release biçimine çevrilmiştir. SHA-256:

```text
bb177fbec7c46fb0361a6106cd9631727c1a537b4fe13d18348289416e7afde1
```

37 tarihsel hesap örneği yeniden çalıştırılmış ve geçmiştir. Bu doğrulama canlı teklif
analizinin veya yeni v3 kontrollerinin yerine geçmez.

## Lisans

Bu depoda açık kaynak lisansı tanımlanmamıştır. Kaynakların görünür olması yeniden
dağıtım veya türev eser izni verildiği anlamına gelmez.
