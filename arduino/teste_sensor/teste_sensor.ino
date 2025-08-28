#include <Wire.h>
#include <VL53L0X.h>

VL53L0X sensor;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  if (!sensor.init()) {
    Serial.println("Erro ao iniciar sensor!");
    while(1);
  }
  sensor.setTimeout(1000);
  sensor.startContinuous();
  Serial.println("INIT");
}

void loop() {
  uint16_t d = sensor.readRangeContinuousMillimeters();
  Serial.println(d);
  delay(500);
}
