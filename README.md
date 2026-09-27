# Teklif Değerlendirme

Satınalma tekliflerini kapsam, maliyet, ticari koşul ve risk açısından karşılaştırır.

## v4.0.2 aday kaynakları

Bu dal ana skill **4.0.2** kaynaklarını içerir. Canlı kabul henüz tamamlanmadı;
bu dal kararlı Release değildir. Son kararlı Release **v3.1.1** olarak kalır.

### Son değişiklikler

- Yeni analiz başlangıcı birleşik `guncelleyici` skill'ine devredilir.
- Sonuç Excelinde köprü bulunmaz; kaynak dosya ve sayfa düz metinle gösterilir.
- Görünen etiketler Türkçedir; firmalar bütün tablolarda aynı açık adla gösterilir.
- Doğrulanmış teklif bedelleri, eşit kapsamlı maliyet hesabından ayrı gösterilir.
- PDF paragraf, başlık ve basım düzeni düzeltildi.
- Yüksek güvence görsel kontrolü bütün sekme ve PDF sayfalarını kapsar.

## Kurulum yapısı

Ana skill `skills/teklif-degerlendirme/` altındadır. Birleşik güncelleyici ayrı
[ozanbesinci/guncelleyici](https://github.com/ozanbesinci/guncelleyici) deposunda
yönetilir; ana skill paketi onu içermez. Depodaki eski
`teklif-degerlendirme-guncelle` ağacı tarihsel v3 kaynaklarıdır; v4 kurulumunda
ayrıca kurulmaz.

Paket manifesti şema 3'tür ve yalnız ana skill'in izinli kaynaklarını kapsar.
Kaynak depo ZIP'i doğrulanmış kurulum paketi yerine kullanılamaz.
Güncelleyici normal kullanımda kararlı Release'i denetler; aday dalı otomatik kurmaz.

## Doğrulama

Bu düzeltme için 49 otomatik test geçti; iki isteğe bağlı Excel testi atlandı.
Gerçek masaüstü Excel yeniden hesaplama, bağımsız sayısal mutabakat ve parametre
geri alma ayrıca doğrulandı. Bu kontroller uçtan uca canlı analiz kabulünün yerine geçmez.

- [Kurulum ve çalışma kapsamı](skills/teklif-degerlendirme/KURULUM.md)
- [Sürüm geçmişi](skills/teklif-degerlendirme/CHANGELOG.md)
- [Kararlı sürümler](https://github.com/ozanbesinci/teklif-degerlendirme/releases)

## Veri sınırı

Bu depo yalnız skill kaynaklarını içerir. Gerçek teklifler, şirket belgeleri,
analiz çıktıları, sohbet/hafıza dosyaları ve kimlik bilgileri yayımlanmaz.

## Lisans

Henüz açık kaynak lisansı tanımlanmamıştır. Kaynakların görünür olması,
yeniden dağıtım veya türev eser izni verildiği anlamına gelmez.
