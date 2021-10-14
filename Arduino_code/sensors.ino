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
  pinMode(A3, INPUT);   // Thermistor
  pinMode(A0, OUTPUT);  // LED IV
  pinMode(A2, INPUT);   // Signal heart beat
  pinMode(A1, INPUT);   // Amplified signal
  pinMode(4, OUTPUT);   // Digital Pin 
  
  Timer1.initialize(10000);               // initialize timer1, and set a 50ms period
  //Timer1.setPeriod(period);
  Timer1.attachInterrupt(reading,10000); // attaches reading() as a timer overflow interrupt
}

void loop() {
  digitalWrite(A0, 1);
  Vo = (5 * (float)analogRead(A3)) / 1023.0; // alterei de 1024 to 1023
  R2 = R1 * (5 - Vo) / Vo;
  logR2 = log(R2);
  Tk = (1.0 / (a + b * logR2 + d * logR2 * logR2 * logR2));
  Tc = Tk - 273.15;
}

void reading() {
//  digitalWrite(4, HIGH);
//  m = 0;
  p = 0;
  for (int n = 0; n < 10; n++) {
//    m += analogRead(A2);
    p +=analogRead(A1);
  }
  Serial.print(analogRead(A2));       // m is the signal from A2 and p is the signal from A1 (amplified)
  Serial.print(",");
  Serial.print(Tc);
  Serial.print(",");
  Serial.println(i);
  
  i = i + 0.01;
//  digitalWrite(4, LOW);
}
