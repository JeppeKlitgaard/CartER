#include <CommandAndControl.h>

#include <Init.h>
#include <PacketReactor.h>
#include <Protocol.h>

#include <memory>


void loop_command_and_control() {
    if (S.available() != 0) {
        S.print("AVAILABLE: ");
        S.println(S.available());

        packet_reactor.tick();
    }
}
// void loop_command_and_control() {
//     // Read a line if available
//     byte packet[MAX_PACKET_SIZE];
//     Packet packetId;
//     size_t bytesRead;

//     if (S.available() != 0) {
//         bytesRead = S.readBytesUntil(PACKET_END, packet, MAX_PACKET_SIZE);
//         packetId = resolvePacket(packet[0]);

//         switch(packetId) {
//             case Packet::PING: S.write(SYMBOL_COMMAND_PONG);
//             case Packet::UNKNOWN: S.write(SYMBOL_OBSERVATION_UNKNOWN);
//             default: S.write(SYMBOL_OBSERVATION_UNKNOWN);
//         }

//         S.write(PACKET_END);
//     }
// }
