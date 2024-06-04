/*********************************************************************
 Author: Bryan C. Jones
 Based on https://github.com/adafruit/Adafruit_nRF52_Arduino/blob/master/libraries/Bluefruit52Lib/examples/Peripheral/bleuart/bleuart.ino
 ----------------------------------------------------------------------
 
 This is an example for our nRF52 based Bluefruit LE modules

 Pick one up today in the adafruit shop!

 Adafruit invests time and resources providing this open source code,
 please support Adafruit and open-source hardware by purchasing
 products from Adafruit!

 MIT license, check LICENSE for more information
 All text above, and the splash screen below must be included in
 any redistribution
*********************************************************************/
#include <bluefruit.h>
#include <Adafruit_LittleFS.h>
#include <InternalFileSystem.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_seesaw.h>

#define SS_SWITCH_SELECT 1
#define SS_SWITCH_UP     2
#define SS_SWITCH_LEFT   3
#define SS_SWITCH_DOWN   4
#define SS_SWITCH_RIGHT  5

#define SEESAW_ADDR      0x49


#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 32 // OLED display height, in pixels

// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
// The pins for I2C are defined by the Wire-library. 
// On an arduino UNO:       A4(SDA), A5(SCL)
// On an arduino MEGA 2560: 20(SDA), 21(SCL)
// On an arduino LEONARDO:   2(SDA),  3(SCL), ...
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3C ///< See datasheet for Address; 0x3D for 128x64, 0x3C for 128x32
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#define NUM_TICKS 24

int curr_rotary = 0;
int last_rotary = 0;

/// Transit Packet
/// byte 0 - rotary encoder position
/// value = pos % NUM_TICKS
/// byte 1 - buttons and check bit
const uint8_t BTN_0      = 0b10000000;
const uint8_t BTN_1      = 0b01000000;
const uint8_t ENC_UP     = 0b00100000;
const uint8_t ENC_LEFT   = 0b00010000;
const uint8_t ENC_DOWN   = 0b00001000;
const uint8_t ENC_RIGHT  = 0b00000100;
const uint8_t ENC_SELECT = 0b00000010;
const uint8_t PARITY_BIT = 0b00000001;

struct d_button {
  uint8_t pin;
  uint8_t mask;
  int state;
  int lastState;
  uint32_t lastTime;
};

#define STD_BTN_COUNT 2
#define SS_BTN_COUNT 5

d_button buttons[STD_BTN_COUNT] = {
  { .pin = PIN_A3, .mask = BTN_0, .state=HIGH, .lastState=HIGH, .lastTime=0},
  { .pin = PIN_A4, .mask = BTN_1, .state=HIGH, .lastState=HIGH, .lastTime=0}
};

d_button ss_buttons[SS_BTN_COUNT] = {
  { .pin = SS_SWITCH_UP    , .mask = ENC_UP    , .state=HIGH, .lastState=HIGH, .lastTime=0 },
  { .pin = SS_SWITCH_LEFT  , .mask = ENC_LEFT  , .state=HIGH, .lastState=HIGH, .lastTime=0 },
  { .pin = SS_SWITCH_DOWN  , .mask = ENC_DOWN  , .state=HIGH, .lastState=HIGH, .lastTime=0 },
  { .pin = SS_SWITCH_RIGHT , .mask = ENC_RIGHT , .state=HIGH, .lastState=HIGH, .lastTime=0 },
  { .pin = SS_SWITCH_SELECT, .mask = ENC_SELECT, .state=HIGH, .lastState=HIGH, .lastTime=0 }
};

GFXcanvas1 canvas(SCREEN_WIDTH, SCREEN_HEIGHT);

// BLE Service
BLEDfu  bledfu;  // OTA DFU service
BLEDis  bledis;  // device information
BLEUart bleuart; // uart over ble
BLEBas  blebas;  // battery

#define PIN_ENCODER_A 13
#define PIN_ENCODER_B 12
#define COM_A    11
#define COM_B    1
#define BUTTON_UP 5
#define BUTTON_LEFT 0
#define BUTTON_DOWN 9
#define BUTTON_RIGHT 6
#define BUTTON_IN 10

#define NUM_TICKS 24  // how many ticks of the encoder is a full rotation

#define BTN_GND 19
#define BTN_0 5
#define BTN_1 6
#define LED 16

