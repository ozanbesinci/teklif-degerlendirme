# Teklif Değerlendirme

Satınalma tekliflerini kapsam, maliyet, ticari koşul ve risk açısından karşılaştırır.

## Kararlı sürüm: v4.0.3

Ana skill **4.0.3**, kullanıcının açık kararıyla kararlı dağıtıma alınmıştır.
[ZIP ve SHA-256 doğrulama dosyası](https://github.com/ozanbesinci/teklif-degerlendirme/releases/tag/v4.0.3)
GitHub Release üzerinden dağıtılır. Uçtan uca canlı analiz kabulü ayrıca izlenir.

### Son değişiklikler

- Yeni analiz başlangıcında güncelleyicinin sürüm tablosu masaüstü Work ve Codex sohbetinde gösterilir; PowerShell seçim penceresi çağrılmaz.
- Kullanıcı **Güncelle** demeden kurulum başlamaz; seçilen işlemler tamamlanınca analiz devam eder.
- Önceki 4.0.2 sürümündeki Excel ve PDF sunum düzeltmeleri korunur.

## Kurulum yapısı

Ana skill `skills/teklif-degerlendirme/` altındadır. Birleşik güncelleyici ayrı
[ozanbesinci/guncelleyici](https://github.com/ozanbesinci/guncelleyici) deposunda
yönetilir; ana skill paketi onu içermez. Depodaki eski
`teklif-degerlendirme-guncelle` ağacı tarihsel v3 kaynaklarıdır; v4 kurulumunda
ayrıca kurulmaz.

Paket manifesti şema 3'tür ve yalnız ana skill'in izinli kaynaklarını kapsar.
Kaynak depo ZIP'i doğrulanmış kurulum paketi yerine kullanılamaz.
Birleşik güncelleyici normal kullanımda en son kararlı Release paketini denetler.

## Doğrulama

97 Python testi geçti; iki isteğe bağlı test atlandı. Güncelleyicinin 42 Python
testi ve sohbet akış testi de geçti. Yerel Work içinden canlı kullanım ve uçtan
uca teklif analizi kabulü ayrıca izlenir.

- [Kurulum ve çalışma kapsamı](skills/teklif-degerlendirme/KURULUM.md)
- [Sürüm geçmişi](skills/teklif-degerlendirme/CHANGELOG.md)
- [Kararlı sürümler](https://github.com/ozanbesinci/teklif-degerlendirme/releases)

## Veri sınırı

Bu depo yalnız skill kaynaklarını içerir. Gerçek teklifler, şirket belgeleri,
analiz çıktıları, sohbet/hafıza dosyaları ve kimlik bilgileri yayımlanmaz.

## Lisans

Henüz açık kaynak lisansı tanımlanmamıştır. Kaynakların görünür olması,
yeniden dağıtım veya türev eser izni verildiği anlamına gelmez.
