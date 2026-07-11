#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

const int pinMosfet = 9; 

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(50);
  pinMode(pinMosfet, OUTPUT);

  // Inisialisasi OLED (tetap dipasang di kode meski fisiknya belum ada)
  if(display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    display.clearDisplay();
    display.setTextSize(2);
    display.setTextColor(WHITE);
    display.setCursor(20, 20);
    display.println("LOQ COOL");
    display.display();
    delay(2000);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    int komaIndex = data.indexOf(',');
    
    if (komaIndex > 0) {
      int tCPU = data.substring(0, komaIndex).toInt();
      int tGPU = data.substring(komaIndex + 1).toInt();
      int suhuMax = max(tCPU, tGPU);

      // KONTROL KIPAS: 40C (0%) sampai 80C (100%)
      int pwm = map(constrain(suhuMax, 40, 80), 40, 80, 0, 255);
      analogWrite(pinMosfet, pwm);

      // UPDATE OLED (nanti otomatis nyala pas dipasang)
      display.clearDisplay();
      display.setTextSize(1);
      display.setTextColor(WHITE);
      display.setCursor(0,0);
      display.print("CPU Temp: "); display.print(tCPU); display.println(" C");
      display.print("GPU Temp: "); display.print(tGPU); display.println(" C");
      display.print("Fan Power: "); display.print(map(pwm, 0, 255, 0, 100)); display.println("%");
      display.display();
    }
  }
}