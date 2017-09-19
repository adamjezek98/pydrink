#include "HX711.h"
#include <Wire.h>


HX711 scale(A1, A0);


#define DIRECTIONPIN  2
#define STEPPIN  3
#define STEPDELAY 500
#define HOMESWITCH 6
int Steps = 0;
bool Direction;


#define RELAYS 0x20
byte states[8] = {0, 0, 0, 0, 0, 0, 0, 0};

void setup() {
  Serial.begin(38400);
  Wire.begin();
  pour(0, false);

  scale.set_scale(2232.71);
  scale.tare();
/*
  pinMode(13,OUTPUT);
  for(int i = 0; i < 5; i++){
    digitalWrite(13,1);
    delay(i*100);
    digitalWrite(13,0);
    delay(i*100);
  }*/
  digitalWrite(13,0);
  pinMode(DIRECTIONPIN, OUTPUT);
  pinMode(STEPPIN, OUTPUT);
  pinMode(HOMESWITCH, INPUT_PULLUP);
  
  
}


String inputData;
void loop() {

  if (Serial.available()) {
    inputData = readString();
    //Serial.println(inputData);
    if (inputData[0] == 'm') { //move
      //Serial.println("MOVE");
      if (inputData[1] == 'h'){
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
          states[i] = 0;
          pour(0, false);
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


    } else if(inputData[0] == 's') {//scale
      if(inputData[1] == 't'){
        scale.tare();
        Serial.println("DONE");        
      } else {
        Serial.println(scale.get_units(1), 1);
      }
    }


  }

}

void pour(byte tap, bool state) {
  if (state)
    states[tap] = 1;
  else
    states[tap] = 0;

  byte res = 255;
  for (int i = 0; i < 8; i++) {
    res -= round(pow(2, i)) * states[i];
  }
  //Serial.println(res);
  Wire.beginTransmission(RELAYS);
  Wire.write(res);
  Wire.endTransmission();
}




void stepper(long xw) {
  //Serial.println("steps: "+String(xw));

  for (long x = 0; x < xw * 100; x++) {
    //delayMicroseconds(200);
    if (!Direction && !digitalRead(HOMESWITCH)) {
      Serial.println("home");
      break;
    }

    digitalWrite(DIRECTIONPIN, Direction);
    digitalWrite(STEPPIN, 1);
    delayMicroseconds(STEPDELAY);
    digitalWrite(STEPPIN, 0);
    delayMicroseconds(STEPDELAY);
  }
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

