/* 
 *  Dissertation - Biomedical Engineering
 *  2020/2021 
 *  Ana Catarina Monteiro Magalhães 
 *  
 *  Water temperature and zebrafish vital signs monitoring Firmware
 *  
 *  File: sensors.ino
 *  Date: 06-09-2021
 *  
 *  Description: This script runs on an Arduino Uno. As input receives four analog signals (A0, A1, A2, A3)
 
*/

#include "TimerOne.h"

float Vo;
float R1 = 10000;
float logR2, R2, Tk, Tc;
float a = 1.01e-03, b = 2.38e-04, d = 2.02e-07;

float m;
float p;
float i = 0;


void setup() {
  Serial.begin(115200); 
  pinMode(A3, INPUT);                     // Thermistor
  pinMode(A0, OUTPUT);                    // LED IV
  pinMode(A2, INPUT);                     // Phototransistor
  pinMode(A1, INPUT);                     // Amplified signal (phototransistor)
  
  // pinMode(4, OUTPUT);                  // Digital Pin - only used for testing if the timer
                                          // was working properly
  
  Timer1.initialize(10000);               // initialize timer1, and set a 10ms period
  // Timer1.setPeriod(period);
  Timer1.attachInterrupt(reading,10000);  // attaches reading() as a timer overflow interrupt
}

void loop() {
  // Set IV LED as High
  digitalWrite(A0, 1);
  // Calculation of the water temperature
  Vo = (5 * (float)analogRead(A3)) / 1023.0; 
  R2 = R1 * (5 - Vo) / Vo;
  logR2 = log(R2);
  Tk = (1.0 / (a + b * logR2 + d * logR2 * logR2 * logR2));
  Tc = Tk - 273.15;         // Water Temperature in Celcius degree
}

void reading() {
//  digitalWrite(4, HIGH);

 // m is the signal from A2 and p is the signal from A1 (amplified)
//  m = 0; 
  p = 0;
  for (int n = 0; n < 10; n++) {
//    m += analogRead(A2);
    p +=analogRead(A1);
  }
  // Sent the data via serial port
  Serial.print(analogRead(A2));     // Heart beat readings   
  Serial.print(",");
  Serial.print(Tc);                 // Water temperature
  Serial.print(",");
  Serial.println(i);                // Time
  
  i = i + 0.01;
//  digitalWrite(4, LOW);
}
