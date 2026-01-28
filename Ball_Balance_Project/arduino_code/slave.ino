#include <Servo.h>
Servo servoX;
Servo servoY;

const int PIN_X = 9;  
const int PIN_Y = 10; 


int posX = 90;
int posY = 90;

void setup() {

  Serial.begin(115200);
  
  
  Serial.setTimeout(10); 

  servoX.attach(PIN_X);
  servoY.attach(PIN_Y);

 
  servoX.write(90);
  servoY.write(90);
}

void loop() {
  
  if (Serial.available() > 0) {
    
    
    char ch = Serial.read();

   
    if (ch == 'X') {
      
      int valX = Serial.parseInt(); 
      
      char nextCh = Serial.read(); 
      
      if (nextCh == 'Y') {
        int valY = Serial.parseInt(); 
        valX = constrain(valX, 20, 150);
        valY = constrain(valY, 20, 150);

       
        servoX.write(valX);
        servoY.write(valY);
      }
    }
  }
}
