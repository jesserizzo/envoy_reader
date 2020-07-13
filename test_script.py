from envoy_reader import EnvoyReader
import logging
import time

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
print("\n\tReader with mode detect")
AutoReader = EnvoyReader("envoy.local")
AutoReader.run_in_console()


print("\n\tEnvoy S Case")
EnvoySReader = EnvoyReader("envoy.local")
EnvoySReader.set_mode("PC")
EnvoySReader.run_in_console()

print("\n\tEnvoy C Case")
EnvoyCReader = EnvoyReader("envoy.local")
EnvoyCReader.set_mode("P")
EnvoyCReader.run_in_console()

print("\n\tOld Envoy Case")
EnvoyOReader = EnvoyReader("envoy.local")
EnvoyOReader.set_mode("P0")
EnvoyOReader.run_in_console()

IQEnvoyReader = EnvoyReader("envoy.local")
IQEnvoyReader.set_mode("IQEnvoy")
IQEnvoyReader.update_interval = 6
print("\n\tIQ Envoy Case with update interval {}".format( IQEnvoyReader.update_interval ))
IQEnvoyReader.run_in_console()
print("\n\tsleep 3 seconds, the next query will not fetch the data")
time.sleep(3)
IQEnvoyReader.run_in_console()
print("\n\tsleep 3 seconds again, the next query will fetch the data")
time.sleep(3)
IQEnvoyReader.run_in_console()

#print("\n\tNegative Case 1")
#try:
#    NegativeReader = EnvoyReader("pi3.local")
#    NegativeReader.run_in_console()
#except:
#    pass

print("\n\tNegative Case 2")
try:
    Negative2= EnvoyReader("pi4.local")
    Negative2.set_mode("EnvoyS")
    Negative2.run_in_console()
except:
    pass
