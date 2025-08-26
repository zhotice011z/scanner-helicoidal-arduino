#include <Wire.h>
#include <VL53L0X.h>
#include <AccelStepper.h>

// ===== Motor =====
const int stepsPerRevolution = 4096; // 28BYJ-48 em meio-passo

// Pinos (ordem HALF4WIRE = IN1, IN3, IN2, IN4)
AccelStepper motorBASE(AccelStepper::HALF4WIRE, 4, 6, 5, 7);
AccelStepper motorELEV(AccelStepper::HALF4WIRE, 10, 12, 11, 13);

// ===== Sensor =====
VL53L0X sensor;

// ===== Perfis de movimento =====
float rpmBASE = 10, rpmELEV = 10;
float accBASE = 400, accELEV = 400;

float rpmToSteps(float rpm) { return (rpm * stepsPerRevolution) / 60.0; }

void aplicarPerfis() {
  motorBASE.setMaxSpeed(rpmToSteps(rpmBASE));
  motorBASE.setAcceleration(accBASE);
  motorELEV.setMaxSpeed(rpmToSteps(rpmELEV));
  motorELEV.setAcceleration(accELEV);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  sensor.init();
  sensor.setTimeout(500);
  sensor.startContinuous();

  motorBASE.setCurrentPosition(0);
  motorELEV.setCurrentPosition(0);
  aplicarPerfis();

  Serial.println("Arduino pronto. Comandos válidos:");
  Serial.println("  BASE:<passos>");
  Serial.println("  ELEV:<passos>");
  Serial.println("  SENS");
}

void processarComando(String cmd) {
  cmd.trim();
  if (cmd.startsWith("BASE:")){
    motorBASE.move(cmd.substring(5).toInt());
  }
  else if (cmd.startsWith("ELEV:")){
    motorELEV.move(cmd.substring(5).toInt());
  }
  else if (cmd == "SENS") {
    uint16_t d = sensor.readRangeContinuousMillimeters();
    if (sensor.timeoutOccurred()) Serial.println("DIST:TIMEOUT");
    else {
      Serial.print("DIST:");
      Serial.println(d);
    }
  }
}

void loop() {
  if (Serial.available()) processarComando(Serial.readStringUntil('\n'));

  motorBASE.run();
  motorELEV.run();

  // Reporta DONE quando motores chegam ao alvo
  static bool baseMov = false, elevMov = false;
  if (motorBASE.distanceToGo() != 0){
    baseMov = true;
  }
  if (motorELEV.distanceToGo() != 0){
    elevMov = true;
  }
  if (baseMov && motorBASE.distanceToGo() == 0){
    baseMov = false; Serial.println("BASE DONE");
  }
  if (elevMov && motorELEV.distanceToGo() == 0){
    elevMov = false; Serial.println("ELEV DONE");
  }
}
