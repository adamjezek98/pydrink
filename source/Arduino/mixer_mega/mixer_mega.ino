#include "HX711.h"



HX711 scale(A1, A0);


#define DIRECTIONPIN  2
#define STEPPIN  3
#define STEPPER_DISABLED 22
#define STEPDELAY 500
#define HOMESWITCH 6
int Steps = 0;
bool Direction;




void setup() {
  Serial.begin(115200);

  scale.set_scale(2232.71);
  scale.tare();


  for (int i = 0; i < 8; i++) {
    pinMode(30 + i, OUTPUT);
    digitalWrite(30 + i, 1);
  }
  digitalWrite(13, 0);
  pinMode(DIRECTIONPIN, OUTPUT);
  pinMode(STEPPIN, OUTPUT);
  pinMode(HOMESWITCH, INPUT_PULLUP);
  pinMode(STEPPER_DISABLED, OUTPUT);
  digitalWrite(STEPPER_DISABLED,1);



}


String inputData;
void loop() {

  if (Serial.available()) {
    inputData = readString();
    //Serial.println(inputData);
    if (inputData[0] == 'm') { //move
      //Serial.println("MOVE");
      if (inputData[1] == 'h') {
        Direction = false;
        stepper(500);
        return;
      }
      else if (inputData[1] == '1')
        Direction = true;
      else
        Direction = false;
      inputData.remove(0, 2);
      stepper(inputData.toInt());
      Serial.println("DONE");
    } else if (inputData[0] == 'p') { //pour
      //Serial.println("POUR");
      if (inputData[1] == 'a') {
        for (int i = 0; i < 8; i++) {
          pour(i, false);
        }
      } else {
        byte tap = (byte)String(inputData[1]).toInt();
        bool state;
        if (inputData[2] == '1')
          state = true;
        else
          state = false;

        pour(tap, state);
      }
      Serial.println("DONE");


    } else if (inputData[0] == 's') { //scale
      if (inputData[1] == 't') {
        scale.tare();
        Serial.println("DONE");
      } else {
        Serial.println(scale.get_units(1), 1);
      }
    }


  }

}

void pour(byte tap, bool state) {
  digitalWrite(30 + tap, !state);
}




void stepper(long xw) {
  //Serial.println("steps: "+String(xw));
  digitalWrite(STEPPER_DISABLED,0);
  for (long x = 0; x < xw * 100; x++) {
    //delayMicroseconds(200);
    if (!Direction && !digitalRead(HOMESWITCH)) {
      Direction = !Direction;
      //while (!digitalRead(HOMESWITCH)) 
      for(int i = 0; i < 100; i++){
        digitalWrite(DIRECTIONPIN, Direction);
        digitalWrite(STEPPIN, 1);
        delayMicroseconds(STEPDELAY);
        digitalWrite(STEPPIN, 0);
        delayMicroseconds(STEPDELAY);
      }
      Serial.println("home");
      break;
    }

    digitalWrite(DIRECTIONPIN, Direction);
    digitalWrite(STEPPIN, 1);
    delayMicroseconds(STEPDELAY);
    digitalWrite(STEPPIN, 0);
    delayMicroseconds(STEPDELAY);
  }
  digitalWrite(STEPPER_DISABLED,1);
}


String readString() {
  String rs;
  while (Serial.available()) {
    char c = Serial.read();
    rs += c;
    delay(2);
  }
  return rs;

}

