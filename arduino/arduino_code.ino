#include <Stepper.h>
#include <Wire.h>
#include <VL53L0X.h>

const int stepsPerRevolution = 4096; // 28BYJ-48 em meio passo

// Motores usando a ordem correta dos pinos
Stepper motorELEV(stepsPerRevolution, 4, 6, 5, 7);
Stepper motorBASE(stepsPerRevolution, 10, 12, 11, 13);
VL53L0X sensor;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  if (!sensor.init()) {
    Serial.println("Erro ao iniciar sensor");
    while(1);
  }
  sensor.setTimeout(1000);
  sensor.startContinuous();

  // Define velocidade (RPM)
  motorBASE.setSpeed(5);
  motorELEV.setSpeed(5);

  Serial.println("Arduino setup DONE");
}

void processarComando(String cmd) {
  cmd.trim();

  if (cmd.startsWith("BASE:")) {
    long passos = cmd.substring(5).toInt();
    Serial.print("Executando BASE: ");
    Serial.println(passos);
    motorBASE.step(passos);
    Serial.println("BASE DONE");
  }

  else if (cmd.startsWith("ELEV:")) {
    long passos = cmd.substring(5).toInt();
    Serial.print("Executando ELEV: ");
    Serial.println(passos);
    motorELEV.step(passos);
    Serial.println("ELEV DONE");
  }
  else if (cmd.startsWith("SENS")) {
    uint16_t d = sensor.readRangeContinuousMillimeters();
    Serial.print("DIST:");
    Serial.println(d);
  }
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    processarComando(cmd);
  }
}
