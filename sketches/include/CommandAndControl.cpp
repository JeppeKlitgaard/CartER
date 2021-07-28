#include <CommandAndControl.h>

#include <Init.h>


void loop_command_and_control() {
    // Read a line if available
    byte packet[MAX_PACKET_SIZE];
    size_t bytesRead;

    if (S.available() != 0) {
        bytesRead = S.readBytesUntil(PACKET_END, packet, MAX_PACKET_SIZE);
        S.write(packet, bytesRead);
        S.write("This is a packet");
        S.write(PACKET_END);
    }
}
