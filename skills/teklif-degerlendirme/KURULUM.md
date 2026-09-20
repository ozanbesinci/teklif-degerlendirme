# Kurulum ve Dağıtım — v3.0.1

## Paket ve kaynak

Resmî dağıtım adresi: [ozanbesinci/teklif-degerlendirme](https://github.com/ozanbesinci/teklif-degerlendirme).
Kaynak adresinin yazılı olması çevrimiçi yayının tamamlandığını göstermez. İlk kurulum
öncesi yayımlanmış kararlı Release ve sürüm dosyaları doğrulanır.

İki skill **birlikte** kurulur ve güncellenir:

```text
skills/
  teklif-degerlendirme/
    SKILL.md
    VERSION
    config/
    references/
    scripts/
  teklif-degerlendirme-guncelle/
    SKILL.md
    VERSION
    scripts/
```

Her iki VERSION dosyası aynı olmalıdır. Kullanıcıya görünen güncelleme skill'i
“Teklif Değerlendirme Güncelle”, teknik adı `teklif-degerlendirme-guncelle`dir.
Güncelleme için GitHub hesabı gerekmez; public Release okuması yeterlidir. Yayınlamak
için depo yazma yetkisi gerekir. Kimlik bilgisi skill'e veya dağıtım ZIP'ine konmaz.

## Çalışma gereksinimleri

- Python 3.11 veya üzeri: hesap, kaynak/kontrol ve güncelleme araçları.
- Tam ajan profili için model/efor seçimini destekleyen Codex ve erişilebilir
  `gpt-5.6-sol`, `gpt-5.6-terra`; kritik inceleme gerekirse `gpt-6-astra`.
- Ana ajan Sol/high; alt ajanlar rol politikasıyla, **Luna hiçbir aşamada yok**.
- Excel üretimi/okuma için mevcut ortamın kütüphanesi; formül testi için gerçek
  hesap motoru; PDF için mevcut dönüştürücü ve görsel inceleme aracı.
- Paket içi PDF içerik kontrolünde `pypdf` gerekir; yoksa kontrol açıkça bloke olur.
  Kurulum eksikliği gerçek PDF başarı testi yerine geçmez.
- Model erişimi, çıktı araçları ve ağ yetkisi çalıştırma öncesinde kontrol edilir.
  Eksik ortam “tam doğrulanmış v3 çalışması” olarak sunulmaz.

## İlk kurulum

Yalnız resmî kararlı Release paketini indir; otomatik üretilen GitHub “Source code”
ZIP'i ile dağıtım paketini karıştırma. Sürüm, paket dosyaları ve SHA-256 manifestini
güncelleme aracına doğrulat. Hash, indirme bütünlüğünü denetler; tek başına bağımsız
yayıncı imzası değildir. Güven kökü doğrulanmış resmî HTTPS deposudur.

Kurulum ve güncelleme komutlarının tek güncel kaynağı:
`../teklif-degerlendirme-guncelle/SKILL.md`. Araçların `--help` çıktısı da paketle
birlikte gelir. Skill-installer ile kaynak depodan kurarken **iki skill yolunu da**
seç; tek klasör kurulumu güncelleme sözleşmesini karşılamaz. Ham kaynak kurulumunu
yönetilen kurulum saymadan önce paket manifestiyle kayıt/bütünlük doğrulaması gerekir.

Kullanıcının seçtiği ortak skill köküne kur. Birden çok istemci aynı fiziksel kaynağı
kullanıyorsa kopya oluşturma; keşif klasörleri bu kaynağa bağlantı/junction olmalıdır.
Mevcut bir klasör veya farklı hedefli bağlantı üzerine yazma. Bu makinedeki ortak
kaynak düzeni korunur; genel kurulum için sabit kişisel disk yolu dayatılmaz.

Yerel Codex keşif dizini mevcut kurulum tercihine göre `~/.codex/skills` veya
`~/.agents/skills` olabilir. Yeni skill sonraki turda kullanılabilir; görünmüyorsa
istemcinin beceri listesini yeniden yükle. Global model/ajan ayarlarını değiştirme.
Bu paketin rol politikası yalnız teklif değerlendirme çalışmasına aittir.

## Kullanım ve model seçimi

1. Ana görevi Sol / yüksek efor ile başlat.
2. `$teklif-degerlendirme` ile tekliflerin bulunduğu klasörü/dosyaları belirt.
3. Kaynak envanteri, gerekirse sorular, hesap ve bağımsız kontrol sonrası çıktıyı al.
4. Alt ajan model/efor seçimi yerleşik araçla açık parametreler üzerinden veya
   `scripts/ajan_yonetimi.py` ile yapılır. Dry-run model çağrısı değildir.
5. İnceleme devam ederken skill güncellenmez. Kapanmamış bir analiz kilidi varsa
   işlemi/çalışma kaydını kontrol et; körlemesine kilit silme.

`references/ajan-calistirma.md` çalıştırıcı ve teslim kontrolü şemasını açıklar.
Sadece SKILL.md'ye “Sol kullan” yazmak aktif oturumun modelini değiştirmez.
Canlı model koşusu yapılmadıysa model davranışı doğrulanmış denmez.

## Güncelleme

“Teklif değerlendirmeyi güncelle” isteği iki skill'in birlikte güncellenmesini
yetkilendirir. “Sürümü kontrol et” yalnız okuma yapar. Güncelleyici daha yeni kararlı
sürümü doğrular; analiz/güncelleme kilidi, dosya değişikliği veya sürüm uyuşmazlığında
durur. Yerel değişiklikleri silmez, başka model seçmez, uzaktaki script'i çalıştırmaz.

Paket doğrulanmadan mevcut kurulum değiştirilmez. Başarısız işlem eski sürümün
korunmasını/geri alınmasını hedefler; güç kesintisi ve süreç çökmesinden sonra
kurulum durumu ayrıca doğrulanır. İki klasörün değiştirilmesi tek bir atomik dosya
işlemi değildir; kurtarma ve kilit kontrollerini atlama. Yeni sürüm sonraki analizde
kullanılır. Downgrade ve ön sürüm otomatik uygulanmaz.

v2 gibi manifesti olmayan eski kurulum üzerine otomatik yazılmaz. Önce kaynak
değişikliklerini koruyarak eşleşen v3 paketiyle kontrollü kurulum/kayıt gerekir;
güncelleyici “temiz kurulum” varsayımıyla dosya silmez.

## Web ve diğer istemciler

Satınalma yöntemi ve belgeler farklı istemcilerde okunabilir; Sol/Terra/Astra
seçimi, bağımsız ajan, kod ve yerel güncelleme yeteneği var kabul edilmez.
Yalnız yüklenmiş dosyalara erişen ortamda GitHub'dan yerel kurulumu değiştirme
vaadi verilmez; paket kullanıcı/yönetici tarafından yenilenir. Model kontrolü
olmayan ortamda v3'ün tam çalışma profili kullanılıyor denmez.

## Sürüm hazırlama ve doğrulama

- İki VERSION, skill metadata ve CHANGELOG aynı sürümü göstermeli.
- Mevcut 37 hesap örneği, yeni hesap/kontrol/güncelleme birim testleri çalışmalı.
- Kurulum, daha yeni sürüm, bozuk paket, yerel değişiklik, aktif analiz, geri alma
  ve zorunlu kontrol eksikliği test edilmeli.
- Gerçek model ve gerçek teklif seti koşusu birim testinden ayrı raporlanmalı;
  sahte başarı kayıtları veya yalnız başlık eşleşmesi yeterli değildir.
- `scripts/paket_olustur.py` yalnız iki skill'in izinli dosyalarını alır. Çıktı
  dizini skill ağacının dışında olmalıdır. Kurumsal belgeler, analizler, anahtarlar,
  sohbet/hafıza dosyaları ve testteki gerçek şirket verileri dağıtıma girmez.
- GitHub'a yalnız bu bağımsız paket/kaynak yapısı yayımlanır; vault'un tamamı
  gönderilmez. Release etiketi `v3.0.1` ile paket sürümü aynı olmalı.
- Kimlik doğrulaması veya yayın tamamlanmadıysa yerel güncelleme ile çevrimiçi yayın
  ayrı durum olarak raporlanır. Yeni sürüm yayımlamak kullanıcı analizini çalıştırmaz.

Önceki sürüm ayrıntıları `CHANGELOG.md` içindedir. v3.0.1 testi üretim ortamında
“sıfır hata”, maliyet azalması veya bütün platformlarda eşdeğer davranış garantisi değildir.
