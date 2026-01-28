#include <Servo.h>

// --- TANIMLAMALAR ---
Servo servoX;
Servo servoY;

// Servo Bağlantı Pinleri (Dijital PWM Pinleri)
// Eğer farklı pinlere taktıysan burayı değiştir.
const int PIN_X = 9;  
const int PIN_Y = 10; 

// Başlangıç Açısı
int posX = 90;
int posY = 90;

void setup() {
  // Python koduyla AYNI hızda olmalı (Çok Önemli!)
  Serial.begin(115200);
  
  // Hızlı tepki için timeout süresini düşürüyoruz
  Serial.setTimeout(10); 

  servoX.attach(PIN_X);
  servoY.attach(PIN_Y);

  // Başlangıçta sistemi merkeze al
  servoX.write(90);
  servoY.write(90);
}

void loop() {
  // Seri porttan veri var mı kontrol et
  if (Serial.available() > 0) {
    
    // Gelen karakteri oku
    char ch = Serial.read();

    // Eğer gelen karakter 'X' ise veri paketinin başındayız demektir
    if (ch == 'X') {
      
      // X'ten sonraki tam sayıyı oku
      int valX = Serial.parseInt(); 
      
      // X değerini okuduktan sonra sırada 'Y' karakteri olmalı.
      // Serial.read() ile sıradaki karakteri (Y'yi) okuyup geçiyoruz.
      // Ancak buffer boşalmış olabilir diye basit bir bekleme/kontrol eklenebilir
      // ama parseInt genelde Y'ye kadar bekler.
      
      char nextCh = Serial.read(); // 'Y' harfini ye
      
      if (nextCh == 'Y') {
        int valY = Serial.parseInt(); // Y'den sonraki sayıyı oku

        // --- GÜVENLİK SINIRLAMASI (Yazılımsal Sigorta) ---
        // Servo mekanik olarak sıkışmasın diye burada da sınır koyuyoruz
        // Python'da zaten var ama Arduino'da olması "son kale" güvenliğidir.
        valX = constrain(valX, 20, 150);
        valY = constrain(valY, 20, 150);

        // Servolara yaz
        servoX.write(valX);
        servoY.write(valY);
      }
    }
  }
}