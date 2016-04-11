#include <SoftwareSerial.h>

SoftwareSerial mySerial(4, 5); // RX, TX
                       // 4 -> green
                       // 5 -> orange

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(19200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  
  Serial.write("Client Connected");
  // set the data rate for the SoftwareSerial port
  mySerial.begin(19200);  
  delay(500);  
  mySerial.write("=");
  delay(5);
}

char lastChar = '$';

int cnt = 0;

void loop() {
    if (mySerial.available()){
      char c = mySerial.read();
      Serial.write(c);
      lastChar = c;
    } else if (lastChar=='$') {
      delay(100);
      Serial.write("\n");    
      mySerial.write("\"?");
      delay(5);
      lastChar='-';   
    } else {
      cnt++;
      delay(5);
      if (cnt%100==0) {
        Serial.write("\n");    
        mySerial.write("\"?");
      }
    }
}
