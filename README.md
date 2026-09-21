# Teklif Değerlendirme Skill Paketi

Satınalma tekliflerini kapsam, maliyet, ticari koşul ve risk açısından
karşılaştırmak için iki birlikte sürümlenen Codex skill'i içerir:

- `teklif-degerlendirme`: analiz, deterministik hesap ve zorunlu kontrol akışı
- `teklif-degerlendirme-guncelle`: kararlı GitHub Release sürümünü kontrol etme,
  doğrulama ve iki skill'i birlikte güncelleme

Güncel kararlı paket: **v3.1.1**

Ana skill: **3.1.1** · Güncelleyici: **1.0.0**

## Mimari özeti

- Ana ajan ve bağımsız nihai denetçi: `gpt-5.6-sol` / high
- Uzman alt ajanlar: `gpt-5.6-terra` / medium veya high
- Yalnız çözülmeyen kritik yorumlarda karşı inceleme: `gpt-6-astra` / high
- Luna hiçbir görevde, yedekte veya yeniden denemede kullanılmaz
- Sabit hesaplar ve dosya kontrolleri Python araçlarıyla yapılır
- Kritik kontrol eksikse kesin firma önerisi verilmez
- CLI devamlarında mantıksal görev kimliği sabittir; her deneme ayrı kaydedilir
- Model/ağ erişimi kaynak paylaşılmadan ve koşu klasörü oluşturulmadan önce sınanır
- Denetçi karşılaştırmasından önce deterministik Excel/JSON kalite kapısı çalışır
- Çağrı, revizyon, token ve süre tavanları kontrolsüz tekrarları durdurur

Aktif modelin gerçekten değişmesi istemcinin model/efor seçimini desteklemesine
bağlıdır. Skill metni tek başına oturum modelini değiştirmez.

## Kurulum

Codex'e şu isteği verin:

> `ozanbesinci/teklif-degerlendirme` deposundaki
> `skills/teklif-degerlendirme` ve
> `skills/teklif-degerlendirme-guncelle` yollarını birlikte kur.

Codex'in sistem `skill-installer` aracı iki yolu tek işlemde kurar. İlk kurulumdan
sonra skill'ler sonraki turda kullanılabilir.

Elle kurulum yapanlar iki klasörü aynı fiziksel `skills` köküne birlikte koymalıdır.
Tek klasör kurulumu desteklenen paket yapısı değildir. Ayrıntılar:
[`skills/teklif-degerlendirme/KURULUM.md`](skills/teklif-degerlendirme/KURULUM.md).

## Güncelleme

Kurulumdan sonra kullanıcı açıkça “teklif değerlendirme skill'ini güncelle” dediğinde
`teklif-degerlendirme-guncelle`, en son kararlı GitHub Release paketini ve SHA-256
kaydını doğrular; iki skill'i birlikte günceller. Yalnız “sürümü kontrol et” isteği
dosyalarda değişiklik yapmaz.

Güncelleme aracı:

- yerel değişiklik veya bilinmeyen dosyada durur,
- analiz devam ederken güncelleme yapmaz,
- sürüm düşürmez ve ön sürüm yüklemez,
- uzaktan indirilen Python kodunu çalıştırmaz,
- ZIP yol kaçışı, bağlantı, aşırı boyut ve manifest tutarsızlığını reddeder.

## Eski sürüme dönme

Tarihsel **v2.0.3** sürümü GitHub'dan kurulabilir:

> `ozanbesinci/teklif-degerlendirme` deposunun `v2.0.3` etiketindeki
> `skills/teklif-degerlendirme` yolunu kur.

v2.0.3 yalnız ana skill'i içerir; `teklif-degerlendirme-guncelle` o sürümde yoktur.
v3 güncelleyicisi bilinçli olarak sürüm düşürmez. Mevcut hedef klasör varken sistem
kurucusu üzerine yazmaz; v3'ten dönüş, mevcut v3 çiftinin açıkça kaldırıldığı ve
yalnız v2.0.3 ana skill'inin kurulduğu ayrı bir işlem olmalıdır.

[v2.0.3 kaynak etiketi](https://github.com/ozanbesinci/teklif-degerlendirme/tree/v2.0.3) ·
[v2.0.3 Release](https://github.com/ozanbesinci/teklif-degerlendirme/releases/tag/v2.0.3)

## Release doğrulama

Her güncel v3 Release şu iki varlığı birlikte yayımlar:

- `teklif-degerlendirme-vX.Y.Z.zip`
- `teklif-degerlendirme-vX.Y.Z.zip.sha256`

v3.1.1 paketinin SHA-256 değeri:

```text
f02796d62c92d5200ae66e51b4640ee212ae1ee7991ec3b67727ddce8cfa9441
```

Sürüm ayrıntıları:
[`skills/teklif-degerlendirme/CHANGELOG.md`](skills/teklif-degerlendirme/CHANGELOG.md).

## Doğrulanan kapsam

v3.1.1 için 116 otomatik test geçti: 57 runtime/çıktı/Excel/motor testi, 37 hesap
örneği ve 22 güncelleyici testi. Bunlar sabit görev kimliği, otomatik artefakt kaydı,
kesinti kurtarma, bütçe kapıları, yerel ön kalite denetimi ve tam-ağaç güncelleme
senaryolarını da kapsar. Birim testleri, düzeltme öncesinde yapılan gerçek teklif
koşusunun veya yeni sürümle tam canlı Sol/Terra/Astra tekrarının yerine geçmez.

## Veri sınırı

Bu depo yalnız skill kaynaklarını içerir. Gerçek teklifler, şirket belgeleri,
analiz çıktıları, sohbet/hafıza dosyaları ve kimlik bilgileri yayımlanmaz.

## Lisans

Bu depoda henüz açık kaynak lisansı tanımlanmamıştır. Kaynakların görünür olması,
yeniden dağıtım veya türev eser izni verildiği anlamına gelmez.
