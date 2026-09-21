# Standart ön sonuç verisi ve Excel

`scripts/excel_uret.py --data <JSON> --output <yeni.xlsx>` mevcut openpyxl
kütüphanesiyle beş sekmeli ön sonuç dosyası üretir. Bu bir tekrar kullanılabilir
üretim bileşenidir; kaynak okuma, model veya doğrulanmış nihai karar motoru değildir.
Özel projelerde bu şablonun yetmediği alanlar gerekçeli genişletilir; her projede
sıfırdan yeni üretici yazılmaz. Mevcut teslim dosyası üzerine yazılmaz.

JSON sözleşmesi `schema:teklif-workbook/v1`, `analysis_mode:preliminary`,
`recommendation:null`, `project`, `analysis_date:YYYY-MM-DD`, `summary:[metinler]`.

- `offers`: benzersiz `id`, `name`, `currency`, `declared_total` (sayı/null),
  `lines:[{id,description,quantity,unit_price,source}]`. Eksik miktar/fiyat null;
  sıfır ayrı bir gerçek değerdir. Firma toplamları birbirine eklenmez; farklı para
  birimleri dönüştürülmeden sıralanmaz. Bilinen toplam nihai KTM diye sunulmaz.
- `scope_items`: benzersiz `id`, `classification:5-A|5-B`, `description`,
  `amount`, `currency`, `source`, `rfi`. 5-A'da gerçek `offer_id` zorunlu.
  5-B'de `allocations:[{offer_id,amount,currency,payment_date,source}]` bütün
  firmaları birer kez kapsamalı; tutar/döviz/tarih aynı ve biliniyor olmalı.
  Bu giriş tutarlılığı kontrolüdür, kaynağın gerçekten doğru olduğunun kanıtı değil.
- `rfi`: `{id,owner,question,source}`. Muhatap bilinmiyorsa açıkça belirtilir.

Kalem tutarı Excel formülüdür; bilinmeyen fiyat boş sonuç üretir. Eksik kalem sayısı
görünür kalır. Girdi metni Excel formülü olarak çalıştırılmaz. Karar özeti uzun
metni satırlara ayırır; RFI/kaynak alanları satır yüksekliğiyle genişler. Çok uzun
tek hücreyi teslim öncesi parçalara böl; okunmayan metni küçük fontla sıkıştırma.

Üretici `DRAFT_RECALC_REQUIRED` döndürür. Formül önbelleğini elle doldurmaz. Gerçek
Excel/LibreOffice yeniden hesabı, temsili parametre değişimi (null/sıfır dahil),
bağımsız hesap ve her yeni sayfanın görsel incelemesi tamamlanmadan teslim kapısı
açılmaz. Revizyonda değişen görünüm ve bağımlılıkları kontrol edilir.