#define PACKET_SIZE 2

uint8_t last_packet[PACKET_SIZE];

Adafruit_seesaw ss;

// for debounce

unsigned long debounceDelay = 10; // in ms

void setup()
{
  Serial.begin(19200);

// #if CFG_DEBUG
  // Blocking wait for connection when debug mode is enabled via IDE
  while ( !Serial ) yield();
// #endif
  
  Serial.println("Game Table Controller");
  Serial.println("---------------------------\n");

  setupPins();
  setupDisplay();
  setupEncoder();
  setupBLE();

  // Set up and start advertising
  startAdv();

  Serial.println("Please use Adafruit's Bluefruit LE app to connect in UART mode");
  Serial.println("Once connected, enter character(s) that you wish to send");
}

void setupPins(void)
{
  // Set pins 2 & 23 to ground
  pinMode(2, OUTPUT);
  pinMode(23, OUTPUT);

  // setup button inputs
  pinMode(PIN_A3, INPUT_PULLUP);
  pinMode(PIN_A4, INPUT_PULLUP);

  digitalWrite(2, LOW);
  digitalWrite(23, LOW);
  Serial.println("Pin Setup Complete.");
}

void setupEncoder(void)
{
  Serial.println("Looking for seesaw!");
  
  if (! ss.begin(SEESAW_ADDR)) {
    Serial.println("Couldn't find seesaw on default address");
    while(1) delay(10);
  }
  Serial.println("seesaw started");
  uint32_t version = ((ss.getVersion() >> 16) & 0xFFFF);
  if (version  != 5740){
    Serial.print("Wrong firmware loaded? ");
    Serial.println(version);
    while(1) delay(10);
  }
  Serial.println("Found Product 5740");

  ss.pinMode(SS_SWITCH_UP, INPUT_PULLUP);
  ss.pinMode(SS_SWITCH_DOWN, INPUT_PULLUP);
  ss.pinMode(SS_SWITCH_LEFT, INPUT_PULLUP);
  ss.pinMode(SS_SWITCH_RIGHT, INPUT_PULLUP);
  ss.pinMode(SS_SWITCH_SELECT, INPUT_PULLUP);

  // get starting position
  last_rotary = ss.getEncoderPosition();
  curr_rotary = last_rotary;

  Serial.println("Turning on interrupts");
  ss.enableEncoderInterrupt();
  ss.setGPIOInterrupts((uint32_t)1 << SS_SWITCH_UP, 1);

  delay(1000);
}

void setupDisplay() {
  // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  } else {
    Serial.println(F("SSD1306 allocation success"));
  }

  delay(100);

  // Show initial display buffer contents on the screen --
  // the library initializes this with an Adafruit splash screen.
  // display.setRotation(2);
  display.display();
  delay(2000); // Pause for 2 seconds

  canvas.setTextWrap(false);
  drawStatus();
}

void setupBLE() {  
  // Setup the BLE LED to be enabled on CONNECT
  // Note: This is actually the default behavior, but provided
  // here in case you want to control this LED manually via PIN 19
  Bluefruit.autoConnLed(true);

  // Config the peripheral connection with maximum bandwidth 
  // more SRAM required by SoftDevice
  // Note: All config***() function must be called before begin()
  Bluefruit.configPrphBandwidth(BANDWIDTH_MAX);

  Bluefruit.begin();
  Bluefruit.setTxPower(6);
  Bluefruit.setName("Game Table Controller");
  Bluefruit.Periph.setConnectCallback(connect_callback);
  Bluefruit.Periph.setDisconnectCallback(disconnect_callback);

  // To be consistent OTA DFU should be added first if it exists
  bledfu.begin();

  // Configure and Start Device Information Service
  bledis.setManufacturer("Adafruit Industries");
  bledis.setModel("Bluefruit Feather52");
  bledis.begin();

  // Configure and Start BLE Uart Service
  bleuart.begin();

  // Start BLE Battery Service
  blebas.begin();
  blebas.write(100);
}

