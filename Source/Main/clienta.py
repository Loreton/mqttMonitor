import paho.mqtt.client as mqtt
import time,logging
broker="lnmqtt.duckdns.org"

port=1883
QOS=0

CLEAN_SESSION=True
logging.basicConfig(level=logging.INFO) #error logging
#use DEBUG,INFO,WARNING
def on_subscribe(client, userdata, mid, granted_qos):   #create function for callback
   #print("subscribed with qos",granted_qos, "\n")
   time.sleep(1)
   logging.info("sub acknowledge message id="+str(mid))
   pass

def on_disconnect(client, userdata,rc=0):
    logging.info("DisConnected result code "+str(rc))


def on_connect(client, userdata, flags, rc):
    logging.info("Connected flags"+str(flags)+"result code "+str(rc))


def on_message(client, userdata, message):
    msg=str(message.payload.decode("utf-8"))
    print("message received  "  +msg)
    
def on_publish(client, userdata, mid):
    logging.info("message published "  +str(mid))

topic1 ="house/client_a"
client= mqtt.Client("ClientA",False)       #create client object

client.on_subscribe = on_subscribe   #assign function to callback
client.on_disconnect = on_disconnect #assign function to callback
client.on_connect = on_connect #assign function to callback
client.on_message=on_message
client.connect(broker,port)           #establish connection
time.sleep(1)
client.loop_start()
client.subscribe("house/client_b")
count=1
while True: #runs forever break with CTRL+C
   print("publishing on topic ",topic1)
   msg="message " +str(count) + " from client A"
   client.publish(topic1,msg)
   count +=1
   time.sleep(5)
client1.disconnect()

client1.loop_stop()

