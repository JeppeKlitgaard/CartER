#include <CommandAndControl.h>

#include <Init.h>
#include <PacketReactor.h>
#include <Protocol.h>
#include <Utils.h>
#include <memory>


void loop_command_and_control() {
    if (S.available() != 0) {
        packet_reactor.tick();
    }
}