void startAdv(void)
{
  // Advertising packet
  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();

  // Include bleuart 128-bit uuid
  Bluefruit.Advertising.addService(bleuart);

  // Secondary Scan Response packet (optional)
  // Since there is no room for 'Name' in Advertising packet
  Bluefruit.ScanResponse.addName();
  
  /* Start Advertising
   * - Enable auto advertising if disconnected
   * - Interval:  fast mode = 20 ms, slow mode = 152.5 ms
   * - Timeout for fast mode is 30 seconds
   * - Start(timeout) with timeout = 0 will advertise forever (until connected)
   * 
   * For recommended advertising interval
   * https://developer.apple.com/library/content/qa/qa1931/_index.html   
   */
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(32, 244);    // in unit of 0.625 ms
  Bluefruit.Advertising.setFastTimeout(30);      // number of seconds in fast mode
  Bluefruit.Advertising.start(0);                // 0 = Don't stop advertising after n seconds  
}

void loop()
{
  uint8_t packet[PACKET_SIZE];

  // read encoder
  int curr_rotary = ss.getEncoderPosition();
  // if(curr_rotary != last_rotary) {
  //   Serial.println(curr_rotary);
  // }

  packet[0] = (uint8_t)(curr_rotary % NUM_TICKS);
  packet[1] = checkButtons();
  
  if (!(last_packet[0] ^ packet[0] == 0 && last_packet[1] ^ packet[1] == 0) )
  {
    bleuart.write( packet, PACKET_SIZE );
  }
  
  // Forward from BLEUART to HW Serial
  while ( bleuart.available() )
  {
    uint8_t ch;
    ch = (uint8_t) bleuart.read();
    Serial.write(ch);
  }

  last_packet[0] = packet[0];
  last_packet[1] = packet[1];
  last_rotary = curr_rotary;
}

void drawStatus(void) {
  //display.clearDisplay();
  canvas.fillScreen(0);

  canvas.setTextSize(1);              // Normal 1:1 pixel scale
  canvas.setTextColor(SSD1306_WHITE); // Draw white text
  canvas.setCursor(0,0);              // Start at top-left corner
  canvas.println(F("1) Hello, world!"));
  canvas.println(F("2) Hello, world!"));
  canvas.println(F("3) Hello, world!"));
  canvas.println(F("4) Hello, world!"));
  canvas.println(F("5) Hello, world!"));
  display.drawBitmap(0, 0, canvas.getBuffer(),
    canvas.width(), canvas.height(), SSD1306_WHITE, SSD1306_BLACK);
  display.display();
  delay(2000);
}

uint8_t checkButtons(void)
{
  // check for button states
  // and assemble packet
  uint8_t packet = 0;

  for (int i = 0; i < STD_BTN_COUNT; i++) {
    readButton(&buttons[i], false);
    if (buttons[i].state == LOW) {
      packet |= buttons[i].mask;
    }
  }
  
  for (int i = 0; i < SS_BTN_COUNT; i++) {
    readButton(&ss_buttons[i], true);
    if (ss_buttons[i].state == LOW) {
      packet |= ss_buttons[i].mask;
    }
  }

  // Serial.println(packet);

  return packet;
}

// callback invoked when central connects
void connect_callback(uint16_t conn_handle)
{
  // Get the reference to current connection
  BLEConnection* connection = Bluefruit.Connection(conn_handle);

  char central_name[32] = { 0 };
  connection->getPeerName(central_name, sizeof(central_name));

  Serial.print("Connected to ");
  Serial.println(central_name);
}

/**
 * Callback invoked when a connection is dropped
 * @param conn_handle connection where this event happens
 * @param reason is a BLE_HCI_STATUS_CODE which can be found in ble_hci.h
 */
void disconnect_callback(uint16_t conn_handle, uint8_t reason)
{
  (void) conn_handle;
  (void) reason;

  Serial.println();
  Serial.print("Disconnected, reason = 0x"); Serial.println(reason, HEX);
}

// debounce input
// returns the current state after debounce
void readButton(d_button *btn, bool is_ss)
{
  int reading;
  if (is_ss) { // read from seesaw lib 
    reading = ss.digitalRead(btn->pin) ? HIGH : LOW;
  } else {
    reading = digitalRead(btn->pin);
  }

  // If the switch changed, due to noise or pressing:
  if (reading != btn->lastState) {
    // reset the debouncing timer
    btn->lastTime = millis();
  }
  
  btn->lastState = reading;

  if ((millis() - btn->lastTime) > debounceDelay) {
    // if the button state has changed:
    if (reading != btn->state) {
      btn->state = reading;
    }
  }
}
